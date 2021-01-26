"""Base classes for digi MVC framework"""


from abc import ABC, abstractmethod
import tkinter as tk

from x7.geom.drawing import DrawingContext
from x7.geom.typing import *
from x7.lib.bidict import BidirectionalUniqueDictionary
from .undo import *


__all__ = ['Mode', 'Callbacks', 'CallbacksAny', 'DigiDraw']
# TODO-report this bug to PyCharm.  Without cast, PyCharm does not think ModeInfo is callable
ModeInfo = cast(type, NamedTuple('ModeInfo', klass=type, concrete=bool, shape=str))


class Mode(ABC):
    """Mode classes control top-level interaction"""

    MODE_TAG = 'None'           # .value of indicators for this mode (buttons, ...)
    CURSOR = 'arrow'
    HELP = 'displayed in status bar'

    @classmethod
    def all_subclasses(cls):
        """Return a list of all non subclasses"""
        yield cls
        for klass in cls.__subclasses__():
            klass = cast(Mode, klass)
            yield from klass.all_subclasses()

    @classmethod
    def all_modes(cls):
        import inspect
        for klass in Mode.all_subclasses():     # Start from top to get all subclasses
            yield ModeInfo(klass, inspect.isabstract(klass), getattr(klass, 'SHAPE_NAME', None))

    @classmethod
    def all_shapes(cls):
        return dict((shape, klass) for klass, concrete, shape in cls.all_modes() if shape)

    def mouse_motion(self, event):
        pass

    @abstractmethod
    def mouse_button1(self, event):
        ...

    @abstractmethod
    def mouse_button1_motion(self, event):
        ...

    @abstractmethod
    def mouse_button1_release(self, event):
        ...

    @abstractmethod
    def mouse_button2(self, event):
        ...

    @abstractmethod
    def select_next(self, event):
        """Select next curve/control point.  Usually <Tab>"""
        ...

    @abstractmethod
    def select_prev(self, event):
        """Select prev curve/control point.  Usually <Shift-Tab>"""
        ...

    @abstractmethod
    def abort(self, event):
        """Abandon current edit.  Usually <Escape>"""
        ...

    @abstractmethod
    def commit(self, event):
        """Commit current edit and exit mode.  Usually <Enter>"""
        ...

    @abstractmethod
    def delete(self, event):
        """Delete something (selected object(s), last control point during curve entry, ...)"""
        ...

    def do_cut(self, event, save_to_buffer=True):
        """Perform cut of cut/copy/paste.  Generally a NOOP outside of Select mode."""
        pass

    def do_copy(self, event):
        """Perform copy of cut/copy/paste.  Generally a NOOP outside of Select mode."""
        pass

    def do_paste(self, event):
        """Perform paste of cut/copy/paste.  Generally a NOOP outside of Select mode."""
        pass

    def exit_ok(self):
        """Leaving this mode, is that OK?"""
        unused(self)
        return True


class Callbacks(object):
    """Encapsulate menu/keyboard callbacks to handle common behavior"""
    def __init__(self, trace=('callback', 'binder'), error_on_missing=True):
        allowed = ('callback', 'binder')
        self.trace = set(trace)
        for t in self.trace:
            if t not in allowed:
                raise ValueError('Callbacks: unknown trace flag: %r' % t)
        self.error_on_missing = error_on_missing
        self.shape_var: Optional[tk.StringVar] = None
        self.shape_map = dict()

    def _common(self, kind, event, name, tag):
        """Lookup callback and trace as desired"""
        cb = getattr(self, name, None)
        if kind in self.trace or not cb:
            print('%s(%s, %s%s, %s)' % (kind, event, name, '' if cb else '[not found]', tag))
        if not cb and self.error_on_missing:
            raise ValueError('Unknown callback name: %s' % name)
        return cb

    def do_callback(self, event, name, tag=None):
        cb = self._common('callback', event, name, tag)
        return cb(event, tag) if cb else None

    def binder(self, name, tag=None):
        """Construct the callback(event=None) function to hand to tk.bind()"""
        self._common('binder', None, name, tag)
        return lambda event=None: self.do_callback(event, name, tag)


class CallbacksAny(Callbacks):
    """Allow any callback as this is a debug-only class"""
    def __init__(self, trace=('callback', 'binder')):
        super().__init__(trace, error_on_missing=False)


class UiMap(object):
    """Bi-directional mapping between tk canvas ids: int and view objects: Tuple[view_object, sub-elem]"""
    def __init__(self):
        self.map = BidirectionalUniqueDictionary()

    def tk_id(self, elem, tag):
        return self.map.inverse.get((elem, tag))

    def obj(self, tk_id) -> Tuple[object, str]:
        return self.map.get(tk_id)

    def register(self, tk_id, elem, tag):
        self.map[tk_id] = (elem, tag)

    def unregister(self, tk_id):
        del self.map[tk_id]


class DigiDraw(object):
    """Abstract object to encapsulate DigiView's drawing interface"""

    def __init__(self, draw: DrawingContext, master: tk.Tk):
        from .shapes import DigitizeShapes

        self.draw = draw
        self.master = master
        self.canvas: Optional[tk.Canvas] = None
        self._ui_map = UiMap()
        self.undo_stack = CommandStack()
        self.undo_current_command: Optional[Command] = None
        self.zoom = 1.0
        self.selection: DigitizeShapes = []

    @property
    def ui_map(self):
        return self._ui_map

    def undo_begin(self, command: Command):
        ...

    def undo_begin_commit(self, command: Command):
        ...

    def undo_snap(self):
        ...

    def undo_commit(self):
        ...

    def undo_abort(self):
        ...

    def select(self, items, add=False):
        ...

    def status_set(self, message: str):
        ...

    def status_clear(self):
        ...
