import tkinter as tk

from ..details import DetailDialog
from ..digi import DigitizeController
from .common import ModeCommon
from ..digiview import DigitizeView, CommandShapeAdd, digi_shape_from_elem
from ..errors import DigitizeInternalError
from ..shapes import *
from ..shapes.group import DigitizeGroup
from ..shapes.shape_su import CommandSimpleUndo
from ..undo import Command
from x7.geom.colors import PenBrush
from x7.geom.geom import Point
from x7.geom.model import Group, DumpContext
from x7.geom.transform import Transform
from x7.geom.typing import *


class CommandShapeReplace(Command):
    """Replace one list of shapes with a different list of shapes"""

    def __init__(self, dv: DigitizeView, shapes_now: DigitizeShapes, shapes_new: DigitizeShapes):
        super().__init__()
        self.dv = dv
        self.shapes_now = shapes_now
        self.shapes_now_idx = [self.dv.shapes.index(s) for s in shapes_now]
        self.shapes_new = shapes_new

    def description(self):
        now_new = (self.shapes_now, self.shapes_new)
        now, new = [('%d shapes' % len(shapes)) if len(shapes) > 1 else shapes[0].short_name() for shapes in now_new]
        return 'Replace %s with %s' % (now, new)

    def do_snap(self):
        pass

    def do(self):
        self.dv.shapes_replace(self.shapes_now, self.shapes_now_idx, self.shapes_new, [-1]*len(self.shapes_new))

    def undo(self):
        self.dv.shapes_replace(self.shapes_new, [-1]*len(self.shapes_new), self.shapes_now, self.shapes_now_idx)


class CommandShapeExplode(CommandShapeReplace):
    """Explode shape and replace with parts"""

    def __init__(self, dv: DigitizeView, shape: DigitizeShape, parts: List[DigitizeShape]):
        super().__init__(dv, [shape], parts)
        self.shape_kind = shape.__class__.__name__

    def description(self):
        return 'Explode ' + self.shape_kind


class MoveHandle(object):
    """Keep track of events for a shape move"""
    def __init__(self, shapes: List[DigitizeShape], start: Point):
        self.shapes = shapes
        self.last = start
        self.aborted = False
        self.dd = shapes[0].dd
        self.dd.undo_begin(CommandSimpleUndo(self.shapes, 'Move %d shapes' % len(self.shapes)))

    def mouse_button1(self, event):
        raise Exception('MoveHandle.mouse_button1 should never get called')

    def mouse_button1_motion(self, event):
        # print('mh: motion:', event)
        assert self.aborted is False
        dxy = event.mp - self.last
        self.last = event.mp
        for shape in self.shapes:
            moved = shape.transform(Transform().translate(*dxy))
            shape.su_restore(**moved.su_save())
            shape.update()
        self.dd.undo_snap()

    def mouse_button1_release(self, event):
        # print('mh: release:', event)
        unused(event)
        assert self.aborted is False
        self.dd.undo_commit()

    def abort(self, event):
        unused(event)
        self.aborted = True
        self.dd.undo_abort()


class DragSelect(object):
    """Handle interaction for a drag select"""
    def __init__(self, dv: DigitizeView, start: tuple):
        self.dv = dv
        self.start = start
        coords = self.start + self.start
        self.tk_id = self.dv.canvas.create_rectangle(*coords)

    def mouse_button1(self, event):
        raise Exception('MoveHandle.mouse_button1 should never get called')

    def mouse_button1_motion(self, event):
        coords = self.start + (event.cx, event.cy)
        self.dv.canvas.coords(self.tk_id, *coords)

    def mouse_button1_release(self, event):
        # print('mh: release:', event)
        unused(event)
        self.dv.canvas.delete(self.tk_id)
        bbox = self.start + (event.cx, event.cy)
        tk_found = self.dv.canvas.find_enclosed(*bbox)
        found = []
        for tk_id in tk_found:
            tk_found = self.dv.ui_map.obj(tk_id)
            if not tk_found:
                continue
            item, tag = tk_found
            # Skip sub-group items found--user must select entire group
            if isinstance(item, DigitizeShape) and item in self.dv.shapes:
                found.append(item)
        self.dv.select(found)
        # TODO-what about edit handles/control points?  Are they selectable?
        # TODO-make move work for multi-selection
        # Only select objects or control points, not both


class AbortMouseEater(object):
    """Eat mouse events after a keyboard abort"""
    def __init__(self):
        pass

    def mouse_button1(self, event):
        raise Exception('AbortMouseEater.mouse_button1 should never get called')

    def mouse_button1_motion(self, event):
        pass

    def mouse_button1_release(self, event):
        pass

    def abort(self, event):
        pass


