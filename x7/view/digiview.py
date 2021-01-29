"""View class for editor"""

import tkinter as tk
from tkinter import ttk
from abc import ABC

# noinspection PyPackageRequirements
from PIL import Image, ImageTk, ImageOps

from .errors import DigitizeInternalError
from x7.geom.geom import BBox
from x7.geom.transform import Transform
from x7.geom.typing import *
from x7.geom.colors import PenBrush
from x7.geom.drawing import DrawingContext
from x7.geom.model import *
from .undo import *
from .digibase import *
from .shapes import *
from .widgets import *


__all__ = ['DigitizeView', 'CommandShapeAdd', 'CommandShapeDel', 'digi_shape_from_elem']
ShapeOrShapes = Union[DigitizeShape, List[DigitizeShape]]


def digi_shape_from_elem(elem: Elem, draw: DigiDraw = None):
    """Return a DigitizeShape based on an Elem"""

    shape_map = DigitizeShape.shape_map()

    digi_class = shape_map.get(elem.__class__, None)
    if digi_class is None:
        raise DigitizeInternalError('ERROR: Missing mapping for %s' % elem.__class__.__name__)
    shape = digi_class(draw, elem)
    return shape


def digi_shapes_from_model(model, names: Optional[Set[str]] = None, draw=None):
    """Return list of DigitizeShapes for use as input to DigitizeWindow"""

    new_way = True
    if new_way:
        model = cast(Group, model)
        return [digi_shape_from_elem(elem, draw) for elem in model.iter_elems_transformed()]
    else:
        shapes = []
        for full_name, elem, transform in model.iter_elems():
            if not names or elem.name in names:
                shape = digi_shape_from_elem(elem, draw)
                shape = shape.transform(transform)
                shapes.append(shape)
    return shapes


class CommandShapeAddDel(Command, ABC):
    """Common base class for CommandShapeAdd and CommandShapeDel"""
    DESCRIPTION = 'Shape Op'

    def __init__(self, dv: 'DigitizeView', shape: ShapeOrShapes, added: bool):
        super().__init__()
        self.dv = dv
        self.da_shapes = shape if isinstance(shape, list) else [shape]
        self.added = added
        if self.added:
            dv_shapes = dv.shapes
            self.shapes_idx = [dv_shapes.index(shape) for shape in self.da_shapes]
        else:
            self.shapes_idx = [-1] * len(self.da_shapes)

    def description(self):
        return self.DESCRIPTION

    def do_snap(self):
        for shape in self.da_shapes:
            shape.draw()
        self.dv.select(self.da_shapes)

    def do_add(self):
        assert self.added is False
        self.dv.shapes_replace([], [], self.da_shapes, self.shapes_idx)
        self.added = True

    def do_del(self):
        if self.added:
            # The never added case is during abort of add/edit event
            self.dv.shapes_replace(self.da_shapes, self.shapes_idx, [], [])
            self.added = False


class CommandShapeDel(CommandShapeAddDel):
    DESCRIPTION = 'Shape Delete'

    def __init__(self, dv: 'DigitizeView', shape: ShapeOrShapes):
        super().__init__(dv, shape, True)

    def do(self):
        self.do_del()

    def undo(self):
        self.do_add()


class CommandShapeAdd(CommandShapeAddDel):
    DESCRIPTION = 'Shape Add'

    def __init__(self, dv: 'DigitizeView', shape: ShapeOrShapes):
        super().__init__(dv, shape, False)

    def snap(self):
        self.do_snap()

    def do(self):
        self.do_add()

    def undo(self):
        self.do_del()


