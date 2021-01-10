from .rect import EditHandleRect
from .shape import DigitizeShape, EditHandle
from x7.geom.typing import *
from ..digibase import *
from x7.geom.model import ElemEllipse


class DigitizeEllipse(DigitizeShape):
    def __init__(self, dd: Optional[DigiDraw], ellipse: ElemEllipse):
        super().__init__(dd, ellipse)

    def details(self):
        from ..details import DetailPoint
        return super().details() + [
            None,
            DetailPoint(self.elem, 'p1', True),
            DetailPoint(self.elem, 'p2', True),
        ]

    def edit_handle_create(self) -> List[EditHandle]:
        return super().edit_handle_create() + [EditHandleRect(self, tag) for tag in EditHandleRect.COORD_MAP.keys()]