class ModeSelectContextMenu:
    def __init__(self, mode: 'ModeSelect'):
        self.mode = mode
        self.active_item = mode.active_item
        self.active_tag = mode.active_tag

    def menu_select(self):
        self.mode.controller.view.select(self.active_item, add=True)

    def menu_deselect(self):
        self.mode.controller.view.select_deselect(self.active_item)

    def menu_edit_points(self):
        self.mode.controller.view.select_none()
        if not isinstance(self.active_item, DigitizeShape):
            return
        self.mode.controller.view.select(self.active_item)
        self.active_item.edit_handle_show()

    def menu_edit_details(self):
        self.mode.controller.view.select_none()
        if not isinstance(self.active_item, DigitizeShape):
            return
        self.mode.controller.view.select(self.active_item)
        DetailDialog(self.mode.controller.view, self.active_item)

    def menu_dump_data(self):
        # TODO-scale digits based on total model extents?
        if not isinstance(self.active_item, DigitizeShape):
            return
        dc = DumpContext()
        for shape in self.mode.controller.view.selection:
            shape.elem.dump(dc)
        print(dc.output(just_lines=True))

    def menu_dump_as_curves(self):
        if not isinstance(self.active_item, DigitizeShape):
            return
        dc = DumpContext()
        for c in self.active_item.as_curves():
            c.elem.dump(dc)
        print(dc.output())

    def menu_explode(self):
        if not isinstance(self.active_item, DigitizeShape):
            return
        curves = self.active_item.as_curves()
        command = CommandShapeExplode(self.mode.controller.view, self.active_item, curves)
        self.mode.controller.view.undo_begin_commit(command)

    def menu_group(self):
        """Group selected items"""
        view = self.mode.controller.view
        elems = [shape.elem for shape in view.selection]
        if not elems:
            raise DigitizeInternalError('Empty group/selection?')
        Group.RAISE_ON_EMPTY = True
        elem = Group('group#1', PenBrush('default'), elems=elems, fix_names=True)
        group = DigitizeGroup(view, elem)
        command = CommandShapeReplace(view, view.selection, [group])
        view.undo_begin_commit(command)

    def menu_ungroup(self):
        selection = self.mode.controller.view.selection
        shapes = []
        for shape in selection:
            for elem in shape.elem.iter_elems_transformed():
                shapes.append(digi_shape_from_elem(elem, self.mode.controller.view))
        if shapes:
            command = CommandShapeReplace(self.mode.controller.view, selection, shapes)
            self.mode.controller.view.undo_begin_commit(command)

    def popup(self, event):
        # print('dcp.m2: event=%s .cx=%s .cy=%s .tag=%s' % (event, event.cx, event.cy, event.tag))
        menu = tk.Menu(self.mode.controller.master, tearoff=0)
        menu.add_command(label="Select", command=self.menu_select)
        menu.add_command(label="Deselect", command=self.menu_deselect)
        menu.add_separator()
        menu.add_command(label='Edit Points', command=self.menu_edit_points)
        menu.add_command(label='Edit Details', command=self.menu_edit_details)
        menu.add_command(label='Explode', command=self.menu_explode)

        selection = self.mode.controller.view.selection
        group = bool(len(selection) > 1)
        ungroup = bool(len(selection) == 1 and isinstance(selection[0], DigitizeGroup))
        state_map = ['disabled', 'normal']
        menu.add_command(label='Group', command=self.menu_group, state=state_map[group])
        menu.add_command(label='Ungroup', command=self.menu_ungroup, state=state_map[ungroup])
        if len(selection) == 1:
            selection[0].context_extra(menu)

        menu.add_separator()
        menu.add_command(label='Dump Data', command=self.menu_dump_data)
        menu.add_command(label='Dump Curves', command=self.menu_dump_as_curves)

        menu.tk_popup(event.x_root, event.y_root)


