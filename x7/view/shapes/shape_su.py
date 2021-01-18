from .shape import DigitizeShape
from ..undo import Command
from x7.geom.typing import *

__all__ = ['CommandSimpleUndo']


class CommandSimpleUndo(Command):
    """Undo command pattern that uses su_save() and su_restore()"""
    def __init__(self, shapes: List[DigitizeShape], desc: str = ''):
        super().__init__()
        self.shapes = shapes
        self.dd = shapes[0].dd
        self.old_values = [shape.su_save() for shape in self.shapes]
        self.new_values = [shape.su_save() for shape in self.shapes]
        self.desc = desc or 'Edit %d shapes' % len(self.shapes)

    def description(self):
        return self.desc

    def snap(self):
        self.new_values = [shape.su_save() for shape in self.shapes]

    def do(self):
        for shape, values in zip(self.shapes, self.new_values):
            shape.su_restore(**values)
            shape.update()
        self.dd.select(self.shapes)

    def undo(self):
        for shape, values in zip(self.shapes, self.old_values):
            shape.su_restore(**values)
            shape.update()
        self.dd.select(self.shapes)
