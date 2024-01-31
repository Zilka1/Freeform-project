import tkinter as tk

class Rect():
    def __init__(self, color, width, x1, y1, x2=None, y2=None, id_=-1):
        self.color = color
        self.width = width
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2 or x1, y2 or y1 # if x2 is None, then x2 = x1, if y2 is None then y2 = y1
        self.id = id_ # id of the whole drawing in the sql db, not an id of a stroke on the canvas

    def update(self, x2, y2):
        self.x2, self.y2 = x2, y2

    def draw(self, canvas: tk.Canvas):
        self.id_in_canvas = canvas.create_rectangle(self.x1, self.y1, self.x2, self.y2, width=self.width, outline=self.color)
    
    def delete_from_canvas(self, canvas: tk.Canvas):
        canvas.delete(self.id_in_canvas)
    
    def redraw(self, canvas: tk.Canvas):
        self.delete_from_canvas(canvas)
        self.draw(canvas)


class Oval(Rect):
    # def __init__(self, color, width, x1, y1, x2=None, y2=None, id_=-1):
    #     super().__init__(color, width, x1, y1, x2, y2, id_)

    def draw(self, canvas: tk.Canvas):
        self.id_in_canvas = canvas.create_oval(self.x1, self.y1, self.x2, self.y2, width=self.width, outline=self.color)