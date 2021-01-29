import tkinter as tk
from abc import ABC

from x7.geom.geom import *
from x7.geom.bezier import *
from x7.geom.model import ElemCurve
from x7.geom.typing import *
from ..errors import DigitizeInternalError
from ..undo import Command
from ..digibase import *
from .shape import *


__all__ = ['DigitizeCurve']

from x7.lib.iters import iter_rotate


class EditHandleControlPoint(EditHandle):
    """A Control point displayed on the screen"""
    show_index = True

    def __init__(self, shape: 'DigitizeCurve', cp: ControlPoint):
        super().__init__(shape)
        self.shape = shape      # type fix
        self.cp = cp
        self.tk_ids = []
        self.l1 = self.shape_line(fill='grey')
        self.l2 = self.shape_line(fill='grey')
        self.h_c = self.shape_rect(fill='blue', tag='c')
        self.h_l = self.shape_oval(fill='red', tag='l', radius=4)
        self.h_r = self.shape_oval(fill='green', tag='r', radius=4)
        if self.show_index:
            self.h_t = self.shape_text(text=str(shape.elem.control_points.index(cp)), fill='white')
        else:
            self.h_t = None
        self.kind_var = tk.StringVar(self.dd.master, value=cp.kind)
        self.kind_var.trace('w', self.kind_change)
        self.closed_var = tk.IntVar(self.dd.master, value=self.shape.elem.closed)
        self.closed_var.trace('w', self.closed_change)

    def update_coords(self):
        transform_pt = self.dd.draw.matrix.transform_pt
        cx, cy = transform_pt(self.cp.c, False)
        lx, ly = transform_pt(self.cp.l, False)
        rx, ry = transform_pt(self.cp.r, False)
        self.l1.update(cx, cy, lx, ly)
        self.l2.update(cx, cy, rx, ry)
        self.h_c.update(cx, cy)
        self.h_l.update(lx, ly)
        self.h_r.update(rx, ry)
        self.h_l.hide() if self.cp.dl == Vector(0, 0) else self.h_l.unhide()
        self.h_r.hide() if self.cp.dr == Vector(0, 0) else self.h_r.unhide()
        self.h_t.update(cx, cy)

    def adjust_vectors(self, target: Point, other: Vector):
        """Adjust one vector to target and the other appropriately"""

        # Delta from center, also new values for target
        delta = target - self.cp.c

        if self.cp.kind == 'smooth':
            # Maintain the length of bx, by, but set direction as -delta
            rad = (other.length() / delta.length()) if delta.length() else 0
            return delta, -delta * rad
        if self.cp.kind == 'very-smooth':
            # Very smooth means both vectors are same length
            return delta, -delta
        if self.cp.kind == 'sharp':
            # Sharp means no relation between vectors
            return delta, other

    def command_default(self) -> Command:
        from .curve_cmd import CommandCpEdit
        return CommandCpEdit(self.shape, self.cp)

    def mouse_button1_motion(self, event):
        if event.tag == 'c':
            self.cp.c = event.mp
        elif event.tag == 'l':
            self.cp.dl, self.cp.dr = self.adjust_vectors(event.mp, self.cp.dr)
        else:
            self.cp.dr, self.cp.dl = self.adjust_vectors(event.mp, self.cp.dl)
        self.shape.update()
        self.undo_snap()

    def menu_delete(self):
        self.shape.cp_del(self.cp)

    def menu_reset(self):
        self.undo_begin()
        self.cp.dl = Vector(3, 3)
        self.cp.dr = Vector(-3, -3)
        self.update_coords()
        self.undo_commit()

    def menu_add(self, delta):
        me = self.shape.elem.control_points.index(self.cp)
        other = me + delta
        insert = min(me, other) + 1
        if other >= len(self.shape.elem.control_points):
            other = 0
        ov = self.shape.elem.control_points[other].c - self.cp.c
        np = self.cp.c + ov * 0.5
        self.shape.cp_add(*np.xy(), insert)

    def menu_add_left(self):
        self.menu_add(-1)

    def menu_add_right(self):
        self.menu_add(1)

    def kind_change(self, name=None, index=None, mode=None):
        unused(name, index, mode)
        kind = self.kind_var.get()
        self.undo_begin()
        self.cp.kind = kind
        if kind == 'very-smooth':
            if self.cp.dr == Vector(0, 0) and self.cp.dl == Vector(0, 0):
                self.cp.dr = Vector(5, 5)
            else:
                self.cp.dr = (self.cp.dr - self.cp.dl) / 2
            self.cp.dl = -self.cp.dr
        elif kind == 'smooth':
            if self.cp.dr == Vector(0, 0) and self.cp.dl == Vector(0, 0):
                self.cp.dr = Vector(5, 5)
                self.cp.dl = Vector(-5, -5)
            else:
                direction = (self.cp.dr - self.cp.dl).unit()
                self.cp.dr = self.cp.dr.length() * direction
                self.cp.dl = -self.cp.dl.length() * direction
        self.update_coords()
        self.undo_commit()
        self.dd.status_set('Control point of curve %s set to %s' % (self.shape.elem.name, kind))

    def delete_lr(self, left: bool):
        self.undo_begin()
        if left:
            self.cp.dl = Vector()
        else:
            self.cp.dr = Vector()
        self.cp.kind = 'sharp'
        self.update_coords()
        self.undo_commit()

    def menu_delete_left(self):
        self.delete_lr(True)

    def menu_delete_right(self):
        self.delete_lr(False)

    def menu_intersect(self):
        from ..modes.select import CommandShapeReplace

        curves = self.shape.elem.self_intersect()
        if curves:
            shapes = [DigitizeCurve(self.dd, curve) for curve in curves]
            self.undo_begin(CommandShapeReplace(self.dd, [self.shape], shapes))
            self.undo_commit()

    def closed_change(self, name=None, index=None, mode=None):
        unused(name, index, mode)
        from .curve_cmd import CommandCurveEditProperty
        closed = bool(self.closed_var.get())
        self.undo_begin(CommandCurveEditProperty(self.shape, closed=closed))
        self.undo_commit()
        self.dd.status_set('Curve %s set to %s' % (self.shape.elem.name, 'Closed' if closed else 'Open'))

    def mouse_button2(self, event):
        # print('dcp.m2: event=%s .cx=%s .cy=%s .tag=%s' % (event, event.cx, event.cy, event.tag))
        tag = event.tag     # l, r, c
        root = self.dd.master
        menu = tk.Menu(root, tearoff=0)
        if tag == 'c':
            menu.add_command(label="Delete", command=self.menu_delete)
        elif tag == 'r':
            menu.add_command(label='Delete Right', command=self.menu_delete_right)
        else:
            menu.add_command(label='Delete Left', command=self.menu_delete_left)
        menu.add_command(label="Reset", command=self.menu_reset)
        menu.add_separator()
        if tag == 'c':
            menu.add_command(label='Self intersect', command=self.menu_intersect)
            menu.add_command(label='Add to Left(red)', command=self.menu_add_left)
            menu.add_command(label='Add to Right(green)', command=self.menu_add_right)
        elif tag == 'r':
            menu.add_command(label='Add', command=self.menu_add_right)
        else:
            menu.add_command(label='Add', command=self.menu_add_left)
        if tag == 'c':
            menu.add_separator()
            menu.add_radiobutton(label='Very Smooth', value='very-smooth', variable=self.kind_var)
            menu.add_radiobutton(label='Smooth', value='smooth', variable=self.kind_var)
            menu.add_radiobutton(label='Sharp', value='sharp', variable=self.kind_var)
            menu.add_separator()
            menu.add_radiobutton(label='Open', value=False, variable=self.closed_var)
            menu.add_radiobutton(label='Closed', value=True, variable=self.closed_var)

        menu.post(event.x_root, event.y_root)


