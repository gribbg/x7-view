import tkinter as tk


root = tk.Tk()

canvas = tk.Canvas(root, width=600, height=400)
canvas.pack()
canvas.create_line((0, 0, 600, 400), fill='blue')


def button():
    print('Button pressed, calling "image %s"' % image)
    # (self._w, 'scale') + args
    canvas.tk.call(canvas._w, 'image', '-foo', '-bar', image)


image = tk.PhotoImage(master=root, name='canvas1', width=20, height=20)
b = tk.Button(root, image=image, command=button)
b.pack()

root.mainloop()
