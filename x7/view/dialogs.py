"""
    Edit details of a shape
"""
import os
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog

from x7.geom.typing import *
from x7.view.widgets import ValidatingEntry


def file_save_as(self):
    # http://effbot.org/tkinterbook/tkinter-file-dialogs.htm
    from tkinter import filedialog
    fn = filedialog.asksaveasfilename(
        # defaultextension='.anim',
        # filetypes=[('anim', '.anim'), ('model', '.model')],
        initialdir=self.base_dir,
        initialfile='test.model',
        parent=self.master,
        # parent=self.view.frame,
        title='Save file as'
    )
    return fn


def file_dialog(parent, title=None, initial_dir=None, initial_file=None):
    dialog = FileDialog(parent, title, initial_dir, initial_file)
    return dialog.result


class FileDialog(simpledialog.Dialog):
    """
        This should be just tkinter.filedialog..., but that seems to crash.
        Construct the dialog, then look for dialog.result
    """
    def __init__(self, parent, title=None, initial_dir=None, initial_file=None):
        self.initial_dir = initial_dir or '/tmp'
        self.initial_file = initial_file or 'foo.txt'
        self.path: Optional[ttk.Entry] = None
        self.entry: Optional[ttk.Entry] = None
        self.text: Optional[tk.Text] = None
        self.result = None
        super().__init__(parent, title)

    def body(self, master: tk.Widget):
        master.pack(expand=1, fill=tk.BOTH)
        frame = master
        frame.grid_columnconfigure(1, weight=2)

        def val_path(_ve, new_path):
            if not os.path.isdir(new_path) or new_path.strip() != new_path:
                self.text_update('')
                return False
            try:
                entries = [e+('/' if os.path.isdir(new_path+'/'+e) else '') for e in os.listdir(new_path)]
            except OSError as err:
                self.text_update('')
                return str(err)
            self.text_update('\n'.join(sorted(entries)))
            return True

        # Note: must create self.text before self.path due to validation
        self.text = tk.Text(frame)
        self.text.grid(row=2, column=0, columnspan=2, sticky='news')
        self.text.configure(state=tk.DISABLED)

        self.path = ValidatingEntry(frame, label='Dir:', value=str(self.initial_dir), validator=val_path, row=0, col=0)
        self.entry = ValidatingEntry(frame, label='File:', value=str(self.initial_file), row=1, col=0)

        return self.entry.entry_field

    def text_update(self, new_text):
        text = self.text
        text.configure(state=tk.NORMAL)
        text.delete(1.0, tk.END)
        text.insert(1.0, new_text)
        text.configure(state=tk.DISABLED)

    def do_validate(self, name=None, index=None, mode=None):
        unused(self, name, index, mode)
        pass

    def apply(self):
        # self.result = self.path_var.get() + '/' + self.entry_var.get()
        self.result = self.path.get() + '/' + self.entry.get()


def test_dialogs():
    from . import style

    root = tk.Tk()
    style.setup_style()

    def cb():
        fd = FileDialog(root, title='Open file')
        print('After: result is %r' % fd.result)

    root.after(100, cb)
    root.mainloop()


if __name__ == '__main__':
    test_dialogs()
