import tkinter as tk

def paint(event):
    x1, y1 = (event.x - 1), (event.y - 1)
    x2, y2 = (event.x + 1), (event.y + 1)
    item = canvas.create_oval(x1, y1, x2, y2, fill="black", outline="black")
    shapes.append(item)

def delete_last_shape():
    if shapes:
        last_shape = shapes.pop()
        canvas.delete(last_shape)

root = tk.Tk()
canvas = tk.Canvas(root, width=400, height=400)
canvas.pack()
canvas.bind("<B1-Motion>", paint)

shapes = []

delete_button = tk.Button(root, text="Delete Last Shape", command=delete_last_shape)
delete_button.pack()

root.mainloop()