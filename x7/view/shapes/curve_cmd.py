from x7.view.undo import Command, CommandEditCP
from . import DigitizeShape
from .digicurve import DigitizeCurve
from x7.geom.model import ControlPoint


class CommandCpEdit(Command):
    """Command pattern to memoize changes to a ControlPoint"""
    def __init__(self, shape: DigitizeShape, cp: ControlPoint):
        super().__init__()
        self.shape = shape
        self.cp_edit = CommandEditCP(cp)

    def description(self):
        return 'Edit Control Point'

    def snap(self):
        self.cp_edit.snap()

    def do(self):
        self.cp_edit.do()
        self.shape.update()

    def undo(self):
        self.cp_edit.undo()
        self.shape.update()


class CommandCurveEditProperty(Command):
    """Command pattern to memoize property changes to a DigitizeCurve"""

    def __init__(self, dcc: DigitizeCurve, **props):
        super().__init__()
        self.dcc = dcc
        self.props_undo = {}
        for k, v in props.items():
            if not hasattr(dcc, k):
                raise ValueError("Curve does not have %s=%r property" % (k, v))
            self.props_undo[k] = getattr(dcc, k)
        self.props_do = props

    def apply(self, props):
        for k, v in props.items():
            setattr(self.dcc, k, v)

    def description(self):
        return 'Edit Curve Properties'

    def snap(self):
        pass

    def do(self):
        self.apply(self.props_do)
        self.dcc.update()

    def undo(self):
        self.apply(self.props_undo)
        self.dcc.update()


class CommandDcpAdd(Command):
    def __init__(self, curve: DigitizeCurve, cp: ControlPoint, where, left=None, right=None):
        super().__init__()
        assert isinstance(curve, DigitizeCurve)
        self.curve = curve
        self.cp = cp
        self.where = where
        if self.where is not None:
            self.left = CommandCpEdit(curve, left)
            self.right = CommandCpEdit(curve, right)

    def description(self):
        return 'Add Control Point'

    def update(self):
        self.curve.need_edit_handle_refresh = True
        self.curve.update()

    def snap(self):
        if self.where is not None:
            self.left.snap()
            self.right.snap()

    def do(self):
        if self.where is None:
            self.curve.elem.control_points.append(self.cp)
        else:
            self.left.do()
            self.right.do()
            self.curve.elem.control_points.insert(self.where, self.cp)
        self.update()

    def undo(self):
        self.curve.elem.control_points.remove(self.cp)
        if self.where:
            self.left.undo()
            self.right.undo()
        self.update()


class CommandDcpDel(Command):
    def __init__(self, curve: DigitizeCurve, cp: ControlPoint):
        super().__init__()
        assert isinstance(curve, DigitizeCurve)
        self.curve = curve
        self.cp = cp
        self.where = self.curve.elem.control_points.index(cp)

    def description(self):
        return 'Delete Control Point'

    def update(self):
        self.curve.need_edit_handle_refresh = True
        self.curve.update()

    def snap(self):
        pass

    def do(self):
        self.curve.elem.control_points.remove(self.cp)
        self.update()

    def undo(self):
        self.curve.elem.control_points.insert(self.where, self.cp)
        self.update()
