from unittest import TestCase
from x7.view import undo
from x7.geom.model import *
from x7.geom.geom import *
from x7.lib.annotations import tests


@tests(undo.Command)
class TestCommand(TestCase):
    @tests(undo.Command.__init__)
    @tests(undo.Command.description)
    def test_basic(self):
        command = undo.Command()
        self.assertIsNotNone(command)
        self.assertEqual('No operation', command.description())

    @tests(undo.Command.do)
    def test_do(self):
        command = undo.Command()
        with self.assertRaises(NotImplementedError):
            command.do()

    @tests(undo.Command.undo)
    def test_do(self):
        command = undo.Command()
        with self.assertRaises(NotImplementedError):
            command.undo()


@tests(undo.CommandEditCP)
class TestCommandEditCP(TestCase):
    @tests(undo.CommandEditCP.__init__)
    @tests(undo.CommandEditCP.do)
    @tests(undo.CommandEditCP.undo)
    def test_do(self):
        cps = ControlPoint(Point(0, 0), Vector(1, 1), Vector(2, 3), 'smooth')
        cpe = ControlPoint(Point(10, 10), Vector(11, 12), Vector(12, 13), 'sharp')
        cmd = undo.CommandEditCP(cps, cpe)
        self.assertEqual(cps.c, Point(0, 0))
        self.assertEqual(cps.dl, Vector(1, 1))
        self.assertEqual(cps.dr, Vector(2, 3))
        self.assertEqual(cps.kind, 'smooth')
        cmd.do()
        self.assertEqual(cps.c, Point(10, 10))
        self.assertEqual(cps.dl, Vector(11, 12))
        self.assertEqual(cps.dr, Vector(12, 13))
        self.assertEqual(cps.kind, 'sharp')
        cmd.undo()
        self.assertEqual(cps.c, Point(0, 0))
        self.assertEqual(cps.dl, Vector(1, 1))
        self.assertEqual(cps.dr, Vector(2, 3))
        self.assertEqual(cps.kind, 'smooth')

    @tests(undo.CommandEditCP.description)
    def test_do(self):
        cp = ControlPoint(Point(0, 0), Vector(1, 1), Vector(2, 3), 'smooth')
        self.assertEqual('Edit control point', undo.CommandEditCP(cp).description())

    @tests(undo.CommandEditCP.snap)
    def test_snap(self):
        # snap(self)
        pass  # TODO-impl x7.view.undo.CommandEditCP.snap test


@tests(undo.CommandStack)
class TestCommandStack(TestCase):
    @tests(undo.CommandStack.__init__)
    def test___init__(self):
        cs = undo.CommandStack()
        self.assertEqual(len(cs.undo_stack), 0)
        self.assertEqual(len(cs.redo_stack), 0)

    # noinspection DuplicatedCode
    @tests(undo.CommandStack.do)
    @tests(undo.CommandStack.redo)
    @tests(undo.CommandStack.undo)
    def test_do(self):
        cps = ControlPoint(Point(1, 1), Vector(2, 2), Vector(4, 3), 'smooth')
        cpe = ControlPoint(Point(11, 11), Vector(11, 12), Vector(12, 14), 'very-smooth')
        cmd = undo.CommandEditCP(cps, cpe)
        cs = undo.CommandStack()
        cs.do(cmd)
        self.assertEqual(len(cs.undo_stack), 1)
        self.assertEqual(len(cs.redo_stack), 0)
        self.assertEqual(cps.c, Point(11, 11))
        self.assertEqual(cps.dl, Vector(11, 12))
        self.assertEqual(cps.dr, Vector(12, 14))
        self.assertEqual(cps.kind, 'very-smooth')
        for n in range(2):
            cs.undo()       # Only the first undo should do anything
            self.assertEqual(len(cs.undo_stack), 0)
            self.assertEqual(len(cs.redo_stack), 1)
            self.assertEqual(cps.c, Point(1, 1))
            self.assertEqual(cps.dl, Vector(2, 2))
            self.assertEqual(cps.dr, Vector(4, 3))
            self.assertEqual(cps.kind, 'smooth')
        for n in range(2):
            cs.redo()       # Only the first redo should do anything
            self.assertEqual(len(cs.undo_stack), 1)
            self.assertEqual(len(cs.redo_stack), 0)
            self.assertEqual(cps.c, Point(11, 11))
            self.assertEqual(cps.dl, Vector(11, 12))
            self.assertEqual(cps.dr, Vector(12, 14))
            self.assertEqual(cps.kind, 'very-smooth')


@tests(undo)
class TestModUndo(TestCase):
    """Tests for stand-alone functions in x7.view.undo module"""
