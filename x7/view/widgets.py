import tkinter as tk
from tkinter import ttk
from x7.geom.typing import *

from x7.view import icons
from x7.view.platform import PCFG

__all__ = [
    'Toolbutton', 'RadioToolbutton',
    'ButtonBar', 'ButtonFrame', 'CanvasScrolled', 'StatusBar', 'ValidatingEntry']


class IconHolder:
    @staticmethod
    def handle_icon(icon, kwargs):
        """Handle icon= in init"""
        if icon:
            icon = icons.icon(icon, size=16)
            kwargs['image'] = icon
        return icon


class Toolbutton(ttk.Button, IconHolder):
    """A ttk.Button in the Toolbutton style with icon= support"""

    def __init__(self, master, icon=None, takefocus=True, **kwargs):
        self.icon = self.handle_icon(icon, kwargs)
        super().__init__(master, style='Toolbutton', takefocus=takefocus, **kwargs)


class RadioToolbutton(ttk.Radiobutton, IconHolder):
    """A ttk.Radiobutton in the Toolbutton style with .mode_tag and .select()/.deselect()"""

    def __init__(self, master, *, variable=None, mode_tag=None, icon=None, takefocus=True, **kwargs):
        self.icon = self.handle_icon(icon, kwargs)
        if variable is None:
            raise ValueError('variable must be supplied')
        super().__init__(master, style='Toolbutton', takefocus=takefocus, variable=variable, **kwargs)
        self.mode_tag = mode_tag

    def select(self):
        self.state(('selected', ))

    def deselect(self):
        self.state(('!selected', ))


class ButtonBar(ttk.Frame):
    """A row of buttons"""

    def __init__(self, master, buttons):
        """Init from list of str, (str, func), ttk.Button"""
        super().__init__(master)

        for n, button in enumerate(buttons(self)):
            if not button:
                button = ttk.Label(self, text=' | ')
            button.grid(row=0, column=n, sticky='nw')


class ButtonFrame(ttk.Frame):
    """
        A frame with a button bar on the top and contents below.
    """

    def __init__(self, master, buttons: Callable, contents: Callable):
        """
            :param master:      tk master
            :param buttons:     callable(master) to create list of buttons
            :param contents:    callable(master) to create content widget or [widget,...]
                                List of widgets are stacked vertically, first fills extra space
        """
        super().__init__(master, border=2)
        self.button_bar = ButtonBar(self, buttons)
        body = contents(master=self)
        if not isinstance(body, (list, tuple)):
            body = [body]
        self.contents = body

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.button_bar.grid(row=0, column=0, sticky='nw')
        for idx, elem in enumerate(self.contents):
            elem.grid(row=idx+1, column=0, sticky='nsew' if idx == 0 else 'sew')


