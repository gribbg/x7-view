"""
    Edit details of a shape
"""
import os
import tkinter as tk
from tkinter import simpledialog

from x7.geom.typing import *


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
        self.path_var = None
        self.path = None
        self.entry_var = None
        self.entry = None
        self.text: Optional[tk.Text] = None
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        frame = tk.Frame(master)

        label = tk.Label(frame, text='Dir:', justify=tk.LEFT)
        label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        path_var = tk.StringVar(frame, value=str(self.initial_dir))
        path_var.trace('w', self.path_changed)
        self.path_var = path_var
        path = tk.Entry(frame, textvariable=path_var, width=80)
        path.grid(row=0, column=1, padx=5, sticky=tk.W+tk.E)
        self.path = path

        label = tk.Label(frame, text='File:', justify=tk.LEFT)
        entry_var = tk.StringVar(frame, value=str(self.initial_file))
        entry_var.trace('w', self.do_validate)
        self.entry_var = entry_var
        entry = tk.Entry(frame, textvariable=entry_var, width=80)
        label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        entry.grid(row=1, column=1, padx=5, sticky=tk.W+tk.E)
        self.entry = entry
        frame.pack()

        text = tk.Text(frame)
        text.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E+tk.S+tk.N)
        text.configure(state=tk.DISABLED)
        self.text = text

        self.path_changed()

        return self.entry

    def text_update(self, new_text):
        text = self.text
        text.configure(state=tk.NORMAL)
        text.delete(1.0, tk.END)
        text.insert(1.0, new_text)
        text.configure(state=tk.DISABLED)

    def path_changed(self, name=None, index=None, mode=None):
        unused(name, index, mode)
        new_path = self.path_var.get()
        print('path_changed: new=', new_path)
        if os.path.isdir(new_path):
            # header = new_path.center(80)+'\n'
            self.path.configure(background='systemWindowBody')
            entries = [e+('/' if os.path.isdir(new_path+'/'+e) else '') for e in os.listdir(new_path)]
            self.text_update('\n'.join(sorted(entries)))
        else:
            self.path.configure(background='#FF8080')

    def do_validate(self, name=None, index=None, mode=None):
        unused(self, name, index, mode)
        pass

    def apply(self):
        self.result = self.path_var.get() + '/' + self.entry_var.get()


if __name__ == '__main__':
    d = FileDialog(tk.Tk(), title='Open file')
    d.mainloop()