class EditHandleDisplayOnly(EditHandle, ABC):
    """Just display, so no mouse interaction, just needs update_coords"""

    def command_default(self) -> Command:
        raise DigitizeInternalError("DisplayOnly, command_default should never get called")

    def mouse_button1_motion(self, event):
        pass


class EditHandleInterestingPoints(EditHandleDisplayOnly):
    """Midpoint and self-intersection points"""

    def __init__(self, shape: 'DigitizeCurve', cpl: ControlPoint, cpr: ControlPoint):
        super().__init__(shape)
        self.cpl = cpl
        self.cpr = cpr
        self.mid = self.shape_oval(fill='cyan')
        self.intersection = self.shape_oval(fill='blue')

    def update_coords(self):
        cpl = self.cpl.transform(self.dd.draw.matrix)
        cpr = self.cpr.transform(self.dd.draw.matrix)
        if cpl == cpr:
            self.intersection.hide()
        else:
            left, middle, right = bez_split(cpl, cpr)
            intersection = bez_intersect(left, middle, middle, right, as_points=True)
            self.mid.update(*middle.c.xy())
            if len(intersection):
                self.intersection.update(*intersection[0].xy())
                self.intersection.unhide()
            else:
                self.intersection.hide()


class EditHandleIntersections(EditHandleDisplayOnly):
    """Intersection points"""

    def __init__(self, shape: 'DigitizeCurve'):
        super().__init__(shape)
        self.shape = shape  # type fix
        self.pts = []
        # print('eih.__init__: ', len(list(self.shapes())))

    def all_intersections(self):
        xformed = [cp.transform(self.dd.draw.matrix) for cp in self.shape.elem.control_points]
        all_curves = list(iter_rotate(xformed))
        import itertools
        points = set()
        for a, b in itertools.combinations(all_curves, 2):
            found: List[Point] = bez_intersect(*a, *b, as_points=True, endpoints=False)
            points.update(p.xy() for p in found)
        return points

    def update_coords(self):
        intersections = self.all_intersections()
        for _ in range(len(intersections) - len(self.pts)):
            tk_shape = self.shape_oval(fill='blue')
            tk_shape.draw()
            self.pts.append(tk_shape)
        for n in range(len(self.pts) - len(intersections)):
            self.pts[n].hide()
        # print('ehi: shapes=%d ints=%d pts=%d' % (len(list(self.shapes())), len(intersections), len(self.pts)))
        for intersection, tk_shape in zip(intersections, self.pts):
            tk_shape.update(*intersection)
            tk_shape.unhide()


