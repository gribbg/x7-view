"""
Simple file to validate that maketests is working.  Call maketests via:
>>> from x7.shell import *; maketests('x7.sample.needs_tests')
"""


def needs_a_test(a, b):
    return a+b
