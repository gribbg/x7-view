from .rect import EditHandleRect
from x7.geom.colors import PenBrush
from x7.geom.model import Group
from x7.geom.typing import *
from ..digibase import *
from .shape import *


class DigitizeGroup(DigitizeShape):
    ELEM_TYPE = Group
    bbox_show = True
    bbox_penbrush = PenBrush(('grey', 1))   # dash=[2, 6]

    def __init__(self, dd: Optional[DigiDraw], group: Group):
        # name, shapes: DigitizeShapes, mat: Optional[Transform] = None):
        super().__init__(dd, group)
        self.elem = group       # type fix

    @property
    def group(self) -> Group:
        return cast(Group, self.elem)

    def details(self) -> list:
        from ..details import Detail

        shape_detail = [Detail(self, 'Shapes', value=repr(self.elem)[:80]+'...')]
        shape_detail += [Detail(self, '', value=repr(s)[:80]+'...') for s in self.elem.elems.values()]
        return super().details() + [Detail(self, 'xform', value=repr(self.elem.xform))] + shape_detail

    def edit_handle_create(self):
        return super().edit_handle_create() + [EditHandleRect(self, tag, True) for tag in EditHandleRect.COORD_MAP.keys()]
