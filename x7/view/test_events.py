from tkinter import *
import re


root = Tk()
top = Frame(root, width=500, height=500)

mb = Menubutton(top, text="condiments", relief=RAISED)
# mb.grid(column=0, row=0)
mb.menu = Menu(mb, tearoff=0)
mb["menu"] = mb.menu

mayoVar = IntVar()
ketchVar = IntVar()

mb.menu.add_checkbutton(label="mayo", variable=mayoVar)
mb.menu.add_checkbutton(label="ketchup", variable=ketchVar)

mb.pack()

Button(top, text='Just a button').pack()
Button(top, text='Just a button').pack()
b = Button(top, text='Just a button')
b.pack()
Label(top, text='').pack()
Label(top, text='').pack()
Label(top, text='').pack()
Label(top, text=' '*80).pack()


log_one = True


def first(event):
    global log_one
    if log_one:
        log_one = False
        print(event.state, event)
        pat = re.compile(r'.* state=([^ ]*) .*')
        for n in range(16):
            event.state = 1 << n
            m = pat.match(str(event))
            print('%s = 0x%04x' % (m.group(1).upper(), event.state))


def callback(evname):
    def actual_func(ev):
        first(ev)
        print('cb for %s: %s .state: %r .widget: %s' % (evname, ev, ev.state, ev.widget))
    return actual_func


def mbcallback(ev):
    print('mbcb: ', ev, '  widget:', ev.widget)


def bindall(root):
    doc = root.bind.__doc__
    # doc = 'my TYPE is one of this or\n that and DETAIL is not relevant'
    pat = re.compile(r'.*TYPE is one of (.*) and DETAIL is the button.*', re.DOTALL)
    m = pat.match(doc)
    print(m.groups() if m else '???')
    from_doc = set('<%s>' % ev for ev in m.group(1).replace('\n', ',').replace(' ', '').replace(',,', ',').split(','))

    # From https://www.tcl-lang.org/man/tcl8.5/TkCmd/bind.htm
    ALL = """
    Activate, Deactivate
    MouseWheel
    KeyPress, KeyRelease
    ButtonPress, ButtonRelease, Motion
    Configure
    Map, Unmap
    Visibility
    Expose
    Destroy
    FocusIn, FocusOut
    Enter, Leave
    Property
    Colormap
    MapRequest, CirculateRequest, ResizeRequest, ConfigureRequest, Create
    Gravity, Reparent, Circulate
    """

    # From https://www.tcl-lang.org/man/tcl8.5/TkCmd/bind.htm#M7
    """
        Activate
        Destroy
        Map
        ButtonPress, Button
        Enter
        MapRequest
        ButtonRelease
        Expose
        Motion
        Circulate
        FocusIn
        MouseWheel
        CirculateRequest
        FocusOut
        Property
        Colormap
        Gravity
        Reparent
        Configure
        KeyPress, Key
        ResizeRequest
        ConfigureRequest
        KeyRelease
        Unmap
        Create
        Leave
        Visibility
        Deactivate    
    """
    all_events = ['<%s>' % ev for ev in ALL.strip().replace('\n', ',').replace(' ', '').split(',')]
    from_source = set(all_events)
    from_evt = set('<%s>' % ev for ev in EventType.__members__.keys())
    print('doc-src: ', sorted(from_doc-from_source))
    print('src-doc: ', sorted(from_source-from_doc))
    everything = from_doc.union(from_source)
    print('everything-evt: ', sorted(everything-from_evt))
    print('evt-everything: ', sorted(from_evt-everything))
    everything.update(from_evt)
    virtual_events = root.event_info()
    everything.update(virtual_events)
    everything.remove('<Motion>')
    print('everything: ', sorted(everything))
    for ev in sorted(everything):
        try:
            do_add = not False
            root.bind_all(ev, callback(ev), do_add)
            root.bind(ev, callback(ev), do_add)
            root.bind_class('Menubutton', ev, callback(ev), do_add)
        except Exception as err:
            print('Error on bind(%s): %s' % (ev, err))
        try:
            do_add = False
            mb.bind_all(ev, callback(ev), do_add)
            mb.bind(ev, callback(ev), do_add)
        except Exception as err:
            print('Error on mb.bind(%s): %s' % (ev, err))


print(root.bind_all())
print(root.bind_class('Menubutton'))
print(root.bind_class('Button'))
root.bind_class('Menubutton', '<<Invoke>>', callback('<<Invoke>>'), False)
root.bind_class('Button', '<<Invoke>>', callback('<<Invoke>>'), False)
root.bind_class('Menubutton', '<<Invoke>>', callback('<<Invoke>>'), False)
mb.bind('<<Invoke>>', callback('<<Invoke>>'), False)
b.bind('<<Invoke>>', callback('<<Invoke>>'), False)
print(mb.bind_all())
print(mb.bind())
print(b.bind())

if not False:
    bindall(top)
    top.pack()
    top.mainloop()
