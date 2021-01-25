import tkinter as tk
from abc import ABC

from x7.geom.typing import *
from x7.geom.geom import Point

import x7.view.event
from ..digi import DigitizeController
from ..digibase import Mode
from ..shapes import DigitizeShape

__all__ = ['tag_area', 'canvas_find', 'canvas_find_multiple', 'ViewEvent', 'ModeCommon']


def tag_area(canvas, tag):
    """Compute the bbox area of a single item on the canvas"""
    # TODO-different areas based on type of shape
    xl, yl, xh, yh = canvas.bbox(tag)
    return (xh-xl) * (yh-yl)


def canvas_find_multiple(view, cx, cy) -> List[Tuple]:
    """Find multiple objects near cursor, return sorted list of (area, tk_id)"""
    debug = False
    if debug:
        shown = set()
        for rad in [0, 1, 2, 4, 8]:
            found = view.canvas.find_overlapping(cx - rad, cy - rad, cx + rad, cy + rad)
            print('rad: %d  found: %s' % (rad, found))
            for f in found:
                if f not in shown:
                    shown.add(f)
                    print('  %d: %s %s %s' % (f, tag_area(view.canvas, f), view.canvas.bbox(f), view.ui_map.obj(f)))
    for rad in range(8):
        found = view.canvas.find_overlapping(cx - rad, cy - rad, cx + rad, cy + rad)
        found = sorted((tag_area(view.canvas, tag), tag) for tag in found if view.ui_map.obj(tag))
        if found:
            if debug:
                print('-->', found)
            return found
    return []


def canvas_find(view, cx, cy) -> Tuple[Optional[object], Optional[str]]:
    """Find object near cursor, return object & tag"""
    found = canvas_find_multiple(view, cx, cy)
    if found:
        obj, tag = view.ui_map.obj(found[0][1])
        if obj not in view.shapes:
            if isinstance(obj, DigitizeShape):
                print('Internal error: shape on canvas, but not in view.shapes: %s' % obj)
        return obj, tag
    else:
        return None, None


class ViewEvent(tk.Event):
    """tk.Event, with typing and some x7-view specific values"""

    serial: int
    num: Union[int, str]        # str:?? implies not set
    focus: bool
    type_test: Union[int, str]
    height: Union[int, str]
    width: Union[int, str]
    keycode: str
    state: Union[int, str]
    time: Union[int, str]
    x: Union[int, str]
    y: Union[int, str]
    x_root: Union[int, str]
    y_root: Union[int, str]
    char: str
    send_event: bool
    keysym: str
    keysym_num: str
    type: tk.EventType
    widget: tk.Misc
    delta: int

    cx: float                           # ev.x converted to canvas space
    cy: float                           # ev.y converted to canvas space
    mp: Point                           # (cx, cy) converted to modeling space
    item: Union[DigitizeShape, Any]     # Really anything that has mouse_button callbacks
    tag: str                            # .tag from .item graphical element
    shift: bool                         # Shift key pressed
    control: bool                       # Control key pressed

    def __init__(self, ev: tk.Event, cx=0.0, cy=0.0, mp=Point(0, 0), item=None, tag=''):
        self.__dict__.update(ev.__dict__)
        self.cx = cx
        self.cy = cy
        self.mp = mp
        self.item = item
        self.tag = tag
        if isinstance(self.state, int):
            self.shift = True if self.state & x7.view.event.SHIFT else False
            self.control = True if self.state & x7.view.event.CONTROL else False
        else:
            # Visibility events have strings for .state, not modifier keys
            self.shift = self.control = False

    def __str__(self):
        return super().__str__() + ' @ (%d, %d) -> %s' % (self.cx, self.cy, self.mp.round(2))


class ModeCommon(Mode, ABC):
    """A few more common behaviors for Modes"""
    def __init__(self, controller: DigitizeController):
        self.controller = controller
        self.active_item: Union[DigitizeShape, Any] = None       # Really anything that has mouse_button callbacks
        self.active_tag: Optional[str] = None
        self.verbose = False

    def event_enrich(self, name, tk_event, verb=None, find=False) -> ViewEvent:
        """
            Enrich an event by adding .cx, .cy, .mx, .my
            Find matching item & tag if not self.active_item
            Add .tag
        """
        canvas = self.controller.view.canvas
        assert tk_event.widget == canvas

        cx, cy = canvas.canvasx(tk_event.x), canvas.canvasy(tk_event.y)
        mp = Point(*self.controller.view.draw.matrix.untransform(cx, cy))
        event = ViewEvent(tk_event, cx, cy, mp)

        if self.verbose:
            print('%s(%s) -> (%d, %d) -> %s  .state=%s' % (name, tk_event, event.cx, event.cy, event.mp, event.state))
            print('%s: %s' % (name, event))
            if verb:
                print('  active %s %s.%s' % (verb, self.active_item.__class__.__name__, self.active_tag))
        if find or not self.active_item:
            item, tag = canvas_find(self.controller.view, event.cx, event.cy)
            event.item = item
            event.tag = tag
            if not self.active_item:
                self.active_item = item
                self.active_tag = tag
            if self.verbose and item:
                print('--> ', tag, '@', item)
        else:
            event.item = self.active_item
            event.tag = self.active_tag
        return event
