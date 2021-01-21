"""
    Access routines to icons
"""

import tkinter as tk
from tkinter import ttk
from importlib import resources
from typing import Dict

ICONS_RESOURCE = 'x7.view.resources.icons'
icons_loaded: Dict[str, tk.PhotoImage] = dict()


def icon(tag: str, size=24) -> tk.PhotoImage:
    """Load an icon and return tk.PhotoImage for use elsewhere"""

    res_name = '%s-%dx%d.png' % (tag, size, size)
    with resources.path(ICONS_RESOURCE, res_name) as path:
        path = str(path)
        if path not in icons_loaded:
            icons_loaded[path] = tk.PhotoImage(file=str(path))
        return icons_loaded[path]


def test():
    import os

    res_icons = 'x7.view.resources.icons'
    icons = []

    print('is?', resources.is_resource(res_icons, 'pencil-24x24.png'))
    with resources.path(res_icons, 'pencil-24x24.png') as path:
        print('path: %s' % path)
        suffix = '-24x24.png'
        for fn in os.listdir(os.path.dirname(path)):
            if fn.endswith(suffix):
                icons.append(fn[:-len(suffix)])

    root = tk.Tk()
    root_frame = ttk.Frame(root)
    root_frame.pack()

    for row, size in enumerate([24, 32, 64]):
        frame = ttk.Frame(root_frame)
        frame.pack()
        for col, ic in enumerate(icons):
            ttk.Button(frame, image=icon(ic, size), style='Toolbutton').grid(row=row, column=col)
    root.mainloop()


if __name__ == '__main__':
    test()
