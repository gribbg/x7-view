"""Basic shape object for editor"""
import math
from abc import *
import tkinter as tk
from abc import ABC
from typing import Type

from x7.lib.subclasses import all_subclasses

from ..errors import DigitizeInternalError
from ..undo import Command
from x7.geom.colors import PenBrush
from x7.geom.geom import BBox, Point
from x7.geom.model import Elem
from x7.geom.transform import Transform
from x7.geom.typing import *
from ..digibase import *

__all__ = [
    'DigitizeShape', 'DigitizeShapes', 'EditHandle', 'EditHandleRotate',
    'TkIdSupport', 'TkShape',
    'tk_color'
]

DigitizeShapes = List['DigitizeShape']


def tk_color(color):
    """Output a tk compatible color"""
    if color is None:
        return ''
    if isinstance(color, str):
        return color
    # Fix tuples
    return '#%02x%02x%02x' % color[:3]


class TkIdSupport(object):
    """A mixin to support tracking tk_ids"""
    def __init__(self, dd: DigiDraw):
        from ..digiview import DigitizeView

        self._tk_ids = {}
        if isinstance(dd, DigitizeView):
            self.dd = cast(DigitizeView, dd)        # type fix
        else:
            raise ValueError('DigitizeView required for dd, not %s' % type(dd))

    def tk_id(self, tk_id, tag=None):
        self._tk_ids[tk_id] = tag
        if tag:
            self.dd.ui_map.register(tk_id, self, tag)
        return tk_id

    def tk_erase(self, tk_id):
        """
            Erase tk_id from screen and all mappings.
            Returns -1, handles tk_id==-1, to facilitate this pattern:
                self.an_id = self.parent.tk_erase(self.an_id)
        """
        if tk_id != -1:
            tag = self._tk_ids.pop(tk_id)
            if tag:
                self.dd.ui_map.unregister(tk_id)
            self.dd.canvas.delete(tk_id)
        return -1

    def tk_erase_all(self):
        for tk_id in list(self._tk_ids.keys()):
            self.tk_erase(tk_id)


