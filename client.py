from drawing import Drawing
import tkinter as tk
# import sqlite3
# import os
import socket
import threading
import pickle
from pathlib import Path
import queue
# import time

class Canvas_GUI:
    def __init__(self, client_socket, file_name, exists = False):
        # self.dir = r'C:\Users\hp\Desktop\Freeform project\projects (db)\\'
        # self.file_name = file_name
        # self.full_path = self.dir + self.file_name

        self.client_socket = client_socket

        self.drawings = []
        self.deleted_drawings = []


        self.color = "black"
        self.target = -1 #setup for target

        self.root = tk.Tk()
        self.root.title("Drawing Application")

        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="white")
        self.canvas.pack()

        self.canvas.bind("<ButtonPress-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", lambda e: threading.Thread(target=self.end_drawing).start())
        
        self.canvas.bind("<Motion>", self.move_target)
        self.canvas.bind("<Leave>", self.hide_target)
        
        self.root.bind("<Control-z>", self.delete_last_drawing)
        self.root.bind("<Control-y>", self.redo_last_deleted_drawing)


        self.colors_frame = tk.Frame(self.root)
        self.colors_frame.pack()

        font = ("Arial", 18)
        tk.Button(self.colors_frame, text="BLACK",font=font, command = lambda: self.set_color("BLACK")).grid(row = 0, column = 0)
        tk.Button(self.colors_frame, text="BLUE",font=font, command = lambda: self.set_color("BLUE")).grid(row = 0, column = 1)
        tk.Button(self.colors_frame, text="RED",font=font, command = lambda: self.set_color("RED")).grid(row = 0, column = 2)
        tk.Button(self.colors_frame, text="ORANGE",font=font, command = lambda: self.set_color("ORANGE")).grid(row = 0, column = 3)


        vcmd = (self.root.register(self.width_entry_validation), "%P") #used to deal with validation in Tcl
        self.line_width_entry = tk.Entry(self.colors_frame, validate="all", validatecommand=vcmd, width=4, justify="center") # %P -> new value of entry box
        self.line_width_entry.grid(row=0,column=4)
        self.line_width_entry.insert(0, "10") # Sets starting width

        tk.Button(self.colors_frame, text="UNDO", font=font, command=self.delete_last_drawing).grid(row=0, column=6) # ↶
        tk.Button(self.colors_frame, text="REDO",font=font, command = self.redo_last_deleted_drawing).grid(row = 0, column = 7) # ↷


        # test_entry = tk.Entry(self.root)
        # self.canvas.create_window(200, 200, window=test_entry)


        # test_label = tk.Label(self.root, font=font, text= "HELLO")
        # self.root.wm_attributes('-transparentcolor', '#ab23ff')
        # self.canvas.create_window(200, 200, window=test_label)


        self.canvas.config(cursor="none")
        
        self.window_open = True # Used to cut the connection when the user closes the window
        
        self.receive_lock = threading.Lock()

        if(exists):
            self.load_canvas()
        else:
            self.create_new_db()

        receive_thread = threading.Thread(target=self.receive_data, args=(self.client_socket,))
        receive_thread.start()

        self.root.mainloop()

        self.window_open = False # Used to cut the connection when the user closes the window


    def start_drawing(self, event):
        '''
            Initializes a new drawing and creates an oval shape at the starting position of the mouse cursor.
        '''

        width = int(self.line_width_entry.get())

        self.deleted_drawings = [] # Clears the redo option

        self.prev_x, self.prev_y = event.x, event.y
        self.cur_drawing = Drawing(self.color, width)


        circle_off = width/2 - 1
        x1, y1 = (event.x - circle_off), (event.y - circle_off)
        x2, y2 = (event.x + circle_off), (event.y + circle_off)
        id = self.canvas.create_oval(x1, y1, x2, y2, fill=self.color, outline="")
        
        self.cur_drawing.add_point((event.x, event.y))
        self.cur_drawing.add_id(id)


    def draw(self, event):
        '''
        Creates a line between the previous and current position of the mouse cursor.
        '''

        self.move_target(event) # Deals with a bug where the target would update if the mouse i pressed

        width = int(self.line_width_entry.get())

        x, y = event.x, event.y
        id = self.canvas.create_line(self.prev_x, self.prev_y, x, y, fill=self.color, width=width)
        self.cur_drawing.add_id(id)
        self.prev_x, self.prev_y = x, y
        
        if (width > 3): # otherwise it looks weird
            circle_off = width/2 - 1 #offset, got to be slightly lower than width/2 so it wont buldge out
            x1, y1 = (event.x - circle_off), (event.y - circle_off)
            x2, y2 = (event.x + circle_off), (event.y + circle_off)
            id = self.canvas.create_oval(x1, y1, x2, y2, fill=self.color, outline="")
            self.cur_drawing.add_id(id)

        self.cur_drawing.add_point((x,y))

    def end_drawing(self, *_): #*_ to deal with event
        '''
            Assigns an ID to the current drawing, adds it to the list of drawings and sends it to the server.
        '''
        cur_id = self.get_and_inc_id()
        print("id:", cur_id)
        self.cur_drawing.id = cur_id

        self.drawings.append(self.cur_drawing)
        self.send_new_drawing(self.cur_drawing)        

    def hide_target(self, *_): #*_ to deal with event
        '''
            Hides the target shape indicating the area to be painted. (used when the mouse leaves the canvas)
        '''
        self.canvas.delete(self.target)
        self.target = -1

    def move_target(self, event):
        '''
            Updates the position of the target shape to follow the mouse cursor.
        '''
        if(self.target != -1):
            self.canvas.delete(self.target)
        circle_off = max(5/2, int(self.line_width_entry.get())/2)
        x1, y1 = (event.x - circle_off), (event.y - circle_off)
        x2, y2 = (event.x + circle_off), (event.y + circle_off)
        # self.target = self.canvas.create_oval(x1, y1, x2, y2, fill="", outline=self.color, dash=(2,1)) # shows the outline of the area you'd paint
        self.target = self.canvas.create_oval(x1, y1, x2, y2, fill="", outline=self.color) # shows the outline of the area you'd paint

    def set_color(self, color):
        '''
            Sets the color variable to the selected color.
        '''
        self.color = color

    def delete_last_drawing(self, *_): #*_ to deal with event if given   
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

            self.client_socket.send(pickle.dumps(("delete", id_)))
              
    def redo_last_deleted_drawing(self, *_): #*_ to deal with event if given
        '''
            Restores the last deleted drawing from the list of deleted drawings and redraws it on the canvas.
        '''
        if self.deleted_drawings:
            d = self.deleted_drawings.pop()
            self.drawings.append(d)
            d.draw_drawing(self.canvas)

            self.send_new_drawing(d)

            # self.save_row(d)

    def width_entry_validation(self, value):
        return value == "" or (value.isnumeric() and int(value) <= 45)


    def load_canvas(self):
        '''
            Loads drawings from the database and adds them to the canvas.
        '''
        self.client_socket.send(pickle.dumps(("load_canvas", None)))
        
        with self.receive_lock:
            CHUNK_SIZE = 1024
            data = b''
            while True:
                chunk = self.client_socket.recv(CHUNK_SIZE)
                data += chunk
                if len(chunk) < CHUNK_SIZE:
                    break

        drawings = pickle.loads(data)
        for d in drawings:
            d.draw_drawing(self.canvas)
            self.drawings.append(d)


    def create_new_db(self):
        '''
            Creates a new database for the canvas.
        '''
        self.client_socket.send(pickle.dumps(("create_new_db", None)))


    def receive_data(self, client_socket):
        '''Receives and processes data from the server.'''
        while self.window_open:
            try:
                # Set a timeout for the socket operation so it will know if the window is closed
                client_socket.settimeout(0.05)  # 0.1 second
                
                with self.receive_lock:
                    CHUNK_SIZE = 1024
                    data = b''
                    while True:
                        chunk = client_socket.recv(CHUNK_SIZE)
                        data += chunk
                        if len(chunk) < CHUNK_SIZE:
                            break
                
                action, content = pickle.loads(data)
                print("action:", action)
                print("content:", content)

                if action == "new_line":
                    self.add_to_drawings(content)
                elif action == "delete":
                    self.delete_line(content) 

            except socket.timeout:
                # Timeout occurred, check the window state
                if not self.window_open:
                    break
                continue


    def send_new_drawing(self, d): # d - Drawing object
        '''Sends a new drawing to the server.'''
        # Define the data to be sent
        data = pickle.dumps(("new_line", d))
        print(d)
        self.client_socket.sendall(data)
        # self.client_socket.sendall("hello my name is jeff im trying to make this string longer but its kinda hard to write a lot so im just writing bullshit until it gets past the chunk size did it get past the chunk size already who knows lets check".encode())


    def add_to_drawings(self, drawing):
        '''Adds a new drawing to the list of drawings and draws it on the canvas.'''
        self.drawings.append(drawing)
        drawing.draw_drawing(self.canvas)


    def delete_line(self, id_, is_this_user = False):
        '''Removes a drawing from the list of drawings and deletes it.'''
        for d in self.drawings:
            if d.id == id_:
                self.drawings.remove(d)
                d.delete_from_canvas(self.canvas)

                if is_this_user: #Only append drawing if it was deleted by this user
                    self.deleted_drawings.append(d)

                break

    def get_and_inc_id(self):
        '''Gets the current ID from the server and increments it.'''
        with self.receive_lock:
            self.client_socket.send(pickle.dumps(("get_and_inc_id", None)))
            id_ = int(self.client_socket.recv(1024).decode())

        print("id from server", id_)

        return id_






