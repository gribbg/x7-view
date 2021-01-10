"""
Undo/redo framework for anim.edit
"""

from x7.geom.typing import *
from x7.geom.model import ControlPoint


__all__ = ['Command', 'CommandDummy', 'CommandStack', 'CommandEditCP']


class Command(object):
    """ABC for Command pattern"""
    def __init__(self):
        pass

    def description(self):
        unused(self)
        return 'No operation'

    def do(self):
        """Apply the change and call .update() or .erase() on impacted objects"""
        raise NotImplementedError

    def undo(self):
        """Apply the change and call .update() or .erase() on impacted objects"""
        raise NotImplementedError

    def snap(self):
        # Snap the current state.  This is optional, depending on the way command is used
        pass


class CommandDummy(Command):
    """Placeholder command that does nothing"""
    def __init__(self):
        super().__init__()

    def description(self):
        unused(self)
        return 'Dummy'

    def do(self):
        pass

    def undo(self):
        pass

    def snap(self):
        pass


class CommandStack(object):
    def __init__(self):
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []

    def reset(self):
        self.undo_stack = []
        self.redo_stack = []

    @property
    def undo_empty(self):
        return len(self.undo_stack) == 0

    @property
    def redo_empty(self):
        return len(self.redo_stack) == 0

    def do(self, command: Command):
        self.redo_stack = []
        self.undo_stack.append(command)
        command.do()

    def undo(self):
        if self.undo_stack:
            command = self.undo_stack.pop()
            self.redo_stack.append(command)
            command.undo()

    def redo(self):
        if self.redo_stack:
            command = self.redo_stack.pop()
            self.undo_stack.append(command)
            command.do()


class CommandEditCP(Command):
    def __init__(self, start: ControlPoint, end: Optional[ControlPoint] = None):
        super().__init__()
        self.cp = start
        self.orig_value = start.copy()
        self.new_value = end.copy() if end else None

    def description(self):
        unused(self)
        return 'Edit control point'

    def snap(self):
        self.new_value = self.cp.copy()

    def do(self):
        self.cp.restore(self.new_value)

    def undo(self):
        self.cp.restore(self.orig_value)