class DigitizeShape(ABC, TkIdSupport):
    """
        Base class for all shapes

        Activation levels:
            - None: just normal display
            - Selected-Group: bold(?)
            - Selected-Single: bold(?) + minimal edit handles
            - Selected-Detail: bold(?) + full edit handles (control points, ...)
    """
    ALWAYS_CLOSED = True
    ELEM_TYPE = None
    bbox_show = False
    bbox_penbrush = PenBrush('grey')    # dash=[2, 6]

    def __init__(self, dd: Optional[DigiDraw], elem: Elem):
        super().__init__(dd)
        self.elem = elem
        self._tk_ids = {}
        self.edit_handles = []
        # List of paths displayed by this object, including bbox at 0
        self.path_info: List[Tuple[int, bool, PenBrush]] = []

    @classmethod
    def shape_map(cls) -> Dict[Type[Elem], Type['DigitizeShape']]:
        """Return mapping from Elem class to DigitizeShape class"""
        shapes: Dict[Type[Elem], Type['DigitizeShape']] = dict()
        for klass in all_subclasses(cls):
            elem_type = getattr(klass, 'ELEM_TYPE', None)
            if elem_type:
                shapes[elem_type] = klass
        return shapes

    def __str__(self):
        return '%s(%s)' % (self.__class__.__name__, self.elem.name)

    def short_name(self):
        return self.__class__.__name__.replace('Digitize', '')

    def set_dd(self, dd: DigiDraw):
        from ..digiview import DigitizeView

        assert self.dd is None
        assert isinstance(dd, DigitizeView)
        self.dd = cast(DigitizeView, dd)

    @abstractmethod
    def details(self) -> list:
        """List of Details instances describing values to edit"""
        from ..details import Detail, DetailBool
        return [
            Detail(self.elem, 'name', name='Name'),
            Detail(self.elem, 'penbrush', name='PenBrush', ro=True),
            DetailBool(self.elem, 'closed', name='Closed', ro=self.ALWAYS_CLOSED),
            Detail(self.elem, 'xform', name='XForm', ro=True),
            Detail(self.elem, '__class__', name='Class', value=self.__class__.__name__, ro=True),
            Detail(self.elem, '', name='Selected', value=self in self.dd.selection, ro=True),
        ]

    def su_save(self):
        """Return dictionary of copies of attributes to save"""
        return dict(elem=self.elem.copy())

    # noinspection PyMethodOverriding
    def su_restore(self, elem):
        """
            Apply dictionary of attributes to restore.
            Best pattern is su_restore(self, p1, p2, radius), but this requires the
            #noinspection PyMethodOverriding directive since each object will have a different pattern
        """
        self.elem.restore(elem)

    def copy(self):
        """Return a copy.  Deep for model elements, shallow for UI elements"""
        # TODO-is that really the correct description, even for Group?
        return type(self)(self.dd, self.elem.copy())

    def transform(self, matrix: Transform):
        """Return a copy of this shape transformed by matrix.  .transform(identity) is like .copy()"""
        return type(self)(self.dd, self.elem.transform(matrix))

    def bbox(self) -> BBox:
        """Return the external space bounding box of this shape"""
        return self.elem.bbox()

    def bbox_int_update(self, bbox: BBox):
        """Update shape based on changes to the internal bounding box, resize/scale/translate as needed"""
        self.elem.bbox_int_update(bbox)
        self.update()

    def draw_space(self) -> Transform:
        """
            Usage:
                with self.draw_space(dc) as xform:
                    ... = xform.transform(...)
        """
        return self.elem.draw_space(self.dd.draw)

    def draw(self):
        """
            Do initial placement of shape on the canvas.
            Does not need to set coordinates
        """
        if not self.path_info:
            if self.bbox_show:
                canvas_rect = self.dd.canvas.create_rectangle([0, 0, 1, 1], dash=[2, 6], outline='grey')
                bbox_id = self.tk_id(canvas_rect)
            else:
                bbox_id = -1
            self.path_info.append((bbox_id, True, self.bbox_penbrush))
            # print('draw: ', self.path_info)

            for idx, path in enumerate(self.elem.paths(self.dd.draw)):
                if path.closed:
                    tk_id = self.dd.canvas.create_polygon([0, 0, 1, 1], fill='', outline='black')
                else:
                    tk_id = self.dd.canvas.create_line([0, 0, 1, 1], fill='black', capstyle=tk.ROUND)
                # TODO-transform width
                self.path_info.append((self.tk_id(tk_id, 'path_%d' % idx), path.closed, path.penbrush))

    def erase(self):
        """Remove shape, bbox, & control points from canvas"""
        if self.path_info:
            self.tk_erase_all()
            self.path_info = []
        self.edit_handle_hide()

    def update(self):
        """Update visual based on changes to data"""
        if self.path_info:
            bbox_id = self.path_info[0][0]
            if bbox_id != -1:
                # BBox is displayed, so it needs to be updated
                bb = self.bbox()
                p1, p2 = self.dd.draw.matrix.transform_pts([(bb.xl, bb.yl), (bb.xh, bb.yh)])
                self.dd.canvas.coords(bbox_id, p1 + p2)

            paths = self.elem.paths(self.dd.draw)
            if len(paths) != len(self.path_info)-1:
                # TODO-reset via .erase() and .draw()?
                raise DigitizeInternalError('len(paths)=%d len(self.elem_ids)=%d' % (len(paths), len(self.path_info)-1))
            for (path_id, closed, pen), path in zip(self.path_info[1:], paths):
                self.dd.canvas.coords(path_id, path.points.tolist(True))

        self.edit_handle_update()

    def context_extra(self, menu: tk.Menu):
        """Add extra menu items to select context menu based on shape type"""
        pass

    @abstractmethod
    def edit_handle_create(self) -> List['EditHandle']:
        """Construct list of edit handles"""
        return [EditHandleRotate(self)]

    def edit_handle_update(self):
        """Update coords of all edit handles"""
        for eh in self.edit_handles:
            eh.update_coords()

    def edit_handle_show(self):
        """Show all edit handles"""
        if not self.edit_handles:
            self.edit_handles = self.edit_handle_create()
        for eh in self.edit_handles:
            eh.draw()
        self.edit_handle_update()

    def edit_handle_hide(self):
        """Hide all edit handles"""
        for eh in self.edit_handles:
            eh.erase()
        self.edit_handles = []

    def edit_handle_refresh(self):
        """If displayed, destroy and recreate edit handles (used when shape makes significant changes)"""
        if self.edit_handles:
            self.edit_handle_hide()
            self.edit_handle_show()

    def select(self):
        """Show this shape in selected mode for editing"""
        # Options: Make shape bold, different color, show edit handles

        for path_id, closed, pb in self.path_info:
            if path_id != -1:
                if closed:
                    self.dd.canvas.itemconfigure(path_id, width=2, fill=tk_color(pb.fill_color), outline='red')
                else:
                    self.dd.canvas.itemconfigure(path_id, width=2, fill='red')

    def deselect(self):
        """Unselect this shape"""
        # first = True
        for path_id, closed, pb in self.path_info:
            # if first:
            #     print('deselect: %s %s %s %s/%r %s/%r' % (
            #         path_id, closed, pb.stroke_width,
            #         pb.stroke_color, tk_color(pb.stroke_color), pb.fill_color, tk_color(pb.fill_color)))
            #     first = False
            if path_id != -1:
                with self.draw_space() as xform:
                    width = pb.stroke_width(xform)
                if closed:
                    self.dd.canvas.itemconfigure(path_id, width=width, fill=tk_color(pb.fill_color),
                                                 outline=tk_color(pb.stroke_color))
                else:
                    self.dd.canvas.itemconfigure(path_id, width=width, fill=tk_color(pb.stroke_color))
        self.edit_handle_hide()

    def as_curves(self) -> List:    # ['DigitizeCurve']
        """Return this object as a list of DigitizeCurve objects"""
        from .digicurve import DigitizeCurve

        return [DigitizeCurve(self.dd, curve) for curve in self.elem.as_curves()]