class Select_project_GUI:
    def __init__(self):
        self.init_connection_to_server()

        # self.dir = r'C:\Users\hp\Desktop\Freeform project\projects (db)\\'
        self.client_socket.send(pickle.dumps(("get_projects_names", None)))
        # files = pickle.loads(self.client_socket.recv(2048))
        self.db_files = pickle.loads(self.client_socket.recv(2048))
        
        self.root = tk.Tk()
        self.root.geometry("400x400")
        self.root.title("Select project")


        tk.Button(text = "START NEW PROJECT", command = self.new_project).pack(pady=20)

        for file in self.db_files:
            tk.Button(text = file.stem, command = lambda name=file: self.open_project(name)).pack()

        self.root.mainloop()


    def open_project(self, file_name):
        self.root.destroy()

        # file = self.dir + file_name
        self.client_socket.send(pickle.dumps(("set_project_name", file_name))) 

        Canvas_GUI(self.client_socket, file_name, True)

    def new_project(self):
        self.root.destroy()
        
        New_project_GUI(self.client_socket, self.db_files)
    
    def init_connection_to_server(self):
        self.client_socket = socket.socket()
        
        server_address = ('localhost', 1729)
        self.client_socket.connect(server_address)

        print(f'Connected to server {server_address[0]}:{server_address[1]}')

    





class New_project_GUI:
    def __init__(self, client_socket, db_files):
        self.client_socket = client_socket
        self.db_files = db_files

        # self.dir = r'C:\Users\hp\Desktop\Freeform project\projects (db)\\'
        self.root = tk.Tk()
        self.root.geometry("400x400")
        self.root.title("Start new project")
        tk.Label(self.root, text="PICK A NAME FOR YOUR PROJECT")
        self.entry = tk.Entry(self.root)
        self.entry.pack()
        tk.Button(text="CREATE", command=self.button_pressed).pack()


    def button_pressed(self):
        '''Opens an existing project by setting the project name and creating a new Canvas_GUI.'''
        name = self.entry.get() + ".db"
        if(name not in self.db_files):
            self.root.destroy()
            self.client_socket.send(pickle.dumps(("set_project_name", name))) 
            Canvas_GUI(self.client_socket, name, False)
        else:
            tk.Label(text="NAME ALREADY TAKEN, PLEASE TRY AGAIN").pack()



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
    Select_project_GUI()

# gui = Canvas_GUI("drawings.db", True)