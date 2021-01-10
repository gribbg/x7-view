# import tkinter as tk
from tkinter import filedialog

file = filedialog.asksaveasfile(
    'wt',
    # defaultextension='.anim',
    # filetypes=[('anim', '.anim'), ('model', '.model')],
    initialdir='/tmp',
    initialfile='test.model',
    # parent=tk.Tk(),
    title='Save file as'
)

print(file)
