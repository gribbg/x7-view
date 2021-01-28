# from: https://tkdocs.com/tutorial/menus.html#popupmenus
from tkinter import *
root = Tk()
button = Button(root, text='Button', command=lambda: print('Button pressed'))
button.pack()
menu = Menu(root, tearoff=0)
for i in ('One', 'Two', 'Three'):
    menu.add_command(label=i)
if (root.tk.call('tk', 'windowingsystem') == 'aqua'):
    root.bind('<2>', lambda e: menu.post(e.x_root, e.y_root))
    root.bind('<Control-1>', lambda e: menu.post(e.x_root, e.y_root))
else:
    root.bind('<3>', lambda e: menu.post(e.x_root, e.y_root))
root.mainloop()
