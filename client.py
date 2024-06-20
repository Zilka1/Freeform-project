from drawing import Drawing
from rect_oval import Rect, Oval
from socket_helper import SocketHelper
import tkinter as tk
from tkinter import colorchooser
# import sqlite3
# import os
import socket
import threading
import pickle
from PIL import Image, ImageDraw
# from pathlib import Path
# import queue
# import time
# import struct
from tkinter import filedialog
from cipher import Cipher
from constants import NONCE
from hashlib import sha256


class CanvasGUI:
    def __init__(self, client_socket, command_client_socket, file_name, shared_key, pwd=None, exists=False):
        # self.dir = r'C:\Users\hp\Desktop\Freeform project\projects (db)\\'
        # self.file_name = file_name
        # self.full_path = self.dir + self.file_name

        self.cipher = Cipher(shared_key, NONCE)

        self.project_name = file_name

        self.client_socket = client_socket
        self.command_client_socket = command_client_socket

        self.drawings = []
        self.deleted_drawings = []

        self.mode = "drawing"
        self.color = "#000000"
        self.color_changed = False
        self.target = -1  # setup for target
        self.show_target = True

        self.root = tk.Tk()
        self.root.title("Drawing Application - " + file_name)

        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="white")
        self.canvas.pack()

        self.canvas.bind("<ButtonPress-1>", self.mouse_pressed)
        self.canvas.bind("<B1-Motion>", self.mouse_pressed_moved)
        self.canvas.bind(
            "<ButtonRelease-1>", lambda _: threading.Thread(target=self.end_drawing).start())

        self.canvas.bind("<Motion>", self.move_target)
        self.canvas.bind("<Leave>", self.hide_target)

        self.root.bind("<Control-z>", self.delete_last_drawing)
        self.root.bind("<Control-y>", self.redo_last_deleted_drawing)

        self.colors_frame = tk.Frame(self.root)
        self.colors_frame.pack()

        font = ("Arial", 18)

        self.pick_color_b = tk.Button(
            self.colors_frame, text="", command=self.pick_color, background=self.color, padx=8)
        self.pick_color_b.grid(row=0, column=0, padx=5)

        def set_mode(mode):
            self.mode = mode

            if mode == "rect" or mode == "oval":
                self.show_target = False
                self.canvas.config(cursor="tcross")
            elif mode == "drawing":
                self.show_target = True
                self.canvas.config(cursor="none")

        tk.Button(self.colors_frame, text="DRAWING", font=font,
                  command=lambda: set_mode("drawing")).grid(row=0, column=4)
        tk.Button(self.colors_frame, text="RECTANGLE", font=font,
                  command=lambda: set_mode("rect")).grid(row=0, column=5)
        tk.Button(self.colors_frame, text="OVAL", font=font,
                  command=lambda: set_mode("oval")).grid(row=0, column=6)

        vcmd = (self.root.register(self.width_entry_validation),
                "%P")  # used to deal with validation in Tcl
        self.line_width_entry = tk.Entry(self.colors_frame, validate="all", validatecommand=vcmd,
                                         width=4, justify="center")  # %P -> new value of entry box
        self.line_width_entry.grid(row=0, column=1)
        self.line_width_entry.insert(0, "10")  # Sets starting width

        tk.Button(self.colors_frame, text="UNDO", font=font,
                  command=self.delete_last_drawing).grid(row=0, column=2)  # ↶
        tk.Button(self.colors_frame, text="REDO", font=font,
                  command=self.redo_last_deleted_drawing).grid(row=0, column=3)  # ↷

        tk.Button(self.colors_frame, text="SAVE IMG", font=font,
                  command=self.save_img).grid(row=0, column=8)

        self.canvas.config(cursor="none")

        self.window_open = True  # Used to cut the connection when the user closes the window

        self.receive_lock = threading.Lock()

        if (exists):
            self.load_canvas()
        else:
            self.create_new_db(pwd)

        receive_thread = threading.Thread(
            target=self.receive_data, args=(self.client_socket,))
        receive_thread.start()

        self.root.mainloop()

        self.window_open = False  # Used to cut the connection when the user closes the window
        print("windows closed")

        receive_thread.join()

    def start_drawing(self, event):
        '''
            Initializes a new drawing and creates an oval shape at the starting position of the mouse cursor.
        '''

        width = int(self.line_width_entry.get())

        self.deleted_drawings = []  # Clears the redo option

        self.prev_x, self.prev_y = event.x, event.y
        self.cur_drawing = Drawing(self.color, width)

        circle_off = width/2 - 1
        x1, y1 = (event.x - circle_off), (event.y - circle_off)
        x2, y2 = (event.x + circle_off), (event.y + circle_off)
        id_ = self.canvas.create_oval(
            x1, y1, x2, y2, fill=self.color, outline="")

        self.cur_drawing.add_point((event.x, event.y))
        self.cur_drawing.add_id(id_)

    def draw(self, event):
        '''
        Creates a line between the previous and current position of the mouse cursor.
        '''

        # Deals with a bug where the target would update if the mouse i pressed
        self.move_target(event)

        width = int(self.line_width_entry.get())

        x, y = event.x, event.y
        id_ = self.canvas.create_line(
            self.prev_x, self.prev_y, x, y, fill=self.color, width=width)
        self.cur_drawing.add_id(id_)
        self.prev_x, self.prev_y = x, y

        if (width > 3):  # otherwise it looks weird
            # offset, got to be slightly lower than width/2 so it wont buldge out
            circle_off = width/2 - 1
            x1, y1 = (event.x - circle_off), (event.y - circle_off)
            x2, y2 = (event.x + circle_off), (event.y + circle_off)
            id_ = self.canvas.create_oval(
                x1, y1, x2, y2, fill=self.color, outline="")
            self.cur_drawing.add_id(id_)

        self.cur_drawing.add_point((x, y))

    def end_drawing(self, *_):  # *_ to deal with event
        '''
            Assigns an ID to the current drawing, adds it to the list of drawings and sends it to the server.
        '''
        cur_id = self.get_and_inc_id()
        self.cur_drawing.id = cur_id

        self.drawings.append(self.cur_drawing)
        self.send_to_db(self.cur_drawing)

    def hide_target(self, *_):  # *_ to deal with event
        '''
            Hides the target shape indicating the area to be painted. (used when the mouse leaves the canvas)
        '''
        self.canvas.delete(self.target)
        self.target = -1

    def move_target(self, event):
        '''
            Updates the position of the target shape to follow the mouse cursor.
        '''
        if (not self.show_target):
            return

        if (self.target != -1):
            self.canvas.delete(self.target)
        circle_off = max(5/2, int(self.line_width_entry.get())/2)
        x1, y1 = (event.x - circle_off), (event.y - circle_off)
        x2, y2 = (event.x + circle_off), (event.y + circle_off)
        # self.target = self.canvas.create_oval(x1, y1, x2, y2, fill="", outline=self.color, dash=(2,1)) # shows the outline of the area you'd paint
        # shows the outline of the area you'd paint
        self.target = self.canvas.create_oval(
            x1, y1, x2, y2, fill="", outline=self.color)

    def set_color(self, color):
        '''
            Sets the color variable to the selected color.
        '''
        self.color = color

    def delete_last_drawing(self, *_):  # *_ to deal with event if given
        '''
            Removes the last drawing from the list of drawings, deletes it from the canvas, and sends a delete msg to the server.
        '''
        if self.drawings:
            d = self.drawings.pop()
            d.delete_from_canvas(self.canvas)
            self.deleted_drawings.append(d)

            # get id to delete
            id_ = d.id

            print("id", id_)

            SocketHelper.send_msg(self.client_socket,
                                  pickle.dumps(("delete", id_)))

    def redo_last_deleted_drawing(self, *_):  # *_ to deal with event if given
        '''
            Restores the last deleted drawing from the list of deleted drawings and redraws it on the canvas.
        '''
        if self.deleted_drawings:
            d = self.deleted_drawings.pop()
            self.drawings.append(d)
            d.draw(self.canvas)

            self.send_to_db(d)

            # self.save_row(d)

    def width_entry_validation(self, value):
        return value == "" or (value.isnumeric() and int(value) <= 45)

    def load_canvas(self):
        '''
            Loads drawings from the database and adds them to the canvas.
        '''
        SocketHelper.send_msg(self.client_socket,
                              pickle.dumps(("load_canvas", None)))

        with self.receive_lock:
            data = self.cipher.aes_decrypt(
                SocketHelper.recv_msg(self.client_socket))

        drawings = pickle.loads(data)
        for d in drawings:
            d.draw(self.canvas)
            self.drawings.append(d)

    def create_new_db(self, pwd):
        '''
            Creates a new database for the canvas.
        '''
        SocketHelper.send_msg(self.client_socket, pickle.dumps(
            ("create_new_db", sha256(pwd.encode()).hexdigest())))

    def receive_data(self, client_socket):
        '''Receives and processes data from the server.'''
        while self.window_open:
            try:
                # Set a timeout for the socket operation so it will know if the window is closed
                client_socket.settimeout(0.5)  # in seconds

                with self.receive_lock:
                    data = SocketHelper.recv_msg(client_socket)

                action, content = pickle.loads(data)
                print(f'action: {action}, content: {content}')

                if action == "new_line":
                    self.add_to_drawings(content)
                elif action == "new_rect" or action == "new_oval":
                    self.add_to_drawings(content)
                elif action == "delete":
                    self.delete_line(content)

            except socket.timeout:
                # Timeout occurred, check the window state
                if not self.window_open:
                    break
                continue

    def send_to_db(self, d):  # d - Drawing/Rect/Oval object
        '''Sends a new drawing to the server.'''
        # Define the data to be sent
        mode = ""
        if isinstance(d, Drawing):
            mode = "new_line"
        elif isinstance(d, Oval):
            mode = "new_oval"
        elif isinstance(d, Rect):
            mode = "new_rect"
        # print(data)

        data = pickle.dumps((mode, self.cipher.aes_encrypt(pickle.dumps(d))))
        SocketHelper.send_msg(self.client_socket, data)

    def add_to_drawings(self, drawing):
        '''Adds a new drawing to the list of drawings and draws it on the canvas.'''
        self.drawings.append(drawing)
        self.root.after(0, lambda: drawing.draw(self.canvas))

    def delete_line(self, id_, is_this_user=False):
        '''Removes a drawing from the list of drawings and deletes it.'''
        for d in self.drawings:
            if d.id == id_:
                self.drawings.remove(d)
                self.root.after(0, d.delete_from_canvas(self.canvas))

                if is_this_user:  # Only append drawing if it was deleted by this user
                    self.deleted_drawings.append(d)

                break

    def get_and_inc_id(self):
        '''Gets the current ID from the server and increments it.'''
        SocketHelper.send_msg(self.command_client_socket,
                              pickle.dumps(("get_and_inc_id", None)))
        id_ = int(SocketHelper.recv_msg(self.command_client_socket).decode())

        print("id from server:", id_)

        return id_

    def pick_color(self):
        # The first time the color picker is opened, the color picker will start with #50dca4, otherwise it will default to the last picked color
        if not self.color_changed:
            color = colorchooser.askcolor(
                title="Select Color", initialcolor="#50dca4")
            self.color_changed = True
        else:
            color = colorchooser.askcolor(
                title="Select Color", initialcolor=self.color)

        if color[1]:  # Check if a color was chosen
            chosen_color = color[1]
            self.color = chosen_color
            self.pick_color_b.config(background=chosen_color)

    def start_rect(self, event):
        width = int(self.line_width_entry.get())
        self.cur_drawing = Rect(self.color, width, event.x, event.y)
        self.cur_drawing.draw(self.canvas)

    def start_oval(self, event):
        width = int(self.line_width_entry.get())
        self.cur_drawing = Oval(self.color, width, event.x, event.y)
        self.cur_drawing.draw(self.canvas)

    def update_rect_oval(self, event):
        self.cur_drawing.update(event.x, event.y)
        self.cur_drawing.redraw(self.canvas)

    def mouse_pressed(self, event):
        if self.mode == "drawing":
            self.start_drawing(event)
        elif self.mode == "rect":
            self.start_rect(event)
        elif self.mode == "oval":
            self.start_oval(event)

    def mouse_pressed_moved(self, event):
        if self.mode == "drawing":
            self.draw(event)
        elif self.mode == "rect" or self.mode == "oval":
            self.update_rect_oval(event)

    def save_img(self):
        # Select file location and name
        file_path = filedialog.asksaveasfilename(initialdir="/", title="Select a file", filetypes=(
            ("PNG", "*.png"),), defaultextension=".png", initialfile=self.project_name+".png")
        if file_path == "":
            return

        # Create a new image
        image = Image.new("RGB", (800, 600), (255, 255, 255))

        # Create an ImageDraw object
        draw = ImageDraw.Draw(image)
        for drawing in self.drawings:
            if isinstance(drawing, Oval):
                x1 = min(drawing.x1, drawing.x2)
                x2 = max(drawing.x1, drawing.x2)
                y1 = min(drawing.y1, drawing.y2)
                y2 = max(drawing.y1, drawing.y2)
                draw.ellipse((x1, y1, x2, y2), width=drawing.width,
                             outline=drawing.color)
            elif isinstance(drawing, Rect):
                x1 = min(drawing.x1, drawing.x2)
                x2 = max(drawing.x1, drawing.x2)
                y1 = min(drawing.y1, drawing.y2)
                y2 = max(drawing.y1, drawing.y2)
                draw.rectangle((x1, y1, x2, y2),
                               width=drawing.width, outline=drawing.color)
            elif isinstance(drawing, Drawing):
                # draw.line(drawing.pt_list, fill=drawing.color, width=drawing.width)
                drawing.draw_PIL(draw)

        # Save the image to the computer
        image.save(file_path)


