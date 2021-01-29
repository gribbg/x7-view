from .rect import DigitizeP1P2
from x7.geom.typing import *
from ..digibase import *
from x7.geom.model import ElemEllipse


class DigitizeEllipse(DigitizeP1P2):
    ELEM_TYPE = ElemEllipse

    def __init__(self, dd: Optional[DigiDraw], ellipse: ElemEllipse):
        super().__init__(dd, ellipse)
        self.elem = ellipse        # type fix
