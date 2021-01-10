from tkinter import *
from pprint import pprint


root = Tk()
top = Frame(root, width=500, height=500)

mb = Menubutton(top, text="condiments", relief=RAISED)
# mb.grid(column=0, row=0)
mb.menu = Menu(mb, tearoff=0)
mb["menu"] = mb.menu


iv = IntVar(mb, value=1)


def what():
    print('iv is', iv.get())


def iv_trace(name=None, index=None, mode=None):
    print('iv_trace: name=', name, ' index=', index, ' mode=', mode)


iv.trace('w', iv_trace)

addVar = StringVar()
addVar.set('something')

mb.menu.add_checkbutton(label="mayo", state='active', variable=iv, command=what)  # , value='mayo', variable=addVar)
# mb.menu.add_checkbutton(label="ketchup", value='ketchup', variable=addVar)

mb.pack()
pprint(mb.menu.entryconfigure(0))
print(mb.menu.entrycget(0, 'indicatoron'))


Button(top, textvariable=addVar).pack()
Button(top, text='Just a button').pack()
Button(top, text='Just a button').pack()
Label(top, text='').pack()
Label(top, text='').pack()
Label(top, text='').pack()
Label(top, text=' '*80).pack()


def callback(evname):
    def actual_func(ev):
        print('cb for %s: %s  .widget: %s' % (evname, ev, ev.widget))
    return actual_func


top.pack()
top.mainloop()
