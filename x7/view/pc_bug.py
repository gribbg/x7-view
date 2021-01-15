# PyCharm debugger does locals()['self.var'] = value instead of locals()['self'].var = value

class Demo:
    def __init__(self):
        self.var = 'init'

    def show_var(self):
        print(self.var)
        print(locals())
        # To reproduce:
        # * Set a breakpoint on the line below
        # * While in the debugger, expand 'self' in the Debugger>Variables window
        # * Right-click on 'var' and choose 'Set Value...' (or hit F2)
        # * Put in any value
        # * Value shows up as a local variable named 'self.var' instead of updating self.var
        # * Result is visible in Debugger>Variables window after stepping and in output of locals()
        print(self.var)     # set breakpoint here
        print(locals())


d = Demo()
d.show_var()
