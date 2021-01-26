from x7.geom.geom import Point, BBox
from ..platform import PCFG
from ..digi import DigitizeController
from .common import ModeCommon


class ModeZoom(ModeCommon):
    """Zoom mode: zoom to a box"""

    MODE_TAG = 'Zoom'
    CURSOR = PCFG.cursor_zoom
    HELP = 'Zoom: click and drag to zoom to box'

    def __init__(self, controller: DigitizeController):
        super().__init__(controller)
        self.start = None
        self.tk_id = None

    def drag_begin(self, event):
        canvas = self.controller.view.canvas
        self.start = Point(canvas.canvasx(event.x), canvas.canvasy(event.y))
        print('drag_begin: ', event, ' ->', self.start)
        coords = tuple(self.start) * 2
        self.tk_id = canvas.create_rectangle(*coords)

    def mouse_button1(self, event):
        assert self.active_item is None
        self.drag_begin(event)

    def mouse_button1_motion(self, event):
        canvas = self.controller.view.canvas
        event.cx, event.cy = canvas.canvasx(event.x), canvas.canvasy(event.y)
        coords = tuple(self.start) + (event.cx, event.cy)
        # print('  coords are ', coords)
        canvas.coords(self.tk_id, *coords)

    def mouse_button1_release(self, event):
        canvas = self.controller.view.canvas
        event.cx, event.cy = canvas.canvasx(event.x), canvas.canvasy(event.y)
        coords = tuple(self.start) + (event.cx, event.cy)
        self.controller.view.zoom_fit(BBox(*coords))
        # print('Final coords are ', coords)
        self.abort(event)

    def mouse_button2(self, event):
        return

    def select_next(self, event):
        """Select next curve/control point.  Usually <Tab>"""
        return

    def select_prev(self, event):
        """Select prev curve/control point.  Usually <Shift-Tab>"""
        return

    def abort(self, event):
        """Abandon current edit.  Usually <Escape>"""

        if self.tk_id is not None:
            self.controller.view.canvas.delete(self.tk_id)
            self.tk_id = None
        self.controller.view.mode_reset()
        # TODO-eat events until mouse-up?

    def commit(self, event):
        pass

    def delete(self, event):
        pass
