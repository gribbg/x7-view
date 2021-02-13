"""
    Edit details of a shape
"""
import re
import tkinter as tk
from tkinter import ttk, simpledialog
from typing import Generator

from x7.geom.geom import Point, Vector
from x7.geom.typing import *
from x7.lib.iters import t_range

from .digiview import DigitizeView
from .platform import PCFG
from .shapes import DigitizeShape
from .shapes.shape_su import CommandSimpleUndo
from .widgets import ValidatingEntry


__all__ = ['Detail', 'DetailBool', 'DetailInt', 'DetailFloat', 'DetailPoint', 'DetailRepr', 'DetailDialog']

DetailAddress = Union[int, str]


class Detail(object):
    """A single detail to be edited"""
    VERBOSE = False

    def __init__(self, target, addr: DetailAddress, ro=False, value=None, name: Optional[str] = None):
        self.target = target
        self.addr = addr
        if name is None:
            name = addr if isinstance(addr, str) else '[%s]' % addr
        self.name = name
        self.ro = ro
        self.ve: Optional[ValidatingEntry] = None
        self.orig_value = value if value is not None else self.get_val()

    def elems(self, frame) -> tuple:        # label, entry field(s)
        self.ve = ValidatingEntry(frame, label=self.name, value=str(self.orig_value), validator=self.validate, read_only=self.ro)
        return self.ve.label, self.ve.entry

    @property
    def addr_text(self):
        """Text version of address"""
        if isinstance(self.addr, str):
            return '.%s' % self.addr
        elif isinstance(self.addr, int):
            return '%s[%s]' % (self.name, self.addr)
        else:
            raise ValueError('Unknown addr type: %s' % type(self.target).__name__)

    def get_val(self):
        """Get value based on address"""
        if isinstance(self.addr, str):
            return getattr(self.target, self.addr)
        elif isinstance(self.addr, int):
            return self.target[self.addr]
        else:
            raise ValueError('Unknown addr type: %s' % type(self.target).__name__)

    def set_val(self, val):
        """Set value based on address"""
        if isinstance(self.addr, str):
            setattr(self.target, self.addr, val)
        elif isinstance(self.addr, int):
            self.target[self.addr] = val
        else:
            raise ValueError('Unknown addr type: %s' % type(self.target).__name__)

    @staticmethod
    def parse(val: str):
        return val

    def validate(self, ve: ValidatingEntry, value: str):
        """Return True if this entry is valid, error string otherwise"""
        unused(ve)

        if self.ro:
            return True
        try:
            self.parse(value)
        except ValueError as err:
            return str(err)
        return True

    def get(self):
        return self.parse(self.ve.get())

    def update(self):
        if not self.ro:
            cur_val = self.get_val()
            new_val = self.get()
            if self.VERBOSE:
                cur_val_displayed = cur_val if isinstance(cur_val, str) else repr(cur_val)
                msg = '[Same]' if cur_val == new_val else ('[was %s]' % cur_val_displayed)
                print('update %s -> %s %s' % (self.addr_text, new_val, msg))
            self.set_val(new_val)

    def animator(self, steps=20) -> Union[None, Generator]:
        if not self.ro:
            cur_val = self.get_val()
            new_val = self.get()
            if cur_val != new_val:
                if isinstance(cur_val, (int, float)):
                    def anim_func():
                        for t in t_range(steps, t_start=cur_val, t_end=new_val):
                            self.set_val(t)
                            yield t
                    return anim_func()
                elif isinstance(cur_val, (Vector, Point)) and isinstance(new_val, (Vector, Point)):
                    v = new_val - cur_val

                    def anim_func():
                        for t in t_range(steps):
                            np = cur_val + t * v
                            self.set_val(np)
                            yield np
                    return anim_func()
                else:
                    raise ValueError("Can't animate %r to %r" % (cur_val, new_val))
        return None


class DetailBool(Detail):
    """Detail for bool"""
    def __init__(self, target, addr: DetailAddress, ro=False, value=None, name: Optional[str] = None):
        super().__init__(target, addr, ro=ro, value=value, name=name)

    @classmethod
    def parse(cls, val: str):
        val = val.strip().lower()
        if val in ('t', 'tr', 'tru', 'true'):
            return True
        # noinspection SpellCheckingInspection
        if val in ('f', 'fa', 'fal', 'fals', 'false'):
            return False
        raise ValueError('Expected bool')


class DetailPoint(Detail):
    """Detail for Point()"""
    pattern = re.compile(r'^\s*\((.*),(.*)\)\s*$')

    def __init__(self, target, addr: DetailAddress, ro=False, value=None, name: Optional[str] = None):
        super().__init__(target, addr, ro=ro, value=value, name=name)
        self.orig_value = self.orig_value.round(4)

    @classmethod
    def parse(cls, val: str):
        if match := cls.pattern.match(val):
            x, y = match.groups()
            try:
                return Point(float(x), float(y))
            except ValueError:
                pass

        raise ValueError('expected point: (x: float, y: float)')


class DetailFloat(Detail):
    """Detail for float"""

    def __init__(self, target, addr: DetailAddress, ro=False, value=None, name: Optional[str] = None):
        super().__init__(target, addr, ro=ro, value=value, name=name)
        self.orig_value = round(self.orig_value, 4)

    @staticmethod
    def parse(val: str):
        return float(val)


class DetailInt(Detail):
    """Detail for int"""

    def __init__(self, target, addr: DetailAddress, ro=False, value=None, name: Optional[str] = None):
        super().__init__(target, addr, ro=ro, value=value, name=name)

    @staticmethod
    def parse(val: str):
        return int(val)


class DetailRepr(Detail):
    """Detail for type that can be repr() / eval()"""

    def __init__(self, target, addr: DetailAddress, ro=False, value=None, name: Optional[str] = None, ctx=None):
        super().__init__(target, addr, ro=ro, value=value, name=name)
        self.orig_type = type(self.orig_value)
        self.orig_value = repr(self.orig_value)
        self.ctx: dict = ctx or {}

    def parse(self, val: str):
        try:
            parsed = eval(val, self.ctx, {})
        except Exception as err:
            raise ValueError('Invalid %s: %s' % (self.orig_type.__name__, err))
        if not isinstance(parsed, self.orig_type):
            raise ValueError('Expected a %s' % self.orig_type.__name__)
        return parsed


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
        w = ttk.Button(box, text="Apply", command=self.apply_button)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = ttk.Button(box, text="Animate", command=self.animate_button)
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
                if label:
                    label.grid(row=row, column=0, padx=5, pady=5, sticky='w')
                entry.grid(row=row, column=1, padx=5, sticky='we')
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

    def apply_button(self, _event=None):
        """Just apply, but don't commit"""
        for d in self.details:
            if d:
                d.update()
        self.shape.update()

    def animate_button(self, _event=None):
        """Linear animation to new values"""
        steps = 1000
        animators = []
        for d in self.details:
            if d:
                a = d.animator(steps=steps)
                if a:
                    animators.append(a)
        if animators:
            widths = [0] * len(animators)

            def animate_update():
                try:
                    vals = [next(anim) for anim in animators]
                    vals = [str(round(v, 2)) for v in vals]
                    for idx, s in enumerate(vals):
                        if len(s) > widths[idx]:
                            widths[idx] = len(s)
                    msg = ' '.join('%-*s' % (w, s) for w, s in zip(widths, vals))
                    self.dv.status_set(msg)
                    self.shape.update()
                    self.master.after(10, animate_update)
                except StopIteration:
                    self.dv.status_clear()
                    # TODO-reset back to current values for this item (weird undo stack interaction)
            animate_update()

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
