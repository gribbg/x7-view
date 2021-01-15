"""
    Edit details of a shape
"""

import tkinter as tk
from tkinter import simpledialog

from .digiview import DigitizeView
from .platform import PCFG
from .shapes import DigitizeShape
from .shapes.shape_su import CommandSimpleUndo
from x7.geom.typing import *


__all__ = ['Detail', 'DetailFloat', 'DetailPoint', 'DetailDialog']


class Detail(object):
    """A single detail to be edited"""

    def __init__(self, target, attr: str, ro=False, value=None):
        self.target = target
        self.attr = attr
        self.ro = ro or value is not None
        self.entry = None
        self.entry_var = None
        self.label = None
        self.orig_value = value if value is not None else getattr(target, attr)

    def elems(self, frame) -> tuple:        # label, entry field(s)
        self.label = tk.Label(frame, text=self.attr, justify=tk.LEFT)
        entry_var = tk.StringVar(frame, value=str(self.orig_value))
        entry_var.trace('w', self.do_validate)
        self.entry_var = entry_var
        self.entry = tk.Entry(frame, textvariable=entry_var, width=80)
        if self.ro:
            self.entry.configure(state='disabled')
        return self.label, self.entry

    def do_validate(self, name=None, index=None, mode=None):
        unused(name, index, mode)
        # print('do_validate(%s, %s, %s) -> %r' % (name, index, mode, self.entry.get()))

        validation = self.validate()
        if validation is True:
            self.entry.configure(background=PCFG.window_body)
        else:
            old = self.entry.configure()
            print('Going red, old was', old['background'])
            self.entry.configure(background='#FF8080')

    def validate(self):
        """Return True if this entry is valid, error string otherwise"""
        if self.ro or self.entry.get() != 'ERROR':
            return True
        return "Error here"

    def update(self):
        if not self.ro:
            print('update %s -> %s' % (self.attr, self.entry.get()))
            setattr(self.target, self.attr, self.entry.get())


class DetailPoint(Detail):
    """Detail for Point(), read-only for now"""

    def __init__(self, target, attr: str, ro=True):
        super().__init__(target, attr, ro=ro)
        self.orig_value = self.orig_value.round(2)


class DetailFloat(Detail):
    """Detail for float, read-only for now"""

    def __init__(self, target, attr: str, ro=True):
        super().__init__(target, attr, ro=ro)
        self.orig_value = round(self.orig_value, 2)


class DetailDialog(simpledialog.Dialog):
    def __init__(self, dv: DigitizeView, shape: DigitizeShape):
        self.dv = dv
        self.shape = shape
        self.details = shape.details()
        self.undo_begin()
        self.undo_state = 'begin'
        super().__init__(dv.frame, 'Edit Details')

    def body(self, master):
        for row, detail in enumerate(self.details):
            if detail:
                label, entry = detail.elems(master)
                label.grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
                entry.grid(row=row, column=1, padx=5, sticky=tk.W+tk.E)
            else:
                label = tk.Label(master, justify=tk.LEFT)
                label.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

        for dt in self.details:
            if not dt.ro:
                return dt.entry
        return self.details[0].entry

    def validate(self):
        valid = True
        for d in self.details:
            if not d:
                continue
            validation = d.validate()
            if validation is not True:
                d.entry.configure(background='red')
                valid = False
        return valid

    def apply(self):
        for d in self.details:
            if d:
                d.update()
        self.undo_snap()
        self.undo_commit()

    def cancel(self, event=None):
        self.undo_abort()
        super().cancel(event)

    def undo_begin(self, command=None):
        command = command or CommandSimpleUndo([self.shape], 'Detail Edit')
        self.dv.undo_begin(command)

    def undo_snap(self):
        self.dv.undo_snap()

    def undo_commit(self):
        assert self.undo_state == 'begin'
        self.dv.undo_commit()
        self.undo_state = 'commit'

    def undo_abort(self):
        if self.undo_state == 'begin':
            self.dv.undo_abort()
            self.undo_state = 'abort'
