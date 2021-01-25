from x7.geom.typing import unused

from ..digi import DigitizeController
from .common import ModeCommon


class ModeAdd(ModeCommon):
    """Base class for add modes"""

    MODE_TAG = 'Add'

    # Add styles:
    #   clip art, component - single click
    #   ellipse & polygon - single click and drag to scale/shape
    #   freehand - click and drag to draw points
    #   curve (choose open or closed by type of curve selected)
    #       - click and drag for each control point
    #       - Enter or Escape to accept curve
    #       - click on starting point to accept and close curve
    #       - ctrl-click for sharp corner
    # Finish:
    #    When complete, call mode_finish to pop back to select mode
    # Consider:
    #    Next/Prev illegal during drag, commits curve?
    #    TODO-classify commands Navigation, Selection, FileOperation, ...  Only Navigation is legal during ModeAdd

    def __init__(self, controller: DigitizeController):
        super().__init__(controller)

    def mode_finish(self):
        self.controller.view.mode_reset()

    def mouse_button1(self, event):
        if self.active_item:
            # TODO-Ignore this mouse press during a menu(?) action
            print('Weird: mouse1 during mouse2 active')
            return

        event = self.event_enrich('mouse_button1', event)
        unused(event)
        print('Begin add of new thingie')

    def mouse_button1_motion(self, event):
        event = self.event_enrich('mouse_button1_motion', event, 'is')
        unused(event)
        print('Continue add of new thingie')

    def mouse_button1_release(self, event):
        event = self.event_enrich('mouse_button1_release', event, 'was')
        print('Finish(?) add of new thingie')
        if hasattr(self.active_item, 'mouse_button1_release'):
            self.active_item.mouse_button1_release(event)
        self.active_item = None
        self.active_tag = None

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
        print('Abort adding current thingie')

    def commit(self, event):
        """Commit current edit and exit mode.  Usually <Enter>"""
        print('Finish adding current thingie')
        return True         # Return True to allow mode to exit

    def delete(self, event):
        print('delete(%s)' % event)
