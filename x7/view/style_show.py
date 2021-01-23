"""
    Debugging: various style introspection and test routines
"""

import os
import re
import tkinter
from tkinter import ttk
import tkinter as tk
from typing import List
from x7.view.widgets import ValidatingEntry, Toolbutton, RadioToolbutton
import x7.view.style


def style_element_options(style_name):
    """Function to expose the options of every element associated to a widget
       style_name."""
    # Based on: https://stackoverflow.com/a/48933106/14856977

    style = ttk.Style()
    style_layout = style.layout(style_name)

    def elements(layout):
        out = []
        for elem, info in layout:
            out.append(elem)
            out.extend(elements(info.get('children', [])))
        return out

    def layout_format(layout, indent=''):
        out = []
        for elem, info in layout:
            sticky = info.get('sticky', '????')
            side = info.get('side')
            side = 'side=%s, ' % side if side else ''
            expand = info.get('expand')
            expand = 'expand=%s, ' % expand if expand else ''
            options = style.element_options(elem)
            out.append('%s[%s, sticky=%s, %s%s%s' % (indent, elem, sticky, side, expand, options))
            out.extend(layout_format(info.get('children', []), indent='  '+indent))
        if out:
            if out[-1].endswith(','):
                out[-1] = out[-1][:-1]
            out[-1] = out[-1] + ']'
        return out

    print('%s:' % style_name)
    print('eo(%s): %s' % (style_name, style.element_options(style_name)))
    print('\n'.join(layout_format(style_layout, '  ')))


def find_themes():
    where = ttk.__file__
    for n in range(3):
        where = os.path.dirname(where)
    where = os.path.join(where, 'tcl', 'tk8.6', 'ttk')
    print(where)
    pat = re.compile(r'ttk::style\s+configure\s+([^\s]+)')
    styles = set()
    for fn in os.listdir(where):
        if fn.endswith('Theme.tcl') or fn == 'defaults.tcl':
            print(fn)
            with open(os.path.join(where, fn), 'r') as f:
                for l in f:
                    if m := pat.search(l):
                        style = m.group(1)
                        if style != '.' and style != '"."':
                            styles.add(style)
    print(sorted(styles))
    for sn in sorted(styles):
        try:
            style_element_options(sn)
        except tk.TclError:
            print('%s: not found' % sn)


def show_style():
    # root = tk.Tk()
    # find_themes(); exit(0)
    style = ttk.Style()
    print('Current:', style.theme_use())
    print('Themes:', style.theme_names())
    print('Elements:', sorted(style.element_names()))
    # print('Other:', style.theme_settings('default', {}))
    # exit(0)

    x7.view.style.setup_style()
    style_element_options('TLabel')
    style_element_options('TSeparator')
    style_element_options('TRadiobutton')
    style_element_options('TCheckbutton')
    style_element_options('TCombobox')
    style_element_options('TLabel')
    style_element_options('TLabelframe')
    style_element_options('TEntry')
    style_element_options('TButton')
    style_element_options('TFrame')
    style_element_options('ValidationBorder')
    print(style.layout('ValidationBorder'))
    print(style.configure('ValidationBorder'))
    print(style.map('ValidationBorder'))
    exit(0)

    def dump_info():
        print('Entry style.font is ', ttk.Style().lookup("TEntry", 'font'))
        print('Entry style.bg is ', ttk.Style().lookup("TEntry", 'background'))
        print('Entry style.fbg is ', ttk.Style().lookup("TEntry", 'fieldbackground'))
        print('Entry style.fbg.disabled is ', ttk.Style().lookup("TEntry", 'fieldbackground', ('disabled', )))
        print('Entry style.fbg.ro is ', ttk.Style().lookup("TEntry", 'fieldbackground', ('readonly', )))
    dump_info()
    x7.view.style.setup_style()
    dump_info()
    exit(0)


