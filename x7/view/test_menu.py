from tkinter import *
from pprint import pprint
import time


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


def popped(thing):
    print('%.4f: popped: %s' % (time.time() % 10, thing))


def popup(ev):
    print('%.4f: Popup: %s' % (time.time() % 10, ev))
    menu = Menu(top, tearoff=0)
    menu.add_command(label="Thing1", command=lambda: popped('thing1'))
    menu.add_command(label="Thing2", command=lambda: popped('thing2'))
    print('%.4f: Pre-post' % (time.time() % 10))
    menu.post(ev.x_root, ev.y_root)
    print('%.4f: Post-post' % (time.time() % 10))


top.bind('<Button-3>', popup)

# Sample output on Windows:
# 2.6393: Popup: <ButtonPress event state=Mod1 num=3 x=254 y=161>
# 2.6393: Pre-post
# 4.2658: Post-post
# 4.2658: popped: thing2


def callback(evname):
    def actual_func(ev):
        print('cb for %s: %s  .widget: %s' % (evname, ev, ev.widget))
    return actual_func


top.pack()
top.mainloop()
