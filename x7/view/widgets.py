import tkinter as tk
from tkinter import ttk
from x7.geom.typing import *


__all__ = ['ButtonBar', 'ButtonFrame', 'CanvasScrolled', 'StatusBar']


class ButtonBar(tk.Frame):
    """A row of buttons"""

    def __init__(self, master, buttons):
        """Init from list of str, (str, func), tk.Button"""
        super().__init__(master)

        for n, button in enumerate(buttons(self)):
            if not button:
                button = tk.Label(self, text=' | ')
            button.grid(row=0, column=n, sticky='nw')


class ButtonFrame(tk.Frame):
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
        super().__init__(master, border=3, relief=tk.RIDGE)
        self.canvas: tk.Canvas = tk.Canvas(self, width=200, height=100)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        x_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        x_scrollbar.grid(row=1, column=0, sticky='ew')

        y_scrollbar = ttk.Scrollbar(self)
        y_scrollbar.grid(row=0, column=1, sticky='ns')

        self.canvas.config(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        ttk.Sizegrip(self).grid(column=1, row=1, sticky='se')
        x_scrollbar.config(command=self.canvas.xview)
        y_scrollbar.config(command=self.canvas.yview)

        self.x_scrollbar = x_scrollbar
        self.y_scrollbar = y_scrollbar

    # self.pack(fill='both', expand=True)

    @staticmethod
    def demo():
        root = tk.Tk()

        frame = ButtonFrame(root, lambda master: [None], CanvasScrolled)
        frame.pack(fill='both', expand=True)
        root.mainloop()


class StatusBar(tk.Frame):
    # TODO-keep log of time, message
    # TODO-Double-click or some other operation to display all messages in separate window
    # TODO-that window should update as new status messages come out
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.label = tk.Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.label.pack(fill=tk.X)

    def set(self, s: str):
        self.label.config(text=s)
        self.label.update_idletasks()

    def clear(self):
        self.label.config(text="")
        self.label.update_idletasks()


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
    import sys
    sys.exit(0)


if __name__ == '__main__':
    test_scrollbars()