ALL_STATES = [
    # From: tcltk/tk/generic/ttk/ttkState.c
    "active",           # Mouse cursor is over widget or element
    "disabled",         # Widget is disabled
    "focus",            # Widget has keyboard focus
    "pressed",          # Pressed or "armed"
    "selected",         # "on", "true", "current", etc.
    "background",       # Top-level window lost focus (Mac,Win "inactive")
    "alternate",        # Widget-specific alternate display style
    "invalid",          # Bad value
    "readonly",         # Editing/modification disabled
    "hover",            # Mouse cursor is over widget
    "reserved1",        # Reserved for future extension
    "reserved2",        # Reserved for future extension
    "reserved3",        # Reserved for future extension
    "user3",            # User-definable state
    "user2",            # User-definable state
    "user1",            # User-definable state
]


def test_style():
    root = tk.Tk()
    style = ttk.Style()
    x7.view.style.setup_style()

    def theme_changed(*_args):
        new_theme = theme_var.get()
        print('Theme changed to ', new_theme)
        style.theme_use(new_theme)

    row_top = 5
    col_state = 5
    col_max = 10
    frame = ttk.Frame(root, padding=4)
    frame.pack()
    top = ttk.Frame(frame)
    top.grid(column=0, columnspan=col_max, row=0, sticky='we')
    top.grid_columnconfigure(0, weight=1)
    top.grid_columnconfigure(3, weight=1)
    ttk.Label(top, text='Theme').grid(column=1, row=0, sticky='ew')
    theme_var = tk.Variable(top, value=style.theme_use(), name='style')
    theme_var.trace('w', theme_changed)
    theme_combo = ttk.Combobox(top, values=style.theme_names(), textvariable=theme_var)
    theme_combo.grid(column=2, row=0, sticky='ew')
    ttk.Separator(frame, orient='h').grid(column=0, columnspan=col_max, row=1, sticky='ew', pady=2)

    def make_frame(outer):
        f = ttk.Frame(outer, borderwidth=2, relief=tk.SUNKEN, takefocus=True)
        f.grid(padx=2, pady=2, ipadx=2, ipady=2)
        ttk.Label(f, text='Label inside frame').grid()
        return f

    def make_labelframe(outer):
        f = ttk.Labelframe(outer, borderwidth=2, relief=tk.SUNKEN, takefocus=True, text='Label on Frame')
        f.grid(padx=2, pady=2, ipadx=2, ipady=2)
        ttk.Label(f, text='Label inside frame').grid()
        return f

    def make_labeled_scale(outer, labeled=True, orient='h'):
        f = ttk.Frame(outer)
        f.scale_variable = tk.DoubleVar(f)
        if labeled:
            ls = ttk.LabeledScale(f, from_=0, to=100, variable=f.scale_variable)
            ls.scale.configure(length=250)
        elif orient == 'v':
            ls = ttk.Scale(f, from_=0, to=100, length=90, variable=f.scale_variable, orient='v')
        else:
            ls = ttk.Scale(f, from_=0, to=100, length=250, variable=f.scale_variable)
        ls.grid(row=0, column=0, padx=2, pady=2, ipadx=2, ipady=2)
        lbl = ttk.Label(f, width=8)
        lbl.grid(row=0, column=1)
        f.scale_variable.trace_variable('w', lambda *args: lbl.configure(text='%6.2f' % f.scale_variable.get()))
        f.scale_variable.set(50.0)
        return f, ls

    def make_entry_v(outer, read_only=False):
        def validator(_entry: ValidatingEntry, s: str):
            s = s.lower()
            if 'invalid' in s:
                if 'message' in s:
                    return 'Invalid entry because "invalid" is in entry'
                else:
                    return False
            return True
        val = 'Read only entry' if read_only else 'Invalid entry with message'
        ev = ValidatingEntry(outer, width=40, value=val, validator=validator, read_only=read_only)
        return ev.entry, ev.entry_field

    #  'Menubutton(Widget)', 'Notebook(Widget)',
    #  'OptionMenu(Menubutton)', 'Panedwindow(Widget, tkinter.PanedWindow)', 'Progressbar(Widget)',
    #  'Scrollbar(Widget, tkinter.Scrollbar)',
    #  'Separator(Widget)', 'Sizegrip(Widget)', 'Spinbox(Entry)',
    #  'Treeview(Widget, tkinter.XView, tkinter.YView)',

    radio_var = tk.StringVar(root, value='rb2')
    check_var = tk.IntVar(root, value=1)

    widget_init_data = [
        ('Button', lambda f: ttk.Button(f, text='Button Text')),
        ('Checkbutton', lambda f: ttk.Checkbutton(f, text='Checkbutton Text', variable=check_var)),
        ('Radiobutton', lambda f: ttk.Radiobutton(f, text='Radiobutton Text', value='rb1', variable=radio_var)),
        ('RadioToolbutton', lambda f: RadioToolbutton(f, value='rb2', text='RadioToolbutton Text', variable=radio_var)),
        ('RadioTb w/image', lambda f: RadioToolbutton(f, value='rb3', icon='pencil', variable=radio_var)),
        ('Toolbutton', lambda f: Toolbutton(f, text='Toolbutton Text')),
        ('Toolbutton w/img', lambda f: Toolbutton(f, icon='pencil')),
        ('Frame', make_frame),
        ('Labelframe', make_labelframe),
        ('Combobox', lambda f: ttk.Combobox(f, values=tuple('abc'))),
        ('Entry', lambda f: ttk.Entry(f, width=40)),
        ('EntryV', make_entry_v),
        ('EntryV RO', lambda f: make_entry_v(f, read_only=True)),
        ('Label', lambda f: ttk.Label(f, text='Example Text')),
        ('Scale', lambda f: make_labeled_scale(f, False)),
        ('ScaleV', lambda f: make_labeled_scale(f, False, 'v')),
        ('LabeledScale', make_labeled_scale),
    ]
    cur_widget = tk.IntVar(frame)

    def check_status():
        widget = widgets[cur_widget.get()]
        cur_state = widget.state()
        # print('%3d: %s' % (cur_widget.get(), cur_state))
        for var, state in zip(states, ALL_STATES):
            selected = state in cur_state
            var.set(selected)
        root.after(100, check_status)

    def changed(var: tk.Variable, idx):
        def callback():
            state = '%s%s' % ('' if var.get() else '!', ALL_STATES[idx])
            widgets[cur_widget.get()].state((state, ))
        return callback

    widgets: List[ttk.Widget] = []
    ttk.Label(frame, text='Widgets').grid(column=0, columnspan=col_state, row=row_top)
    for index, (name, func) in enumerate(widget_init_data):
        row = index+1+row_top
        ttk.Radiobutton(frame, text=name, variable=cur_widget, value=index).grid(column=0, row=row, sticky='w')
        item = func(frame)
        item_to_grid, item_to_watch = item if isinstance(item, tuple) else (item, item)
        item_to_grid.grid(column=1, row=row, sticky='w')
        if name == 'ScaleV':
            item_to_grid.grid(column=3, row=row-1, rowspan=3, sticky='w')
        if 'Radio' in name or 'Check' in name:
            if 'Radio' in name:
                var_to_use = radio_var
                # var_to_use.set(item.configure('value')[-1])
            else:
                var_to_use = check_var
                # var_to_use.set(True)
            rf = ttk.Frame(frame)
            rf.grid(column=3, row=row, sticky='w')
            ttk.Label(rf, text='Variable: ').grid(column=0, row=0, sticky='w')
            ttk.Label(rf, textvariable=var_to_use).grid(column=1, row=0, sticky='w')
        try:
            item_to_grid.configure(justify=tk.LEFT)
        except tkinter.TclError:
            pass
        widgets.append(item_to_watch)

    states: List[tk.BooleanVar] = []
    ttk.Label(frame, text='State').grid(column=col_state, columnspan=col_max-col_state, row=row_top)
    for index, name in enumerate(ALL_STATES):
        row = index+1+row_top
        state_var = tk.BooleanVar(frame, value=True)
        b = ttk.Checkbutton(frame, text=name, variable=state_var, command=changed(state_var, index))
        b.grid(column=col_state, row=row, sticky='w')
        states.append(state_var)

    sep_height = 1 + max(len(ALL_STATES), len(widget_init_data))
    ttk.Separator(frame, orient=tk.VERTICAL).grid(column=col_state-1, row=row_top, rowspan=sep_height, sticky='ns', padx=2)
    check_status()

    root.mainloop()
    exit(0)


if __name__ == '__main__':
    show_style()
    test_style()
