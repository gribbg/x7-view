from x7.geom.drawing import DrawingContext
from .__version__ import __version__

__all__ = ['digitize', '__version__']


def digitize(draw: DrawingContext, model, model_filter=None):
    from x7.view import digi
    dc = digi.DigitizeController(draw, model, model_filter)
    dc.run()
