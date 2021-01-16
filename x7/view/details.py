"""
    Edit details of a shape
"""

import tkinter as tk
from tkinter import ttk, simpledialog

from x7.geom.typing import *
from .digiview import DigitizeView
from .platform import PCFG
from .shapes import DigitizeShape
from .shapes.shape_su import CommandSimpleUndo
from .widgets import ValidatingEntry


__all__ = ['Detail', 'DetailFloat', 'DetailPoint', 'DetailDialog']


class Detail(object):
    """A single detail to be edited"""

    def __init__(self, target, attr: str, ro=False, value=None):
        self.target = target
        self.attr = attr
        self.ro = ro or value is not None
        self.ve: Optional[ValidatingEntry] = None
        self.orig_value = value if value is not None else getattr(target, attr)

    def elems(self, frame) -> tuple:        # label, entry field(s)
        self.ve = ValidatingEntry(frame, label=self.attr, value=str(self.orig_value), validator=self.validate, read_only=self.ro)
        return self.ve.label, self.ve.entry

    def validate(self, ve: ValidatingEntry, value: Any):
        """Return True if this entry is valid, error string otherwise"""
        if self.ro or value != 'ERROR':
            return True
        return "Error here"

    def update(self):
        if not self.ro:
            cur_val = getattr(self.target, self.attr)
            new_val = self.ve.get()
            print('update %s -> %s %s' % (self.attr, new_val, '[Same]' if cur_val == new_val else ('[was %s]' % cur_val)))
            setattr(self.target, self.attr, new_val)


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

    def buttonbox(self):
        """Add standard button box using ttk elements"""

        box = ttk.Frame(self)

        w = ttk.Button(box, text="OK", command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = ttk.Button(box, text="Cancel", command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    def body(self, master: tk.Frame):
        master.pack(expand=1, fill=tk.BOTH)
        master.configure(background=PCFG.frame_background)
        master.master.configure(background=PCFG.frame_background)
        frame = ttk.Frame(master)
        frame.pack(expand=1, fill=tk.BOTH)

        for row, detail in enumerate(self.details):
            if detail:
                label, entry = detail.elems(frame)
                label.grid(row=row, column=0, padx=5, pady=5, sticky=tk.W)
                entry.grid(row=row, column=1, padx=5, sticky=tk.W+tk.E)
            else:
                sep = ttk.Separator(frame)
                sep.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky='we')

        for dt in self.details:
            if not dt.ro:
                return dt.ve.entry
        return self.details[0].ve.entry

    def validate(self):
        valid = True
        for d in self.details:
            if not d:
                continue
            validation = d.validate(d.ve, d.ve.get())
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
