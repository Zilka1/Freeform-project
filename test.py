import tkinter as tk
# import subprocess
# import os
import io
from PIL import Image

class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.line_start = None
        self.canvas = tk.Canvas(self, width=300, height=300, bg="white")
        self.canvas.bind("<Button-1>", lambda e: self.draw(e.x, e.y))
        self.button = tk.Button(self, text="save",
                                command=self.save)
        self.canvas.pack()
        self.button.pack(pady=10)

    def draw(self, x, y):
        if self.line_start:
            x_origin, y_origin = self.line_start
            self.canvas.create_line(x_origin, y_origin, x, y)
        self.line_start = x, y

    def save(self):
        ps = self.canvas.postscript(colormode='color')
        img = Image.open(io.BytesIO(ps.encode('utf-8')))
        img.save('/tmp/test.jpg')

app = App()
app.mainloop()