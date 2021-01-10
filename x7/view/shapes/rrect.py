from .rect import *
from x7.geom.model import ElemRectangleRounded


class DigitizeRoundedRectangle(DigitizeShape):
    def __init__(self, dd: Optional[DigiDraw], rrect: ElemRectangleRounded):
        super().__init__(dd, rrect)

    def details(self):
        from ..details import DetailFloat, DetailPoint
        return super().details() + [
            None,
            DetailPoint(self.elem, 'p1'),
            DetailPoint(self.elem, 'p2'),
            DetailFloat(self.elem, 'radius'),
        ]

    def edit_handle_create(self) -> List[EditHandle]:
        return (
            super().edit_handle_create() +
            [EditHandleRect(self, tag) for tag in EditHandleRect.COORD_MAP.keys()] +
            [EditHandleRadius(self)]
        )

    def update_radius(self, radius: float):
        self.elem.radius = radius
        self.update()


class EditHandleRadius(EditHandle):
    """Edit handle for radius of rounded rectangle"""

    def __init__(self, shape: DigitizeRoundedRectangle):
        super().__init__(shape)
        self.handle = self.shape_oval('yellow', 'radius')

    def update_coords(self):
        """Redraw edit handle based on changes to shape"""
        x1, y1, x2, y2 = self.shape.elem.bbox_int()
        radius = min(abs(x1-x2)/2, self.shape.elem.radius)
        x = min(x1, x2) + radius
        y = max(y1, y2)
        with self.shape.draw_space() as xform:
            x, y = xform.transform(x, y)
        rad = 4
        self.handle.update(x-rad, y-rad, x+rad, y+rad)

    def command_default(self) -> Command:
        return CommandSimpleUndo([self.shape], 'Edit Radius')

    def mouse_button1_motion(self, event):
        mp = Point(*self.shape.elem.xform.untransform(event.mp.x, event.mp.y))
        bbox = self.shape.elem.bbox_int()
        top_left_x = min(bbox[0], bbox[2])
        radius = max(0, mp.x - top_left_x)
        self.shape.update_radius(radius)

    def mouse_button2(self, event):
        """Handle mouse_button2, usually via self.context_menu()"""
        self.context_menu(event, [('what?', None), None, ('bye', None)])