class EditHandleOffset(EditHandleDisplayOnly):
    """An offset curve, just for fun"""

    def __init__(self, shape: 'DigitizeCurve', offset: float):
        super().__init__(shape)
        self.shape = shape      # type fix
        self.poly = self.shape_poly('green')
        self.offset = offset

    def update_coords(self):
        offset_curve = self.shape.elem.offset(self.offset)
        paths = offset_curve.paths(self.shape.dd.draw)
        if len(paths) != 1:
            raise DigitizeInternalError('EditHandleOffset: len(paths)=%d, expected 1' % len(paths))
        self.poly.update(paths[0].points.tolist(True))


class DigitizeCurve(DigitizeShape):
    ALWAYS_CLOSED = False
    ELEM_TYPE = ElemCurve

    def __init__(self, dd: Optional[DigiDraw], curve: ElemCurve):
        super().__init__(dd, curve)
        self.elem = curve       # type fix
        self.need_edit_handle_refresh = False
        self.offsets = (5, )

    def details(self) -> list:
        from ..details import DetailRepr

        ctx = dict(ControlPoint=ControlPoint, Point=Point, Vector=Vector)
        cps = self.elem.control_points
        cp_detail = [DetailRepr(cps, idx, name='' if idx else 'Points', value=cp.round(4), ctx=ctx, ro=False)
                     for idx, cp in enumerate(cps)]
        return super().details() + [DetailRepr(self, 'offsets', name='Offsets')] + cp_detail

    def edit_handle_create(self) -> List[EditHandle]:
        # Sigh.  A little bit of typing goofiness
        eh: List[EditHandle] = [EditHandleControlPoint(self, cp) for cp in self.elem.control_points]
        eh.extend([EditHandleInterestingPoints(self, a, b) for a, b in iter_rotate(self.elem.control_points)])
        eh.append(EditHandleIntersections(self))
        for offset in self.offsets:
            eh.append(EditHandleOffset(self, offset))
        return eh

    def update(self):
        """Update visual based on changes to control points"""
        super().update()

        if self.edit_handles and len(self.edit_handles) != len(self.elem.control_points):
            self.need_edit_handle_refresh = True
            # if not self.need_edit_handle_refresh:
            #     raise DigitizeInternalError('edit_handle_refresh inconsistency')
        if self.need_edit_handle_refresh:
            # Change in handles, so reset them all
            self.edit_handle_refresh()
        self.need_edit_handle_refresh = False

    def menu_intersect(self):
        from ..modes.select import CommandShapeReplace

        curves = self.elem.self_intersect()
        if curves:
            shapes = [DigitizeCurve(self.dd, curve) for curve in curves]
            self.dd.undo_begin_commit(CommandShapeReplace(self.dd, [self], shapes))

    def context_extra(self, menu: tk.Menu):
        """Add extra menu items to select context menu based on shape type"""
        menu.add_separator()
        menu.add_command(label='Self Intersect', command=self.menu_intersect)

    def cp_add(self, x, y, where=None):
        from .curve_cmd import CommandDcpAdd

        self.need_edit_handle_refresh = True
        center = Point(x, y)
        magnitude = 12 / self.dd.zoom  # This should be reasonably visible on screen
        if self.elem.control_points:
            dxy = (Point(x, y) - self.elem.control_points[-1].c).unit() * magnitude
        else:
            dxy = Vector(magnitude, magnitude)
        cp = ControlPoint(center, -dxy, dxy, 'very-smooth')
        if where is None:
            self.dd.undo_begin(CommandDcpAdd(self, cp, None))
        else:
            # Adjust dl & dr
            left = self.elem.control_points[where - 1]
            right = self.elem.control_points[where % len(self.elem.control_points)]
            self.dd.undo_begin(CommandDcpAdd(self, cp, where, left, right))
            cp_left, cp_mid, cp_right = bez_split(left, right, t=0.5)
            left.restore(cp_left)
            cp.restore(cp_mid)
            right.restore(cp_right)
        self.dd.undo_commit()

    def cp_del(self, cp: ControlPoint):
        from .curve_cmd import CommandDcpDel

        self.need_edit_handle_refresh = True
        if cp in self.elem.control_points:
            self.dd.undo_begin(CommandDcpDel(self, cp))
            self.dd.undo_commit()
        else:
            raise ValueError('cp_del: Attempt to delete %s not in %s' % (cp, self))