class ModeSelect(ModeCommon):
    """Selection mode: select & drag objects.  Right-click goes to main or selected object"""
    MODE_TAG = 'Select'
    HELP = 'Select object by click, multiple by click and drag'

    def __init__(self, controller: DigitizeController):
        super().__init__(controller)

    def mouse_motion(self, event):
        assert self.active_item is None
        assert self.controller.view.undo_current_command is None

    def mouse_button1(self, event):
        self.controller.view.frame.focus_set()
        if self.active_item:
            # TODO-Ignore this mouse press during a menu(?) action
            print('Weird: mouse1 during mouse2 active: ai=', self.active_item)
            return

        event = self.event_enrich('mouse_button1', event)
        if self.active_item:
            if hasattr(self.active_item, 'mouse_button1'):
                self.active_item.mouse_button1(event)
            else:
                assert isinstance(self.active_item, DigitizeShape)
                if self.active_item not in self.controller.view.selection:
                    self.controller.view.select(self.active_item)
                self.active_item = MoveHandle(self.controller.view.selection, event.mp)
        else:
            self.active_item = DragSelect(self.controller.view, (event.cx, event.cy))

    def mouse_button1_motion(self, event):
        event = self.event_enrich('mouse_button1_motion', event, 'is')
        if self.active_item:
            if hasattr(self.active_item, 'mouse_button1_motion'):
                self.active_item.mouse_button1_motion(event)

    def mouse_button1_release(self, event):
        event = self.event_enrich('mouse_button1_release', event, 'was')
        if self.active_item:
            if hasattr(self.active_item, 'mouse_button1_release'):
                self.active_item.mouse_button1_release(event)
            self.active_item = None
            self.active_tag = None

    def mouse_button2(self, event):
        if self.active_item:
            # TODO-Ignore this mouse press during a drag action
            print('Weird: mouse2 during mouse1 drag.  Ignored. s.ai=', self.active_item)
            return
        event = self.event_enrich('mouse_button2', event)
        if not self.active_item:
            self.controller.top_level_context_menu.popup(event)
        else:
            selection = self.controller.view.selection
            if self.active_item in selection and len(selection) > 1:
                # This will popup with Group option enabled
                self.context_menu(event)
            else:
                if isinstance(self.active_item, DigitizeShape):
                    self.controller.view.select([self.active_item])
                if hasattr(self.active_item, 'mouse_button2'):
                    if self.verbose:
                        # print('mouse_button1(%s @ %d, %d) -> (%d, %d)' % (event, event.x, event.y, cx, cy))
                        print('  active is %s.%s' % (self.active_item.__class__.__name__, self.active_tag))
                    self.active_item.mouse_button2(event)
                else:
                    self.context_menu(event)
        self.active_item = None
        self.active_tag = None

    def select_next(self, event):
        """Select next curve/control point.  Usually <Tab>"""
        self.controller.view.select_next_shape(1)

    def select_prev(self, event):
        """Select prev curve/control point.  Usually <Shift-Tab>"""
        self.controller.view.select_next_shape(-1)

    def abort(self, event):
        """Abandon current edit.  Usually <Escape>"""
        verbose = self.verbose or True
        if not self.active_item:
            if self.controller.view.selection:
                self.controller.view.select_none()
            else:
                # TODO-good for debugging, bad for production.  Needs chicken box at least.
                self.controller.view.master.quit()
        else:
            if hasattr(self.active_item, 'abort'):
                # Abort during mouse move
                if verbose:
                    print('abort(%s @ %d, %d)' % (event, event.x, event.y))
                    print('  active was %s.%s' % (self.active_item.__class__.__name__, self.active_tag))
                self.active_item.abort(event)
            else:
                if verbose:
                    print('abort(%s @ %d, %d) ignored' % (event, event.x, event.y))
                # TODO-this seems like a hack.  Should abort() be required?
                self.controller.view.select_none()
            self.active_item = AbortMouseEater()
            self.active_tag = None

    def commit(self, event):
        """Commit current edit and exit mode.  Usually <Enter>"""
        print('commit(%s)' % event)

    def delete(self, event):
        self.do_cut(event, save_to_buffer=False)

    def do_cut(self, event, save_to_buffer=True):
        from ..digiview import CommandShapeDel

        # print('do_cut(%s, %s)' % (event, save_to_buffer))
        to_cut = self.controller.view.selection
        if to_cut:
            if save_to_buffer:
                self.controller.copy_buffer = [s.copy() for s in to_cut]
                self.controller.copy_count = 0
            cmd = CommandShapeDel(self.controller.view, to_cut)
            self.controller.view.undo_begin_commit(cmd)

    def do_copy(self, event):
        to_copy = self.controller.view.selection
        if to_copy:
            self.controller.copy_buffer = [s.copy() for s in to_copy]
            self.controller.copy_count = 0

    def do_paste(self, event):
        to_paste = self.controller.copy_buffer
        if to_paste:
            self.controller.copy_count += 1
            off = self.controller.copy_count*3
            trans = Transform().translate(off, -off)
            to_paste = [s.transform(trans) for s in to_paste]
            cmd = CommandShapeAdd(self.controller.view, to_paste)
            self.controller.view.undo_begin_commit(cmd)

    def context_menu(self, event):
        # print('dcp.m2: event=%s .cx=%s .cy=%s .tag=%s' % (event, event.cx, event.cy, event.tag))
        menu = ModeSelectContextMenu(self)
        menu.popup(event)
