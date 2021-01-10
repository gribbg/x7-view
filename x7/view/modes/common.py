from abc import ABC

from x7.geom.typing import *
from x7.geom.geom import Point
from ..digi import DigitizeController
from ..digibase import Mode
from ..shapes import DigitizeShape


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


class ModeCommon(Mode, ABC):
    """A few more common behaviors for Modes"""
    def __init__(self, controller: DigitizeController):
        self.controller = controller
        self.active_item: Union[DigitizeShape, Any] = None       # Really anything that has mouse_button callbacks
        self.active_tag: Optional[str] = None
        self.verbose = False

    def event_enrich(self, name, event, verb=None, find=False):
        """
            Enrich an event by adding .cx, .cy, .mx, .my
            Find matching item & tag if not self.active_item
            Add .tag
        """
        canvas = self.controller.view.canvas
        assert event.widget == canvas

        event.cx, event.cy = canvas.canvasx(event.x), canvas.canvasy(event.y)
        event.mp = Point(*self.controller.view.draw.matrix.untransform(event.cx, event.cy))

        if self.verbose:
            print('%s(%s) -> (%d, %d) -> %s  .state=%s' % (name, event, event.cx, event.cy, event.mp, event.state))
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