class SelectProjectGUI:
    def __init__(self):
        self.init_connection_to_server()

        # self.dir = r'C:\Users\hp\Desktop\Freeform project\projects (db)\\'
        SocketHelper.send_msg(self.client_socket, pickle.dumps(
            ("get_projects_names", None)))
        # files = pickle.loads(self.client_socket.recv(2048))
        self.db_files = pickle.loads(SocketHelper.recv_msg(self.client_socket))

        self.root = tk.Tk()
        self.root.geometry("400x400")
        self.root.title("Select project")

        tk.Button(text="START NEW PROJECT",
                  command=self.new_project).pack(pady=20)

        for file in self.db_files:
            tk.Button(
                text=file, command=lambda name=file: self.open_project(name)).pack()

        self.root.mainloop()

    def open_project(self, name):
        self.root.destroy()

        # file = self.dir + file_name
        # SocketHelper.send_msg(self.client_socket,
        #                       pickle.dumps(("set_project_name", name)))
        # SocketHelper.send_msg(self.command_client_socket, name.encode())
        print(name)

        # CanvasGUI(self.client_socket, self.command_client_socket,
        #           name, self.shared_key, exists=True)

        EnterPasswordGUI(name, self.client_socket, self.command_client_socket, self.shared_key)



    def new_project(self):
        self.root.destroy()

        NewProjectGUI(self.client_socket, self.command_client_socket,
                      self.db_files, self.shared_key)

    def init_connection_to_server(self):
        hostname = 'localhost'

        self.client_socket = socket.socket()
        server_address = (hostname, 1729)
        self.client_socket.connect(server_address)

        self.command_client_socket = socket.socket()
        command_server_address = (hostname, 1730)
        self.command_client_socket.connect(command_server_address)

        # generate shared key
        dh, pk = Cipher.get_dh_public_key()
        self.client_socket.send(pk)
        reply = self.client_socket.recv(1024)
        self.shared_key = Cipher.get_dh_shared_key(dh, reply)

        print("shared key:", self.shared_key)

        print(f'Connected to server {server_address[0]}:{server_address[1]}')


