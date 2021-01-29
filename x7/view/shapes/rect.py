from ..undo import Command
from x7.geom.typing import *
from ..digibase import *
from x7.geom.geom import *
from x7.geom.model import ElemRectangle, ElemP1P2
from .shape import *
from .shape_su import CommandSimpleUndo
from ..event import *

__all__ = ['DigitizeP1P2', 'DigitizeRectangle', 'EditHandleRect']


class DigitizeP1P2(DigitizeShape):
    def __init__(self, dd: Optional[DigiDraw], p1p2: ElemP1P2):
        super().__init__(dd, p1p2)
        self.elem = p1p2        # type fix

    def details(self):
        from ..details import DetailPoint
        return super().details() + [
            None,
            DetailPoint(self.elem, 'p1'),
            DetailPoint(self.elem, 'p2'),
        ]

    def edit_handle_create(self) -> List['EditHandle']:
        return super().edit_handle_create() + [EditHandleRect(self, tag) for tag in EditHandleRect.COORD_MAP.keys()]


class DigitizeRectangle(DigitizeP1P2):
    ELEM_TYPE = ElemRectangle

    def __init__(self, dd: Optional[DigiDraw], rect: ElemRectangle):
        super().__init__(dd, rect)
        self.elem = rect        # type fix


class EditHandleRect(EditHandle):
    """Edit handles for rectangle"""

    COORD_MAP = dict(
        top=(None, 1),
        left=(0, None),
        bot=(None, 3),
        right=(2, None),
        tl=(0, 1),
        bl=(0, 3),
        br=(2, 3),
        tr=(2, 1),
    )

    def __init__(self, shape: DigitizeShape, tag: str, use_xform=False):
        super().__init__(shape)
        self.tag = tag
        self.use_xform = use_xform
        self.shape_bbox = None
        self.shape_xform = None
        self.handle = self.shape_rect('blue', tag)
        if tag not in self.COORD_MAP:
            raise ValueError('Unknown tag: %s' % tag)

    def update_coords(self):
        """Redraw edit handle based on changes to shape"""
        bbox = self.shape.elem.bbox_int()
        xi, yi = self.COORD_MAP[self.tag]
        x = (bbox[0]+bbox[2])/2 if xi is None else bbox[xi]
        y = (bbox[1]+bbox[3])/2 if yi is None else bbox[yi]

        with self.shape.draw_space() as xform:
            x, y = xform.transform(x, y)

        rad = 5
        self.handle.update(x-rad, y-rad, x+rad, y+rad)

    def command_default(self) -> Command:
        return CommandSimpleUndo([self.shape], 'Edit Extents')

    def mouse_button1(self, event):
        super().mouse_button1(event)
        self.shape_bbox = self.shape.elem.bbox_int()
        self.shape_xform = self.shape.elem.xform.copy()

    def mouse_button1_motion(self, event):
        # event.mp is in shape.elem's external space, so map it into internal space
        if self.use_xform:
            mp = Point(*self.shape_xform.untransform(event.mp.x, event.mp.y))
        else:
            mp = Point(*self.shape.elem.xform.untransform(event.mp.x, event.mp.y))
        bbox = self.shape_bbox.copy()
        xi, yi = self.COORD_MAP[self.tag]
        if xi is not None and yi is not None and not event.state & SHIFT:
            # use original aspect ratio, otherwise SHIFT does not work
            pt = Point(bbox[xi], bbox[yi])
            other = Point(bbox[2-xi], bbox[4-yi])
            line = Line.from_pts(pt, other)
            closest = line.closest(mp)
            bbox[xi], bbox[yi] = closest.xy()
        else:
            if xi is not None:
                bbox[xi] = mp.xy()[0]
            if yi is not None:
                bbox[yi] = mp.xy()[1]
        if self.use_xform:
            xform = self.shape_xform.copy().scale_bbox(self.shape_bbox, bbox)
            print('%-8.2f, %-8.2f: %s' % (bbox.width, bbox.height, bbox))
            self.shape.elem.xform = xform
        else:
            self.shape.bbox_int_update(bbox)
        self.shape.update()

    def mouse_button1_release(self, event):
        super().mouse_button1_release(event)
        self.shape_bbox = None
        self.shape_xform = None

    def mouse_button2(self, event):
        """Handle mouse_button2, usually via self.context_menu()"""
        self.context_menu(event, [('what?', None), None, ('bye', None)])
