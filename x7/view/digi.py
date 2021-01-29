"""
Main digitize controller.  All callbacks flow through here
"""
import re
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import screeninfo

from x7.geom.typing import *
from x7.geom.colors import PenBrush
from x7.geom.drawing import DrawingContext
from x7.geom.geom import Vector, Point
from x7.geom.model import ControlPoint, Group, DumpContext, Elem, GroupBuilder
from x7.geom.transform import Transform
from .style import setup_style
from .shapes import *
from .digibase import *
from .digiview import *


class TopLevelContextMenu(object):
    def __init__(self, controller: 'DigitizeController'):
        self.controller = controller

    def menu_quit(self):
        # TODO-chicken box
        self.controller.view.master.quit()

    def menu_dump_data(self):
        self.controller.dump_data()

    def popup(self, event):
        # print('Mouse2: tag=', tag, tk_id, event.x, event.y, event, id(event), event.widget)
        menu = tk.Menu(self.controller.view.master, tearoff=0)
        menu.add_command(label="Dump Data", command=self.menu_dump_data)
        menu.add_separator()
        menu.add_command(label='Quit', command=self.menu_quit)
        menu.post(event.x_root, event.y_root)


class TopLevelMenu(object):
    """Application menubar"""
    def __init__(self, controller: 'DigitizeController'):
        self.controller = controller

        self.menu = self.make_menu(self.controller.view.master)
        self.controller.view.master.config(menu=self.menu)

    def menu_quit(self):
        # TODO-chicken box
        self.controller.view.master.quit()

    def menu_dummy(self):
        unused(self)
        print('menu: dummy')

    def menu_about(self):
        unused(self)
        from x7 import geom
        messagebox.showinfo("About Geom Viewer", 'Geom version: ' + geom.__version__)

    def menu_bkg_clear(self):
        img = self.controller.view.base_image
        img.paste((250, 250, 250, 255), (0, 0) + img.size)
        self.controller.view.set_image()

    def menu_bkg_set_up(self):
        unused(self)
        messagebox.showinfo("Set Up", 'Set Up to be implemented')

    def make_model_open(self, model_name):
        def opener():
            self.controller.model_open(model_name)
        return opener

    def make_menu(self, root):
        menubar = tk.Menu(root)

        # create a pulldown menu, and add it to the menu bar
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.controller.file_open)
        file_menu.add_command(label="Save", command=self.controller.file_save)
        file_menu.add_command(label="Save As...", command=self.controller.file_save_as)
        file_menu.add_command(label="Dump Data", command=self.controller.dump_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # create more pulldown menus
        edit_menu = tk.Menu(menubar, tearoff=0)
        view_frame = self.controller.view.frame
        background_menu = tk.Menu(edit_menu, tearoff=0)
        background_menu.add_command(label="Clear", command=self.menu_bkg_clear)
        background_menu.add_command(label="Set Up", command=self.menu_bkg_set_up)

        edit_menu.add_command(label="Undo", command=lambda: view_frame.event_generate('<<Undo>>'))
        edit_menu.add_command(label="Redo", command=lambda: view_frame.event_generate('<<Redo>>'))
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=lambda: view_frame.event_generate('<<Cut>>'))
        edit_menu.add_command(label="Copy", command=lambda: view_frame.event_generate('<<Copy>>'))
        edit_menu.add_command(label="Paste", command=lambda: view_frame.event_generate('<<Paste>>'))
        edit_menu.add_command(label="Delete", command=lambda: view_frame.event_generate('<<Clear>>'))
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=lambda: view_frame.event_generate('<<SelectAll>>'))
        edit_menu.add_command(label="Select None", command=lambda: view_frame.event_generate('<<SelectNone>>'))
        edit_menu.add_separator()
        edit_menu.add_cascade(label="Background", menu=background_menu)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.menu_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        return menubar