class NewProjectGUI:
    def __init__(self, client_socket, command_client_socket, db_files, shared_key):
        self.client_socket = client_socket
        self.command_client_socket = command_client_socket
        self.db_files = db_files
        self.shared_key = shared_key

        # self.dir = r'C:\Users\hp\Desktop\Freeform project\projects (db)\\'
        self.root = tk.Tk()
        self.root.geometry("400x400")
        self.root.title("Start new project")
        # tk.Label(self.root, text="CREATE PROJECT").
        tk.Label(self.root, text="NAME:", padx=3).grid(row=0, column=0)
        self.name_entry = tk.Entry(self.root)
        self.name_entry.grid(row=0, column=1)
        tk.Label(self.root, text="PASSWORD:", padx=3).grid(row=1, column=0)
        self.pwd_entry = tk.Entry(self.root, show="*")
        self.pwd_entry.grid(row=1, column=1)
        tk.Button(text="CREATE", command=self.button_pressed).grid(row=2, column=1)

    def button_pressed(self):
        '''Opens an existing project by setting the project name and creating a new Canvas_GUI.'''
        name = self.name_entry.get()
        pwd = self.pwd_entry.get()
        if name not in self.db_files:
            self.root.destroy()
            SocketHelper.send_msg(self.client_socket,
                                  pickle.dumps(("set_project_name", name)))
            SocketHelper.send_msg(self.command_client_socket, name.encode())
            CanvasGUI(self.client_socket, self.command_client_socket,
                      name, self.shared_key, pwd, False)
        else:
            tk.Label(text="NAME ALREADY TAKEN, PLEASE TRY AGAIN").pack()