class TkShape(object):
    SHAPES = ('rect', 'oval', 'line')

    def __init__(self, parent: 'EditHandle', kind, fill, tag, radius=5):
        self.parent = parent
        self.kind = kind
        self.fill = fill
        self.tag = tag
        self.radius = radius
        self.tk_id = -1
        self.hidden = False
        if kind not in self.SHAPES:
            raise ValueError('TkShape: unknown kind: %s' % kind)

    def draw(self):
        parent = self.parent
        if self.tk_id == -1:
            if self.kind == 'rect':
                shape_func = parent.dd.canvas.create_rectangle
            elif self.kind == 'oval':
                shape_func = parent.dd.canvas.create_oval
            elif self.kind == 'line':
                shape_func = parent.dd.canvas.create_line
            else:
                raise NotImplementedError
            self.tk_id = parent.tk_id(shape_func(0, 0, 0, 0, fill=self.fill), tag=self.tag)
        return self.tk_id

    def erase(self):
        self.tk_id = self.parent.tk_erase(self.tk_id)

    def hide(self):
        self.parent.dd.canvas.itemconfigure(self.tk_id, state='hidden')
        self.hidden = True

    def unhide(self):
        self.parent.dd.canvas.itemconfigure(self.tk_id, state='normal')
        self.hidden = False

    def update(self, xl, yl, xh=None, yh=None):
        """Update coords.  If xh is None, use radius around (xl, yl)"""
        if xh is None:
            r = self.radius
            xl, yl, xh, yh = xl-r, yl-r, xl+r, yl+r
        self.parent.dd.canvas.coords(self.tk_id, xl, yl, xh, yh)


class TkShapeText(TkShape):
    SHAPES = ('text', )

    def __init__(self, parent: 'EditHandle', text, fill, tag, height=9):
        super().__init__(parent, 'text', fill, tag, radius=5)
        self.text = text
        self.height = height

    def draw(self):
        parent = self.parent
        if self.tk_id == -1:
            canvas_id = parent.dd.canvas.create_text(0, 0, text=self.text, fill=self.fill)
            self.tk_id = parent.tk_id(canvas_id, tag=self.tag)
        return self.tk_id

    # noinspection PyMethodOverriding
    def update(self, x, y, t=None):
        """Update coords.  If t is None, don't change text"""
        self.parent.dd.canvas.coords(self.tk_id, x, y)


class TkShapePoly(TkShape):
    SHAPES = ('poly', )

    def __init__(self, parent: 'EditHandle', fill, tag):
        super().__init__(parent, 'poly', fill, tag, radius=5)

    def draw(self):
        parent = self.parent
        if self.tk_id == -1:
            canvas_id = parent.dd.canvas.create_polygon([0, 0, 1, 1], fill='', outline=self.fill)
            self.tk_id = parent.tk_id(canvas_id, tag=self.tag)
        return self.tk_id

    # noinspection PyMethodOverriding
    def update(self, pts):
        """Update coords"""
        self.parent.dd.canvas.coords(self.tk_id, pts)


