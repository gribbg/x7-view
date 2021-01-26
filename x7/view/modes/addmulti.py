from typing import cast
from x7.geom.colors import PenBrush
from x7.geom.model import *
from x7.geom.geom import *
from ..digi import DigitizeController
from ..shapes import *
from ..digiview import CommandShapeAdd
from .add import ModeAdd


class ModeAddMultiClick(ModeAdd):
    """Mode for adding via a multiple click/drag operations"""

    # Click - set first point
    # Repeat:
    #    Motion - moving to next point
    #    Click - set next point
    # Terminate:
    #    Click on original point to complete and close
    #    Enter or Escape to terminate and leave open

    def __init__(self, controller: DigitizeController):
        super().__init__(controller)
        # self.active_start = None              # Starting point for drag operation
        # self.verbose = True
        self.mode_finish_on_release = False     # Finish mode on release of mouse button1?

    def multi_begin(self, mp: Point) -> DigitizeCurve:
        """Start a multi-click add at model space point mp"""
        raise NotImplementedError

    def multi_drag(self, curve: DigitizeCurve, mp: Point):
        """Drag last point (usually control-point move)"""
        raise NotImplementedError

    def multi_drag_finish(self, curve: DigitizeCurve, mp: Point):
        """Drag finished (mouse-release)"""
        raise NotImplementedError

    def multi_move(self, curve: DigitizeCurve, mp: Point):
        """Animate curve while moving to next point"""
        raise NotImplementedError

    def multi_click(self, curve: DigitizeCurve, mp: Point):
        """Add mp to curve"""
        raise NotImplementedError

    def multi_finish(self, curve: DigitizeCurve, keep_last=False):
        """Finish a multi-click add"""
        raise NotImplementedError

    def undo_commit(self):
        self.controller.view.undo_commit()
        self.active_item = None
        self.active_tag = None

    def undo_abort(self):
        self.controller.view.undo_abort()
        self.active_item = None
        self.active_tag = None

    def mouse_motion(self, event):
        # Mouse moving, but no button pressed
        if self.active_item:
            event = self.event_enrich('mouse_motion', event, 'is')
            self.multi_move(self.active_item, event.mp)
            self.active_item.update()
            self.controller.view.undo_snap()
        # print('motion: cvc.len=', len(self.controller.view.shapes), ' active=', self.active_item)

    def mouse_button1(self, event):
        event = self.event_enrich('mouse_button1', event, find=True)
        if self.active_item:
            assert isinstance(self.active_item, DigitizeCurve)
            curve = cast(DigitizeCurve, self.active_item)
            if curve.elem.control_points[0] == event.item and event.tag == 'c':
                # Clicked on starting control point
                self.multi_finish(self.active_item)
                self.active_item.update()
                self.undo_commit()
                self.mode_finish_on_release = True
            else:
                # TODO-allow editing of other control points of this curve?
                self.multi_click(self.active_item, event.mp)
        else:
            curve = self.multi_begin(event.mp)
            self.controller.view.undo_begin(CommandShapeAdd(self.controller.view, curve))
            self.controller.view.status_set('Click-drag to set curvature. Mouse-2 or Enter to accept.  ESC to abort')
            self.active_item = curve
        if self.active_item:
            self.active_item.update()

    def mouse_button1_motion(self, event):
        if self.active_item:
            event = self.event_enrich('mouse_button1_motion', event, 'is')
            self.multi_drag(self.active_item, event.mp)
            self.controller.view.undo_snap()
            self.active_item.update()
        # print('motion: cvc.len=', len(self.controller.view.shapes), ' active=', self.active_item)

    def mouse_button1_release(self, event):
        if self.mode_finish_on_release:
            self.mode_finish()
        elif self.active_item:
            event = self.event_enrich('mouse_button1_release', event, 'was')
            self.multi_drag(self.active_item, event.mp)
            self.multi_drag_finish(self.active_item, event.mp)
            self.active_item.update()

    def mouse_button2(self, event):
        # TODO-context menu during add thing
        #  Closed, Open, Finish
        self.commit(event)
        # self.multi_finish(self.active_item)
        # self.undo_commit()

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
        self.multi_finish(self.active_item)
        self.undo_commit()
        self.mode_finish()

    def exit_ok(self):
        """Leaving this mode, is that OK?"""
        # print('exit_ok: ', self.active_item is None)
        # print('  ', self.controller.view.mode, self.controller.view.mode_stack)
        return self.active_item is None


class ModeAddCurve(ModeAddMultiClick):
    SHAPE_NAME = 'Curve'
    HELP = 'Add curve: click for points, drag to set curvature, right-click to end'

    def multi_begin(self, mp: Point) -> DigitizeCurve:
        """Start a multi-click add at model space point mp"""
        curve = ElemCurve('curveN', PenBrush('black'), [ControlPoint(mp, Vector(), Vector(), 'smooth')], closed=True)
        dc = DigitizeCurve(self.controller.view, curve)
        dc.edit_handle_show()
        return dc

    def multi_drag(self, curve: DigitizeCurve, mp: Point):
        """Drag last point (usually control-point handle move)"""
        dcp = curve.elem.control_points[-1]
        dcp.dr = mp - dcp.c
        dcp.dl = -dcp.dr

    def multi_drag_finish(self, curve: DigitizeCurve, mp: Point):
        """Drag finished (mouse-release)"""
        curve.elem.control_points.append(ControlPoint(mp, Vector(), Vector(), 'smooth'))
        self.multi_move(curve, mp)      # Set DL & DR

    def multi_move(self, curve: DigitizeCurve, mp: Point):
        """Animate curve while moving to next point"""
        cp = curve.elem.control_points[-1]
        cp.c.set(mp)
        cps = curve.elem.control_points[0]
        if len(curve.elem.control_points) == 2:
            # Set DL & DR perpendicular to vector back to start
            vs = (mp-cps.c).normal()*0.2
            if vs.dot(cps.dr) > 0:
                vs = -vs
            cp.dl.set(-vs)
            cp.dr.set(vs)
        else:
            vs = (cps.c-curve.elem.control_points[-2].c)*0.2
            cp.dl.set(-vs)
            cp.dr.set(vs)

    def multi_click(self, curve: DigitizeCurve, mp: Point):
        """Add mp to curve"""
        curve.elem.control_points[-1].c.set(mp)

    def multi_finish(self, curve: DigitizeCurve, keep_last=False):
        """Finish a multi-click add"""
        if not keep_last:
            assert len(curve.elem.control_points) > 1
            curve.elem.control_points.pop()
            curve.update()