class CanvasScrolled(tk.Frame):
    """A canvas object with scroll bars"""

    def __init__(self, master):
        super().__init__(master)
        canvas_row = 1
        if canvas_row:
            # TODO-should the separators be part of this object or the parent?
            frame = self
            ttk.Separator(frame).grid(row=canvas_row-1, column=0, columnspan=2, sticky='we')
            ttk.Separator(frame).grid(row=canvas_row+2, column=0, columnspan=2, sticky='we')
        else:
            self.frame = ttk.Frame(self)
            self.frame.pack(pady=1)
            frame = self.frame
        self.canvas: tk.Canvas = tk.Canvas(frame, width=200, height=100)
        frame.grid_rowconfigure(canvas_row, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        x_scrollbar = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)
        x_scrollbar.grid(row=canvas_row+1, column=0, sticky='ew')

        y_scrollbar = ttk.Scrollbar(frame)
        y_scrollbar.grid(row=canvas_row, column=1, sticky='ns')

        self.canvas.config(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
        self.canvas.grid(row=canvas_row, column=0, sticky='nsew')
        ttk.Sizegrip(frame).grid(row=canvas_row+1, column=1, sticky='se')
        x_scrollbar.config(command=self.canvas.xview)
        y_scrollbar.config(command=self.canvas.yview)

        self.x_scrollbar = x_scrollbar
        self.y_scrollbar = y_scrollbar

    @staticmethod
    def demo():
        root = tk.Tk()

        frame = ButtonFrame(root, lambda master: [None], CanvasScrolled)
        frame.pack(fill='both', expand=True)
        root.mainloop()


class StatusBar(ttk.Frame):
    # TODO-keep log of time, message
    # TODO-Double-click or some other operation to display all messages in separate window
    # TODO-that window should update as new status messages come out
    def __init__(self, master):
        super().__init__(master)
        self.label = ttk.Label(self, anchor=tk.W)
        self.label.pack(fill=tk.X)

    def set(self, s: str):
        self.label.config(text=s)
        self.label.update_idletasks()

    def clear(self):
        self.label.config(text="")
        self.label.update_idletasks()


# TODO-this does not seem to be needed
class ValidationBorder(ttk.Frame):
    """
        A frame/border around a widget that turns red when invalid.

        Expects style.style_setup() to have been called to define ValidationBorder style
    """

    def __init__(self, master=None, padding=1, style='ValidationBorder', **kw):
        super().__init__(master, padding=padding, style=style, **kw)

    def state(self, statespec=None):
        # TODO-Not sure we need to do this
        if statespec is not None:
            # Pass the state onto the children
            for child in self.children.values():
                child.state(statespec)
        return super().state(statespec)


class ValidatingEntry:
    """
        ttk.Entry with optional validation and label

        Not actually a widget, just a composite object with .label, .entry, .entry_field, and .entry_var.
        Expects style.style_setup() to have been called to define ValidationBorder style

        Fields (.label and .entry are the fields to grid/pack if external layout is required):

            * label - the ttk.Label or None if label text was not passed in
            * entry - the border Frame around Entry & message
            * entry_field - the actual Entry field
            * entry_var - the variable bound to the Entry field (use ValidatingEntry.get() to access)
            * message - the validation message (automatically managed by class using result of validator)
    """

    def __init__(self, frame, *, label=None, value='',
                 validator: Optional[Callable[['ValidatingEntry', str], Union[str, bool]]] = None,
                 row=None, col=None, width=80, read_only=False):
        """

        :param frame:       Containing widget
        :param label:       Optional text for a label to be displayed to the left entry field
        :param value:       Optional starting value
        :param validator:   Optional validation function, called with ValidatingEntry and current field value
        :param row:         Optional row.  If row & col are set, call .grid().  Label goes at col, entry at col+1
        :param col:         Optional column.
        :param width:       Width of Entry field
        :param read_only:   True to make Entry field read-only.
        """
        self.frame = frame
        self.validator = validator or (lambda ev, s: True)
        self.label = ttk.Label(frame, text=label, justify=tk.LEFT) if label else None
        self.entry_var = tk.StringVar(frame, value=str(value))
        if PCFG.ui_platform == 'darwin':
            # TODO-Can't get darwin to work with ttk.Frame, so fall-back to tk.Frame and custom state method
            self.entry = tk.Frame(frame)
            self.entry.state = lambda state: \
                self.entry.configure(bg=PCFG.frame_background if '!invalid' in state else 'red')
        else:
            self.entry = ttk.Frame(frame, style='ValidationBorder')
        self.entry.grid_columnconfigure(0, weight=1)
        if read_only:
            self.entry_field = ttk.Label(self.entry, textvariable=self.entry_var, width=width)
        else:
            self.entry_field = ttk.Entry(self.entry, textvariable=self.entry_var, width=width)
        self.entry_field.grid(row=0, column=0, padx=1, pady=1, sticky='we')
        self.message = ttk.Label(self.entry, text='nothing', foreground='red')
        self.message.grid(row=1, column=0, sticky='we')
        self.message.grid_remove()
        if read_only:
            self.entry_field.state(('readonly',))
        if validator:
            self.entry_var.trace('w', self.validate)
            self.entry_field.bind('<FocusIn>', self.validate)
            self.entry_field.bind('<FocusOut>', self.validate)
            self.validate()
        if row is not None and col is not None:
            if label:
                self.label.grid(row=row, column=col, sticky='w')
                self.entry.grid(row=row, column=col + 1, sticky='we')
            else:
                self.entry.grid(row=row, column=col, sticky='we')

    def validate(self, *_args):
        result = self.validator(self, self.entry_var.get())
        if result is True:
            state = ('!invalid',)
            self.message.grid_remove()
        elif result is False:
            state = ('invalid',)
            self.message.grid_remove()
        else:
            state = ('invalid',)
            self.message.configure(text=str(result))
            self.message.grid()
        self.entry.state(state)
        self.entry_field.state(state)

    def get(self):
        return self.entry_var.get()


def test_entry_v():
    from . import style

    def validator(_entry: ValidatingEntry, s: str):
        if 'invalid' in s:
            if 'message' in s:
                return 'Invalid entry because "invalid" is in entry'
            else:
                return False
        return True

    root = tk.Tk()
    style.setup_style()
    ValidatingEntry(root, label='Ev1', value='Ev1 is valid', validator=validator, row=0, col=0)
    ValidatingEntry(root, label='Ev2', value='Ev2 is invalid with message', validator=validator, row=1, col=0)
    ValidatingEntry(root, label='Ev3', value='Ev3 is read_only', validator=validator, row=2, col=0, read_only=True)
    ValidatingEntry(root, label='Ev4', value='Ev4 is read_only and invalid', validator=validator, row=3, col=0, read_only=True)
    root.mainloop()
    exit(0)


def test_scrollbars():
    root = tk.Tk()
    frame = tk.Frame(root, bd=2, relief=tk.SUNKEN)

    x_scrollbar = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)
    y_scrollbar = ttk.Scrollbar(frame)
    canvas = tk.Canvas(frame, bd=2, scrollregion=(0, 0, 1000, 1000), xscrollcommand=x_scrollbar.set,
                       yscrollcommand=y_scrollbar.set)
    grip = ttk.Sizegrip(frame)

    grip.grid(column=1, row=1, sticky=(tk.S, tk.E))
    canvas.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
    y_scrollbar.grid(row=0, column=1, sticky=tk.N + tk.S)
    x_scrollbar.grid(row=1, column=0, sticky=tk.E + tk.W)
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    x_scrollbar.config(command=canvas.xview)
    y_scrollbar.config(command=canvas.yview)

    frame.pack(fill="both", expand=True)
    frame.mainloop()
    exit(0)


if __name__ == '__main__':
    test_entry_v()
    # test_scrollbars()