class CallbacksDC(Callbacks):
    def __init__(self, dc: 'DigitizeController'):
        # Need to import .modes to initialize all_shapes
        from .modes import ModeSelect

        super().__init__((), error_on_missing=False)
        self.dc = dc
        self.shape_map = ModeSelect.all_shapes()
        self.shape_var = tk.StringVar(dc.master)
        self.shape_var.set('Curve')

    def edit_undo_show(self, event, tag):
        unused(event, tag)
        print('Selected items:')
        for item in self.dc.view.selection:
            print('  ', item)
        if self.dc.view.undo_stack.undo_empty:
            print('Undo stack:  -empty-')
        else:
            print('Undo stack:')
            for item in list(reversed(self.dc.view.undo_stack.undo_stack))[:10]:
                print(' ', item.description())
        if self.dc.view.undo_stack.redo_empty:
            print('Redo stack:  -empty-')
        else:
            print('Redo stack:')
            for item in list(reversed(self.dc.view.undo_stack.redo_stack))[:10]:
                print(' ', item.description())
        print('ui_map:')
        for tk_id, v in self.dc.view.ui_map.map.items():
            tk_type = self.dc.view.canvas.type(tk_id)
            coords = self.dc.view.canvas.coords(tk_id)
            print('  %s: %s.%s %s %s' % (tk_id, v[0], v[1], tk_type, coords))
        self.dc.validate()

    def edit_undo(self, event, tag):
        # print('cb dc.edit_undo(%s, %s)' % (event, tag))
        unused(event, tag)
        if self.dc.view.undo_stack.undo_empty:
            pass    # messagebox.showwarning('Undo', 'Undo stack empty')
        else:
            self.dc.view.undo_stack.undo()

    def edit_redo(self, event, tag):
        # print('cb dc.edit_redo(%s, %s)' % (event, tag))
        unused(event, tag)
        if self.dc.view.undo_stack.redo_empty:
            pass    # messagebox.showwarning('Redo', 'Redo stack empty')
        else:
            self.dc.view.undo_stack.redo()

    def zoom_up(self, event, tag):
        unused(event, tag)
        self.dc.view.set_zoom(self.dc.view.zoom * 1.2)

    def zoom_down(self, event, tag):
        unused(event, tag)
        self.dc.view.set_zoom(self.dc.view.zoom / 1.2)

    def zoom_100(self, event, tag):
        unused(event, tag)
        self.dc.view.set_zoom(1.0)

    def zoom_fit(self, event, tag):
        unused(event, tag)
        self.dc.view.zoom_fit()

    def zoom_box(self, event, tag):
        unused(event, tag)
        from .modes import ModeZoom
        self.dc.view.mode_set(ModeZoom(self.dc))

    def mode_add(self, event, tag):
        unused(event, tag)
        mode_class = self.shape_map[self.shape_var.get()]
        self.dc.view.mode_set(mode_class(self.dc))

    def mode_select(self, event, tag):
        unused(event, tag)
        from .modes import ModeSelect
        if self.dc.view.mode.__class__ != ModeSelect:
            self.dc.view.mode_reset()


