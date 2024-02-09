import tkinter as tk
from tkinter import filedialog

# Create the Tkinter window
root = tk.Tk()

# Define the function to select the directory and file name
def select_directory_and_file():
    # Open the file dialog
    file_path = filedialog.asksaveasfilename(initialdir="/", title="Select a file", filetypes=(("PNG", "*.png"),), defaultextension=".png", initialfile="project name.png")

    # Print the selected file path
    print(file_path)

# Create a button to trigger the function
button = tk.Button(root, text="Select Directory and File Name", command=select_directory_and_file)
button.pack()

# Run the main loop
root.mainloop()