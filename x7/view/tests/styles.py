from tkinter import ttk
import tkinter

root = tkinter.Tk()

style = ttk.Style()
style.theme_create('new', 'default')
style.theme_use('new')
style.theme_settings('new', {
    '.': {
        'map': {
            'fieldbackground': [('invalid', 'red')],
        },
    },
    "TCombobox": {
        "configure": {"padding": 5},
        "map": {
            # "background": [("active", "green2"),                           ("!disabled", "green4")],
            # "fieldbackground": [("!disabled", "green3")],
            "foreground": [("focus", "OliveDrab1"),
                           ("!disabled", "OliveDrab2")]
        }
    },
    "TEntry": {
        "configure": {"padding": 15},
        "map": {
            # "background": [("active", "green2"),                           ("!disabled", "green4")],
            # "fieldbackground": [("!disabled", "green3")],
            "foreground": [("focus", "OliveDrab1"),
                           ("!disabled", "OliveDrab2")]
        }
    },
})

ttk.Combobox(root).pack()
e = ttk.Entry(root, text='This one is valid')
e.state(('!invalid', ))
e.pack()
print(e.state())
e = ttk.Entry(root, text='This one is invalid', state=[('invalid', )])
e.state(('invalid', ))
e.pack()
print(e.state())

root.mainloop()
