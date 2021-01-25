from tkinter import *
import re
import time
from typing import Dict, Tuple

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


event_types_seen = set()
event_attributes: Dict[str, Tuple[set, set]] = dict()
event_attrs_known = '''
    serial num focus height width keycode state time
    x y x_root y_root char send_event keysym keysym_num
    type widget delta
'''.split()


def track_event(event, event_name):
    if not event_types_seen:
        print(event.state, event)
        pat = re.compile(r'.* state=([^ ]*) .*')
        for n in range(16):
            event.state = 1 << n
            m = pat.match(str(event))
            print('%s = 0x%04x' % (m.group(1).upper(), event.state))
    if event_name not in event_types_seen:
        event_types_seen.add(event_name)
        from pprint import pp
        pp({'Event: '+event_name: event.__dict__})
    for k, v in event.__dict__.items():
        attr = event_attributes.setdefault(k, (set(), set()))
        attr[0].add(type(v))
        attr[1].add(v)
    for attr in event_attrs_known:
        if not hasattr(event, attr):
            event_attributes.setdefault(attr, (set(), set()))[1].add('Missing')


def track_dump():
    print('- ' * 60)
    print('%d events seen: %s' % (len(event_types_seen), ', '.join(sorted(event_types_seen))))
    print('%d event attributes seen' % len(event_attributes))
    attrs_found = set(event_attributes.keys())
    print('af: ', attrs_found)
    print('ak: ', event_attrs_known)
    print('afd:', list(attrs_found.difference(event_attrs_known)))
    attrs_to_iter = event_attrs_known + list(attrs_found.difference(event_attrs_known))

    def fmt(val):
        if isinstance(val, EventType):
            return 'EventType.%s' % val
        if isinstance(val, Misc):
            return 'tkinter.%s' % type(val).__name__
        return repr(val)
    for attr in attrs_to_iter:
        attr_types, attr_values = event_attributes[attr]
        types = ', '.join(t.__name__ for t in attr_types)
        print('   %-12s: %s' % (attr, types))
        print('      [%d]: %s' % (len(attr_values), ', '.join(fmt(z) for z in list(attr_values)[:20])))

    print('__init__')
    for attr in attrs_to_iter:
        attr_types, attr_values = event_attributes[attr]
        if len(attr_types) > 1:
            types = 'Union[%s]' % ', '.join(t.__name__ for t in attr_types)
        else:
            types = attr_types.pop().__name__
        print("        %s: %s = %r" % (attr, types, '??' if '??' in attr_values else 'unknown'))
        if 'Missing' in attr_values:
            print('        ...missing')


def callback(evname: str, verbose=False):
    def actual_func(ev):
        track_event(ev, evname)
        print('cb for %s: %s .state: %r .widget: %s' % (evname, ev, ev.state, ev.widget))
    print('Cb:', evname, verbose)
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
    verbose_set = {'<%s>' % ev for ev in ('KeyPress', 'ButtonPress')}
    for ev in sorted(everything):
        verbose = ev in verbose_set
        try:
            do_add = not False
            root.bind_all(ev, callback(ev, verbose), do_add)
            root.bind(ev, callback(ev, verbose), do_add)
            root.bind_class('Menubutton', ev, callback(ev), do_add)
        except Exception as err:
            print('Error on bind(%s): %s' % (ev, err))
        try:
            do_add = False
            mb.bind_all(ev, callback(ev, verbose), do_add)
            mb.bind(ev, callback(ev, verbose), do_add)
        except Exception as err:
            print('Error on mb.bind(%s): %s' % (ev, err))


def popup(ev):
    def popped(thing):
        print('%.4f: popped: %s' % (time.time() % 10, thing))

    print('%.4f: Popup: %s' % (time.time() % 10, ev))
    menu = Menu(top, tearoff=0)
    menu.add_command(label="Thing1", command=lambda: popped('thing1'))
    menu.add_command(label="Thing2", command=lambda: popped('thing2'))
    print('%.4f: Pre-post' % (time.time() % 10))
    menu.post(ev.x_root, ev.y_root)
    print('%.4f: Post-post' % (time.time() % 10))


top.bind('<Button-3>', popup)
top.bind('<<ContextMenu>>', popup)

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
    track_dump()