class EditHandle(ABC, TkIdSupport):
    """A generic edit handle displayed on the screen"""

    def __init__(self, shape: DigitizeShape):
        super().__init__(shape.dd)
        assert isinstance(shape, DigitizeShape)
        self.shape = shape

    def __str__(self):
        return str('EditHandle(%s)' % self.shape.__class__.__name__)

    def __repr__(self):
        return str(self)

    def shape_rect(self, fill, tag=None, radius=5):
        return TkShape(self, 'rect', fill, tag=tag, radius=radius)

    def shape_oval(self, fill, tag=None, radius=5):
        return TkShape(self, 'oval', fill, tag=tag, radius=radius)

    def shape_line(self, fill, tag=None, radius=5):
        return TkShape(self, 'line', fill, tag=tag, radius=radius)

    def shape_text(self, text, fill, tag=None, height=9):
        return TkShapeText(self, text, fill, tag=tag, height=height)

    def shape_poly(self, fill, tag=None):
        return TkShapePoly(self, fill, tag=tag)

    def shapes(self) -> Iterable[TkShape]:
        """Iterator over all TkShapes in self"""
        for member, value in self.__dict__.items():
            if isinstance(value, TkShape):
                yield value
            if isinstance(value, (list, tuple)):
                for sub_value in value:
                    if isinstance(sub_value, TkShape):
                        yield sub_value

    def shapes_draw_all(self):
        """Erase all TkShapes in self"""
        for shape in self.shapes():
            shape.draw()

    def shapes_erase_all(self):
        """Erase all TkShapes in self"""
        for shape in self.shapes():
            shape.erase()

    def erase(self):
        self.shapes_erase_all()

    def draw(self):
        self.shapes_draw_all()
        self.update_coords()

    @abstractmethod
    def update_coords(self):
        raise NotImplementedError

    @abstractmethod
    def command_default(self) -> Command:
        ...

    def undo_begin(self, command=None):
        command = command or self.command_default()
        self.dd.undo_begin(command)

    def undo_snap(self):
        self.dd.undo_snap()

    def undo_commit(self):
        self.dd.undo_commit()

    def undo_abort(self):
        self.dd.undo_abort()

    def mouse_button1(self, event):
        unused(event)
        self.undo_begin()

    @abstractmethod
    def mouse_button1_motion(self, event):
        ...

    def mouse_button1_release(self, event):
        unused(event)
        self.undo_commit()

    def mouse_button2(self, event):
        """Handle mouse_button2, usually via self.context_menu()"""
        unused(self, event)

    def abort(self, event):
        unused(event)
        self.undo_abort()

    def context_menu(self, event, items: List):
        """
            Popup a context menu.  Items is a list of:
                (label, command)    - menu entry
                None                - menu separator
        """
        # print('dcp.m2: event=%s .cx=%s .cy=%s .tag=%s' % (event, event.cx, event.cy, event.tag))
        menu = tk.Menu(self.dd.master, tearoff=0)
        for item in items:
            if item is None:
                menu.add_separator()
            else:
                # TODO-how to add check_button and radio_button
                label, command = item
                menu.add_command(label=label, command=command)
        menu.post(event.x_root, event.y_root)


class EditHandleRotate(EditHandle):
    """Edit handle for generic rotation"""

    def __init__(self, shape: DigitizeShape):
        super().__init__(shape)
        self.handle = self.shape_oval('green', 'rotate', radius=4)
        self.line = self.shape_line(fill='grey')
        self.center = self.shape_oval('green', 'what', radius=4)
        self.copy = None

    def update_coords(self):
        """Redraw edit handle based on changes to shape"""
        x1, y1, x2, y2 = self.shape.elem.bbox_int()
        mid = Point((x1+x2)/2, y2)
        up = Point(mid.x, mid.y+10)
        with self.shape.draw_space() as xform:
            mid = xform.transform_pt(mid)
            upv = xform.transform_pt(up) - mid
            handle = mid + upv.unit()*30
            center = xform.transform_pt(self.shape.elem.bbox_int().center)

        self.handle.update(handle.x, handle.y)
        self.line.update(*mid, *handle)
        self.center.update(*center)

    def command_default(self) -> Command:
        from .shape_su import CommandSimpleUndo
        return CommandSimpleUndo([self.shape], 'Edit Rotation')

    def mouse_button1(self, event):
        super().mouse_button1(event)
        self.copy = self.shape.elem.copy()

    def mouse_button1_motion(self, event):
        if event.tag != 'rotate':
            return
        # Compute the angle of mp relative to internal "up" for .copy object
        bbox = self.copy.bbox_int()
        mp = Point(*self.copy.xform.untransform(event.mp.x, event.mp.y))
        up = mp-bbox.center
        angle = math.degrees(math.atan2(up.x, up.y))
        # Now, rotate in external space by that angle
        center = self.copy.bbox().center
        self.shape.elem.restore(self.copy.transform(Transform().rotate_about(angle, center)))
        self.shape.update()

    def mouse_button1_release(self, event):
        super().mouse_button1_release(event)
        self.copy = None

    def mouse_button2(self, event):
        """Handle mouse_button2, usually via self.context_menu()"""
        self.context_menu(event, [('what?', None), None, ('bye', None)])