class DigitizeController(object):
    def __init__(self, draw, model: Union[None, Elem, GroupBuilder], model_filter=None):
        self.draw = draw
        self.model = model.the_group if isinstance(model, GroupBuilder) else model
        self.model_filter = model_filter
        self.master = tk.Tk()
        setup_style()
        self.callbacks = CallbacksDC(self)
        # print('cb trace=', self.callbacks.trace)
        self.view = self.make_view()
        self.top_level_context_menu = TopLevelContextMenu(self)
        self.top_level_menu = TopLevelMenu(self)
        self.copy_buffer = None
        self.copy_count = 0
        self.file_name = None
        self.base_dir = '/Users/glenn/PycharmProjects/animate/saves'

    def run(self):
        """Main interaction loop"""
        self.view.run()

    def make_view(self):
        """Create the screen widgets.  Canvas is empty"""
        from .modes import ModeSelect
        view = DigitizeView(self.draw, self.callbacks, ModeSelect(self), master=self.master)
        if self.model:
            view.set_model(self.model, self.model_filter)
        return view

    def validate(self):
        """Make sure all items in ui_map are in shapes and vice-versa"""

        shapes = set(self.view.shapes)
        if len(shapes) != len(self.view.shapes):
            print('Weird: len(view.shapes)=%d  len(set(view.shapes))=%d' % (len(self.view.shapes), len(shapes)))

        ui_shapes = set(k for k, t in self.view.ui_map.map.inverse.keys())
        if shapes != ui_shapes:
            print('Weird: shapes!=ui_shapes')

            def print_shapes(title, p_shapes):
                print(title, ', '.join('%s.%s at 0x%x' % (s.short_name(), s.elem.name, id(s)) for s in p_shapes))

            print_shapes('  Extra shapes: ', shapes-ui_shapes)
            print_shapes('  Extra ui_shapes: ', ui_shapes-shapes)
        else:
            print('Validate: apparently valid')

    def extract_model(self, shapes=None):
        """Temp function to extract model-type objects from shape objects"""
        # top = Group(self.model.name, self.model.pens_by_shape)
        # pen = PenBrush('black')
        # TODO-Don't wrap in group if top-level is a single group
        elems = [shape.elem for shape in shapes or self.view.shapes]
        name = self.model.name if self.model else 'default'
        top = Group(name, PenBrush('default'), elems=elems, fix_names=True)
        return top

    # noinspection PyUnresolvedReferences
    def model_open(self, model_name):
        from kltv.logos import get_logo
        from kltv.full_logo import make_full_logo
        from kltv.kitty import make_kitty
        from kltv.radio import make_radio
        from kltv.tv import make_tv

        models = dict(
            full=make_full_logo,
            kitty=make_kitty,
            radio=make_radio,
            tv=make_tv,
        )
        model_func = models[model_name]
        model = model_func(draft=False)

        logo_name = 'tv' if model_name == 'radio' else model_name
        logo_image, logo_matrix = get_logo(logo=logo_name, grid=True)
        draw = DrawingContext(logo_image, logo_matrix)
        self.view.reset_draw(draw)
        self.view.set_model(model)
        self.view.zoom_fit()
        self.view.refresh()
        self.validate()

    def file_open(self):
        # http://effbot.org/tkinterbook/tkinter-file-dialogs.htm
        fn = filedialog.askopenfilename(
            # defaultextension='.anim',
            # filetypes=[('anim', '.anim'), ('all', '*')],
            initialdir=self.base_dir,
            initialfile='test.model',
            parent=self.view.frame,
            title='Open file'
        )
        print('Open: fn=', fn)
        if fn:
            if fn.endswith('.model'):
                self.file_open_model(fn)
            else:
                self.file_open_shapes(fn)

    def file_open_model(self, fn):
        variables = {}
        exec(open(fn, 'rt').read(), variables)
        model = variables['model']
        print(model)
        self.view.set_model(model)
        self.view.refresh()
        self.validate()

    def file_open_shapes(self, fn):
        funcs = dict(
            Point=Point,
            Vector=Vector,
            ControlPoint=ControlPoint,
            DigitizeCurve=DigitizeCurve,
            DigitizeGroup=DigitizeGroup,
            DigitizeRoundedRectangle=DigitizeRoundedRectangle,
            DigitizeRectangle=DigitizeRectangle,
            Transform=Transform,
        )
        shapes: List[DigitizeShape] = eval(open(fn, 'rt').read(), funcs)
        for shape in shapes:
            shape.set_dd(self.view)
        self.view.set_shapes(shapes)
        self.view.refresh()
        self.validate()

    def file_save(self, file_name: str = None):
        self.validate()
        file_name = self.file_name if file_name is None else file_name
        if not file_name:
            self.file_save_as()
        else:
            with open(file_name, 'wt', encoding='utf-8') as out:
                self.file_save_model(out)

    def file_save_model(self, out_file):
        model = self.extract_model()
        out_file.write(model.dump().output())

    def file_save_as(self):
        from .dialogs import file_dialog
        fn = file_dialog(self.master, initial_dir=self.base_dir, initial_file='test.model')
        if fn:
            self.file_save(file_name=fn)
            self.file_name = fn

    def dump_data(self):
        dc = DumpContext()
        for shape in self.view.shapes:
            shape = cast(DigitizeShape, shape)
            shape.elem.dump(dc)
        print(dc.output())


def screen_size() -> Tuple[int, int, int, int]:
    """
        Get the size of the current screen.

        :return: (width, height, left, top)
    """
    # https://stackoverflow.com/questions/3129322/how-do-i-get-monitor-resolution-in-python/56913005#56913005
    # ISSUE: This causes a window to popup and the next root window is behind all others

    root = tk.Tk()
    root.update_idletasks()
    root.attributes('-fullscreen', True)
    root.state('iconic')
    geometry = root.winfo_geometry()
    root.destroy()
    w, h, l, t = map(int, re.split(r'[+x]', geometry))
    return w, h, l, t


def test_digi():
    # noinspection PyPackageRequirements
    from PIL import Image
    from x7.geom.drawing import DrawingContext
    from x7.geom.transform import Transform
    from x7.geom.model import gen_test_model

    #  image = Image.open('/tmp/parrot.jpg')
    m = screeninfo.get_monitors()[0]
    w, h, l, t = m.width, m.height, m.x, m.y
    # w, h, l, t = screen_size()
    w = w * 3 // 4
    h = h * 3 // 4
    w, h = 600, 200
    image = Image.new('RGBA', (w, h), 'lightgrey')
    # TODO - add grid over blank image
    # TODO - eliminate default background image
    mat = Transform.canvas_fit(canvas_size=image.size, zoom=5, zero_zero=(w//2, h//2))
    draw = DrawingContext(image, mat)

    show_model = False
    if show_model:
        model = gen_test_model()
        dc = DigitizeController(draw, model)
    else:
        dc = DigitizeController(draw, None)
    dc.run()


def show_virtual_events():
    root = tk.Tk()
    for ev in sorted(root.event_info()):
        print('%-32s %s' % (ev, root.event_info(ev)))


def show_mode_shapes():
    from .modes import ModeSelect
    print(list(Mode.all_subclasses()))
    for m in ModeSelect.all_modes():
        print(m)
    from pprint import pprint
    pprint(ModeSelect.all_shapes())


if __name__ == '__main__':
    # show_mode_shapes()
    test_digi()
