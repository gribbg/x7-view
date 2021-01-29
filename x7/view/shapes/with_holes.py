from .rect import EditHandleRect
from x7.geom.model import ElemWithHoles
from x7.geom.typing import *
from ..digibase import *
from .shape import *


__all__ = ['DigitizeWithHoles']


class DigitizeWithHoles(DigitizeShape):
    ELEM_TYPE = ElemWithHoles

    def __init__(self, dd: Optional[DigiDraw], holey: ElemWithHoles):
        super().__init__(dd, holey)

    def details(self) -> list:
        from ..details import Detail
        holey = cast(ElemWithHoles, self.elem)

        outside_detail = Detail(holey.outside, 'Outside', value=repr(holey)[:80]+'...')
        inside_detail = [Detail(elem, '', value=repr(elem)[:80]+'...') for elem in holey.inside]
        return super().details() + [outside_detail] + inside_detail

    def edit_handle_create(self):
        return super().edit_handle_create() + [EditHandleRect(self, tag, True) for tag in EditHandleRect.COORD_MAP.keys()]
