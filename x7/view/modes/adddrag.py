import math
from math import copysign

from x7.geom.colors import PenBrush
from x7.geom.geom import Vector
from x7.geom.typing import *
from x7.geom.model import *

from .common import ViewEvent
from ..digi import DigitizeController
from ..shapes import *
from ..digiview import CommandShapeAdd
from .add import ModeAdd


class ModeAddDrag(ModeAdd):
    """Mode for adding via a single drag operation"""

    def __init__(self, controller: DigitizeController):
        super().__init__(controller)
        self.active_start = None            # Starting point for drag operation
        # self.verbose = True

    def drag_begin(self, mp) -> DigitizeShape:
        """Start a drag operation at model space point mp"""
        raise NotImplementedError

    def drag_extend(self, start, event: ViewEvent, shape):
        """Extend a drag operation to model space point mp"""
        raise NotImplementedError

    def drag_finish(self, shape):
        """Finish a drag operation.  Mostly a NOOP"""
        pass

    def undo_commit(self):
        self.controller.view.undo_commit()
        self.active_item = None
        self.active_tag = None
        self.active_start = None
        # TODO-resume old mode?

    def undo_abort(self):
        self.controller.view.undo_abort()
        self.active_item = None
        self.active_tag = None
        self.active_start = None
        # TODO-resume old mode?

    def mouse_button1(self, event):
        if self.active_item:
            # TODO-Ignore this mouse press during a menu(?) action
            print('Weird: mouse1 during mouse2 active')
            return

        event = self.event_enrich('mouse_button1', event)
        curve = self.drag_begin(event.mp)
        curve.update()
        self.controller.view.undo_begin(CommandShapeAdd(self.controller.view, curve))
        self.active_item = curve
        self.active_start = event.mp.copy()

    def mouse_button1_motion(self, event):
        if self.active_item:
            event = self.event_enrich('mouse_button1_motion', event, 'is')
            self.drag_extend(self.active_start, event, self.active_item)
            self.active_item.update()
            self.controller.view.undo_snap()
        # print('motion: cvc.len=', len(self.controller.view.shapes), ' active=', self.active_item)

    def mouse_button1_release(self, event):
        if self.active_item:
            event = self.event_enrich('mouse_button1_release', event, 'was')
            unused(event)
            # print('Finish drag add of new thingie, reset mode(?)')
            self.drag_finish(self.active_item)
            self.undo_commit()
        # print('release: cvc.len=', len(self.controller.view.shapes), ' cvc[-1]=', self.controller.view.shapes[-1])
        self.mode_finish()

    def mouse_button2(self, event):
        # TODO-context menu during add thing
        pass

    def select_next(self, event):
        """Select next curve/control point.  Usually <Tab>"""
        # TODO-commit and reset to ModeSelect()?
        pass

    def select_prev(self, event):
        """Select prev curve/control point.  Usually <Shift-Tab>"""
        # TODO-commit and reset to ModeSelect()?
        pass

    def abort(self, event):
        """Abandon current edit.  Usually <Escape>"""
        self.undo_abort()
        self.mode_finish()

    def commit(self, event):
        """Commit current edit and exit mode.  Usually <Enter>"""
        self.drag_finish(self.active_item)
        self.undo_commit()
        self.mode_finish()

    def exit_ok(self):
        """Leaving this mode, is that OK?"""
        # print('exit_ok: ', self.active_item is None)
        # print('  ', self.controller.view.mode, self.controller.view.mode_stack)
        return self.active_item is None


def rounded_bez(angle):
    """
        From https://math.stackexchange.com/questions/1671588/b%C3%A9zier-curve-approximation-of-a-circular-arc.
        The control points of a cubic Bezier curve for approximating a circular arc with end points
        P0, P1, radius R, and angular span A:
                P0, P0+R*L*T0, P1-R*L*T1, P1
        where T0 and T1 are the unit tangent vector of the circular arc at P0 and P1
        and L = 4/3*tan(A/4)

        :param angle:
        :return:
    """
    return 4/3 * math.tan(math.radians(angle/4))


class ModeAddDragP1P2(ModeAddDrag):
    """Mode for adding P1P2 shape via a single drag operation"""

    SHAPE_NAME = None

    def __init__(self, controller: DigitizeController):
        super().__init__(controller)
        # self.verbose = True

    def drag_begin(self, mp) -> DigitizeShape:
        """Start a drag operation at model space point mp"""
        raise NotImplementedError

    def drag_extend(self, start, event: ViewEvent, shape):
        """Extend a drag operation to model space point mp"""
        shape = cast(DigitizeP1P2, shape)
        if event.shift:
            # Force to square
            mpv = event.mp - shape.elem.p1
            mid = (abs(mpv.x) + abs(mpv.y))/2
            sqv = Vector(copysign(mid, mpv.x), copysign(mid, mpv.y))
            shape.elem.p2.restore(shape.elem.p1+sqv)
        else:
            shape.elem.p2.restore(event.mp)


class ModeAddRectangle(ModeAddDragP1P2):
    """Mode for adding via a single drag operation"""

    SHAPE_NAME = 'Rect'
    HELP = 'Add rectangle: click to start, drag to second corner, Shift for square'

    def drag_begin(self, mp) -> DigitizeShape:
        """Start a drag operation at model space point mp"""
        return DigitizeRectangle(self.controller.view, ElemRectangle('rectN', PenBrush('black'), mp, mp))


class ModeAddRoundedRectangle(ModeAddDragP1P2):
    """Mode for adding via a single drag operation"""

    SHAPE_NAME = 'RRect'
    HELP = 'Add rounded rectangle: click to start, drag to second corner, Shift for square'

    def drag_begin(self, mp) -> DigitizeShape:
        """Start a drag operation at model space point mp"""
        return DigitizeRoundedRectangle(self.controller.view, ElemRectangleRounded('rectN', PenBrush('black'), mp, mp, 5))


class ModeAddEllipse(ModeAddDragP1P2):
    """Add an ellipse via a single drag operation"""

    SHAPE_NAME = 'Ellipse'
    HELP = 'Add ellipse: click to start, drag to set bounding box corner, Shift for circle'

    def drag_begin(self, mp) -> DigitizeShape:
        """Start a drag operation at model space point mp"""
        return DigitizeEllipse(self.controller.view, ElemEllipse('ellipseN', PenBrush('black'), mp, mp))
