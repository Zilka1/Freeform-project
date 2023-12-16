import tkinter as tk
from tkinter import colorchooser

def pick_color():
    color = colorchooser.askcolor(title="Select Color")
    if color[1]:  # Check if a color was chosen
        chosen_color = color[1]
        print("Chosen color:", chosen_color)
        # Do something with the chosen color, such as updating a canvas or widget

root = tk.Tk()

color_button = tk.Button(root, text="Pick Color", command=pick_color)
color_button.pack()

root.mainloop()