class EnterPasswordGUI:
    def __init__(self, name, client_socket, command_client_socket, shared_key):
        self.name = name
        self.client_socket = client_socket
        self.command_client_socket = command_client_socket
        self.shared_key = shared_key

        self.root = tk.Tk()
        self.root.geometry("400x400")
        self.root.title("Enter Password")
        tk.Label(self.root, text="ENTER PASSWORD:").pack()
        
        self.pwd_entry = tk.Entry(self.root, show="*")
        self.pwd_entry.pack()
        
        tk.Button(self.root, text="ENTER", command=self.button_pressed).pack()

        self.root.mainloop()

    def button_pressed(self):
        SocketHelper.send_msg(self.client_socket,
        pickle.dumps(("name_and_pwd", (self.name, sha256(self.pwd_entry.get().encode()).hexdigest()))))
        answer = SocketHelper.recv_msg(self.client_socket).decode()
        if answer == "success":
            self.root.destroy()
            SocketHelper.send_msg(self.command_client_socket, self.name.encode())
            CanvasGUI(self.client_socket, self.command_client_socket,
                   self.name, self.shared_key, exists=True)
        else:
            tk.Label(self.root, text="INCORRECT PASSWORD", fg="red").pack()

        # SocketHelper.send_msg(self.command_client_socket, name.encode())



# class Client:
#     def __init__(self):
#         self.socket = socket.socket()

#         server_address = ('localhost', 1730)
#         self.socket.connect(server_address)

#         print(f'Connected to server {server_address[0]}:{server_address[1]}')

#         receive_thread = threading.Thread(target=self.receive_data, args=(client_socket,))
#         receive_thread.start()

#     def recieve_data(self):
#         while True:
#             # Receive data from the server
#             data = self.socket.recv(1024).decode()
#             if data == "exit":
#                 break

#             # Print the received data
#             print('Received from server:', data)

#         # Close the client socket
#         self.socket.close()


if __name__ == "__main__":
    SelectProjectGUI()

# gui = Canvas_GUI("drawings.db", True)