class DigitizeView(DigiDraw):
    """Screen widgets for editor"""
    def __init__(self, draw: DrawingContext, menu_callbacks: Callbacks, base_mode: Mode, master=None):
        super().__init__(draw, master=master or tk.Tk())
        self.callbacks = menu_callbacks
        self.mode_base = base_mode
        self.mode = base_mode
        self.mode_var = tk.StringVar(self.master)
        self.mode_buttons = []
        self.old_mode_stack = []
        self.selection: List[DigitizeShape] = []

        self.frame = ButtonFrame(self.master, self.make_buttons, self.make_content)
        self.canvas: tk.Canvas = self.frame.contents[0].canvas
        w, h = self.draw.background.size
        self.canvas.configure(width=w, height=h)

        self._status_bar: StatusBar = self.frame.contents[1]
        self.bind_events()

        self.show_base_image = False
        self.base_image = Image.new('RGBA', (2, 2), 'black')
        self.base_transform = Transform()
        self.base_image_anchor = (0, 0)
        self.reset_draw(self.draw)

        # Setup empty model placeholder values, waiting for set_model() call
        self.tk_image = None
        self.tk_image_id = -1
        self._shapes: List[DigitizeShape] = []
        self.model = Group('dummy', PenBrush('default'))

        self.frame.focus_set()
        self.frame.pack(fill='both', expand=True)
        # self.set_model(self.model)

    @property
    def dc(self):
        from .digi import CallbacksDC
        if isinstance(self.callbacks, CallbacksDC):
            return self.callbacks.dc
        raise TypeError('Expected self.callbacks to be a CallbacksDC')

    def reset_draw(self, new_draw: DrawingContext):
        self.draw = new_draw
        self.base_image = self.draw.image()
        self.base_transform = self.draw.matrix.copy()
        self.base_image_anchor = self.draw.matrix.untransform(0, 0)

    @property
    def shapes(self) -> Tuple[DigitizeShape]:
        return tuple(self._shapes)

    def shapes_remove(self, shapes: DigitizeShapes, shapes_idx: Optional[List[int]] = None):
        if shapes_idx is None:
            shapes_idx = [-1]*len(shapes)
        self.shapes_replace(shapes, shapes_idx, [], [])

    def shapes_replace(self, this: DigitizeShapes, this_idx: List[int], that: DigitizeShapes, that_idx: List[int]):
        """Replace list this with list that"""
        if len(this) != len(this_idx):
            raise DigitizeInternalError('shapes_replace len mismatch: this=%d this_idx=%d' % (len(this), len(this_idx)))
        if len(that) != len(that_idx):
            raise DigitizeInternalError('shapes_replace len mismatch: that=%d that_idx=%d' % (len(that), len(that_idx)))
        for idx, shape in zip(this_idx, this):
            shape.erase()
            if idx >= 0:
                assert shape == self._shapes[idx]
            else:
                assert shape in self._shapes
        for shape in this:
            self._shapes.remove(shape)

        # Include id(that) so that sort is unique even if that_idx==[-1,-1,...]
        for idx, _, shape in sorted(zip(that_idx, map(id, that), that)):
            if idx < 0:
                self._shapes.append(shape)
            else:
                self._shapes[idx:idx] = [shape]
        for shape in that:
            shape.draw()
            shape.update()
        self.select(that)

    def shapes_replace_single(self, idx, shapes: List[DigitizeShape], do_select=True):
        """Replace self._shapes[idx] (index or slice) with shapes"""
        if not isinstance(idx, slice):
            idx = slice(idx, idx+1)
        for shape in self._shapes[idx]:
            shape.erase()
            if shape in self.selection:
                self.selection.remove(shape)
        self._shapes[idx] = shapes
        for shape in shapes:
            shape.draw()
            shape.update()
        if do_select:
            self.select(shapes)

    def status_set(self, message: str):
        self._status_bar.set(message)

    def status_clear(self):
        self._status_bar.clear()

    def make_content(self, master):
        unused(self)
        return [CanvasScrolled(master), StatusBar(master)]

    def make_buttons(self, master: tk.Widget):
        """Return list of command buttons for the button bar"""

        binder = self.callbacks.binder

        shapes = sorted(self.callbacks.shape_map.keys())
        shapes_max_len = max(map(len, shapes))
        add_menu = ttk.Menubutton(master, text='?', style='Toolbutton')
        add_menu.menu = tk.Menu(add_menu, tearoff=0)
        add_menu["menu"] = add_menu.menu
        for val in shapes:
            add_menu.menu.add_radiobutton(
                label=val, value=val, variable=self.callbacks.shape_var, command=binder('mode_add'))

        select_button = RadioToolbutton(master, mode_tag='Select', value='Select',
                                        text='Select',
                                        variable=self.mode_var, command=binder('mode_select'))
        add_button = RadioToolbutton(master, mode_tag='Add', value='Add',
                                     textvariable=self.callbacks.shape_var, width=shapes_max_len,
                                     variable=self.mode_var, command=binder('mode_add'))
        master.after(10, add_button.invoke)

        self.mode_buttons = [select_button, add_button]

        return [
            Toolbutton(master, icon='undo', command=binder('edit_undo')),     # TODO - indicate if undo/redo is available
            Toolbutton(master, icon='redo', command=binder('edit_redo')),
            ttk.Button(master, text='Show', style='Toolbutton', command=binder('edit_undo_show')),
            select_button,
            add_button,
            add_menu,
            ttk.Button(master, text='ZFit', style='Toolbutton', command=binder('zoom_fit')),
        ]

    def bind_events(self):
        # Setup tk.Frame
        # self.master.unbind_all('<Tab>')
        self.master.unbind_all('<<NextWindow>>')
        self.master.unbind_all('<<PrevWindow>>')

        binder = self.callbacks.binder

        self.frame.bind('<<Undo>>', binder('edit_undo'))
        self.frame.bind('<<Redo>>', binder('edit_redo'))
        self.frame.bind('+', binder('zoom_up'))
        self.frame.bind('=', binder('zoom_up'))
        self.frame.bind('-', binder('zoom_down'))
        self.frame.bind('_', binder('zoom_down'))
        self.frame.bind('0', binder('zoom_100'))
        self.frame.bind('f', binder('zoom_fit'))
        self.frame.bind('z', binder('zoom_box'))

        self.canvas.bind('<Motion>', self.mouse_motion)
        self.canvas.bind('<Button-1>', self.mouse_button1)
        self.canvas.bind('<B1-Motion>', self.mouse_button1_motion)
        self.canvas.bind('<ButtonRelease-1>', self.mouse_button1_release)
        self.canvas.bind('<<ContextMenu>>', self.mouse_button2)
        self.frame.bind('<<SelectAll>>', lambda e: self.select_all())
        self.frame.bind('<<SelectNone>>', lambda e: self.select_none())
        self.frame.bind('<<NextWindow>>', self.select_next)
        self.frame.bind('<<PrevWindow>>', self.select_prev)
        self.frame.bind('<Escape>', self.abort)
        self.frame.bind('<Return>', self.commit)
        self.frame.bind('<<Clear>>', self.do_delete)       # Edit menu generates <<Clear>>
        self.frame.bind('<Delete>', self.do_delete)
        self.frame.bind('<<Cut>>', self.do_cut)
        self.frame.bind('<<Copy>>', self.do_copy)
        self.frame.bind('<<Paste>>', self.do_paste)

    def mouse_motion(self, event):
        return self.mode.mouse_motion(event)

    def mouse_button1(self, event):
        return self.mode.mouse_button1(event)

    def mouse_button1_motion(self, event):
        return self.mode.mouse_button1_motion(event)

    def mouse_button1_release(self, event):
        return self.mode.mouse_button1_release(event)

    def mouse_button2(self, event):
        return self.mode.mouse_button2(event)

    def select_next(self, event):
        return self.mode.select_next(event)

    def select_prev(self, event):
        return self.mode.select_prev(event)

    def abort(self, event):
        return self.mode.abort(event)

    def commit(self, event):
        return self.mode.commit(event)

    def do_delete(self, event):
        return self.mode.delete(event)

    def do_cut(self, event):
        return self.mode.do_cut(event)

    def do_copy(self, event):
        return self.mode.do_copy(event)

    def do_paste(self, event):
        return self.mode.do_paste(event)

    def set_zoom(self, zoom, where=None):
        # Adjust zoom, but keep where (defaults to current center) of screen at center
        bb = self.bbox_window()
        if where is None:
            where = bb.center

        # Now, create a bbox that is the size of the new view
        scale = self.zoom / zoom
        w, h = bb.width * scale / 2, bb.height * scale / 2
        zoom_bb = BBox(where.x-w, where.y-h, where.x+w, where.y+h)
        self.zoom_fit(zoom_bb)

    def bbox_canvas(self):
        """Return the BBox of all as if drawn to canvas"""
        bbox = BBox(None)
        for shape in self._shapes:
            paths = shape.elem.paths(self.draw)
            for path in paths:
                bbox = bbox + BBox(*path.points.getbbox())
        return bbox

    def bbox_window(self):
        """Bounding box of the current window"""
        return BBox(0, 0, self.canvas.winfo_width(), self.canvas.winfo_height())

    def zoom_fit(self, fit_bb=None):
        """Zoom to fit fit_bb (in canvas-coords) on screen.  Use full model if fit_bb is None."""
        if fit_bb is None:
            fit_bb = self.bbox_canvas()
        if fit_bb.is_none:
            self.draw.matrix.set_matrix(self.base_transform)
            self.zoom = 1
        else:
            window_bb = BBox(0, 0, self.canvas.winfo_width(), self.canvas.winfo_height())
            m2w = Transform().scale_bbox(fit_bb, window_bb, True)
            self.draw.matrix.compose_outer(m2w)

            debug = False
            if debug:
                def show_bbox(tag, bb: BBox):
                    bb = round(bb, 2)
                    print('%s %-18s %-18s:%-18s %s' % (tag, bb.size(), bb.p1, bb.p2, bb.center))

                show_bbox(' window: ', window_bb)
                show_bbox(' model:  ', fit_bb)
                print(' now: ', self.draw.matrix)

            self.zoom = self.draw.matrix.scale_vals()[0] / self.base_transform.scale_vals()[0]
        self.refresh()
        self.set_image()

    def run(self):
        """Main interaction loop"""
        self.refresh()
        self.frame.mainloop()

    def set_image(self):
        """Set the tk_image values based on current zoom"""

        if self.tk_image_id >= 0:
            self.canvas.delete(self.tk_image_id)
        if self.show_base_image:
            self.tk_image = ImageTk.PhotoImage(ImageOps.scale(self.base_image, self.zoom, Image.BOX))
            ax, ay = self.draw.matrix.transform(*self.base_image_anchor)
            ax, ay = round(ax), round(ay)
            model_bb = self.bbox_canvas()
            if model_bb.is_none:
                model_bb = BBox(0, 0, self.tk_image.width(), self.tk_image.height())
            self.canvas.configure(scrollregion=tuple(round(model_bb, 0)))
            self.tk_image_id = self.canvas.create_image(ax, ay, image=self.tk_image, anchor=tk.NW)
            self.canvas.tag_lower(self.tk_image_id)

    # noinspection PyShadowingBuiltins
    def set_model(self, model, filter: Optional[Set] = None):
        """Clear canvas and draw the model"""
        self.set_shapes(digi_shapes_from_model(model, names=filter, draw=self))
        self.model = model

    def set_shapes(self, shapes):
        """Clear canvas and set shapes"""
        verbose = False
        if verbose and len(self.ui_map.map) != 0:
            from pprint import pprint
            pprint({'set_shapes: ui_map is': self.ui_map.map})
            print('  shapes is:', self._shapes)

        # Erase all shapes so that tk_ids get reset
        self.select_none()
        for shape in self._shapes:
            shape.erase()
        self._shapes = []
        self.selection = []
        self.undo_stack.reset()

        # Erase everything else (image + stragglers?)
        # TODO-should not need this.  Should only need the call to set_image
        self.canvas.delete(tk.ALL)
        self.tk_image_id = -1
        self.set_image()
        if len(self.ui_map.map) != 0:
            from pprint import pprint
            pprint({'ui_map is not empty': self.ui_map.map})
            assert len(self.ui_map.map) == 0

        # TODO - deactivate things?  What about current mode?
        self.model = None
        self._shapes = shapes
        # self.set_zoom(1.0)        - zoom is not changing

    def select_deselect(self, item: DigitizeShape):
        """Deselect a single item"""
        item.deselect()
        if item in self.selection:
            self.selection.remove(item)

    def select_none(self):
        for shape in self.selection:
            shape.deselect()
        self.selection = []

    def select_all(self):
        self.select(self._shapes)

    def select(self, items, add=False):
        if not isinstance(items, (tuple, list)):
            items = [items]
        if not add:
            if set(items) != set(self.selection):   # Skip deselect if just reselecting selection
                self.select_none()
        if items:
            for item in items:
                item.select()
                if item not in self.selection:
                    self.selection.append(item)

    def select_next_shape(self, direction=1):
        """Select next or prev shape"""
        assert direction in (1, -1)
        if not self._shapes:
            return
        if len(self.selection) == 1:
            selected = self.selection[0]
            assert selected in self._shapes
            idx = self._shapes.index(selected) + direction
            if idx >= len(self._shapes):
                idx = 0
        else:
            if direction > 0:
                idx = 0
            else:
                idx = -1
        self.select(self._shapes[idx])

    def refresh(self):
        """Refresh the entire display (initial, after zoom, ...)"""
        # This should not need to:
        #   a. delete anything from display
        #   b. redraw the image
        # But it does need to tell mode to refresh()
        for shape in self._shapes:
            shape.draw()
            shape.update()
        for item in self.selection:
            item.select()
        # TODO - self.mode.refresh()

    def mode_reset(self):
        self.status_clear()
        self.mode_set(self.mode_base)

    def mode_set(self, mode: Mode):
        """Change the main interaction mode"""
        found = False
        for b in self.mode_buttons:
            if b.mode_tag == mode.MODE_TAG:
                b.select()
                found = True
            else:
                b.deselect()
        if not found:
            print('Strange, mode_set(%s TAG=%s) did not find mode_button' % (mode, mode.MODE_TAG))
        # TODO-Seems like this should only notify the departing mode at most
        if self.mode.exit_ok():
            self.canvas.configure(cursor=mode.CURSOR)
            self.mode = mode
            self.status_set(mode.HELP)
            return True
        else:
            print('Warning: mode change from %s to %s rejected' % (self.mode, mode))
            return False

    def old_push_mode(self, mode):
        """Change the main interaction mode"""
        # print('v.pm(%s)' % mode)
        mode_old = self.mode
        if self.mode_set(mode):
            # print('  sm==True')
            self.old_mode_stack.append(mode_old)
        # print('  mode_stack=', self.mode_stack)

    def old_pop_mode(self):
        """Revert back to previous mode"""

        new_mode = self.old_mode_stack[-1]
        if self.mode_set(new_mode):
            self.old_mode_stack.pop()
        # print('pop_mode: after pop, mode is', self.mode, '  stack is', self.mode_stack)

    def undo_begin(self, command: Command):
        assert self.undo_current_command is None
        self.undo_current_command = command

    def undo_begin_commit(self, command: Command):
        self.undo_begin(command)
        self.undo_commit()

    def undo_snap(self):
        self.undo_current_command.snap()

    def undo_commit(self):
        self.undo_snap()
        self.undo_stack.do(self.undo_current_command)
        self.undo_current_command = None

    def undo_abort(self):
        self.undo_current_command.undo()
        self.undo_current_command = None
