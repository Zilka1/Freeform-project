from drawing import Drawing
import tkinter as tk
import sqlite3
import os
import socket
import threading
import pickle

class Canvas_GUI:
    def __init__(self, file_name, exists = False):
        self.dir = r'C:\Users\hp\Desktop\Freeform project\projects (db)\\'
        self.file_name = file_name
        self.full_path = self.dir + self.file_name
        
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
        self.canvas.bind("<ButtonRelease-1>", self.end_drawing)
        
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

        delete_button = tk.Button(self.colors_frame, text="UNDO", font=font, command=self.delete_last_drawing) # ↶
        delete_button.grid(row = 0, column=5)

        tk.Button(self.colors_frame, text="REDO",font=font, command = self.redo_last_deleted_drawing).grid(row = 0, column = 7) # ↷

        # tk.Button(self.colors_frame, text="SAVE",font=font, command = self.save_canvas_sql).grid(row = 0, column = 8) # ↷
        # tk.Button(self.colors_frame, text="LOAD",font=font, command = self.load_canvas_sql).grid(row = 0, column = 9) # ↷


        # test_entry = tk.Entry(self.root)
        # self.canvas.create_window(200, 200, window=test_entry)


        # test_label = tk.Label(self.root, font=font, text= "HELLO")
        # self.root.wm_attributes('-transparentcolor', '#ab23ff')
        # self.canvas.create_window(200, 200, window=test_label)


        self.canvas.config(cursor="none")


        if(exists):
            self.load_canvas_sql()
        else:
            self.create_new_db()
        
        self.window_open = True # Used to cut the connection when the user closes the window
        self.init_connection_to_server()

        self.root.mainloop()

        self.window_open = False # Used to cut the connection when the user closes the window


    def start_drawing(self, event):
        width = int(self.line_width_entry.get())

        self.deleted_drawings = [] # Clears the redo option

        self.prev_x, self.prev_y = event.x, event.y
        self.cur_drawing = Drawing(self.canvas, self.color, width)


        circle_off = width/2 - 1
        x1, y1 = (event.x - circle_off), (event.y - circle_off)
        x2, y2 = (event.x + circle_off), (event.y + circle_off)
        id = self.canvas.create_oval(x1, y1, x2, y2, fill=self.color, outline="")
        
        self.cur_drawing.add_point((event.x, event.y))
        self.cur_drawing.add_id(id)


    def draw(self, event):
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

    def end_drawing(self, *args): #*args to deal with event
        cur_id = self.get_id_from_db()
        self.cur_drawing.id = cur_id

        self.drawings.append(self.cur_drawing)
        self.send_new_drawing(self.cur_drawing)
        self.save_row(self.cur_drawing)


        self.inc_id()
        

    def hide_target(self, *args): #*args to deal with event
        self.canvas.delete(self.target)
        self.target = -1

    def move_target(self, event):
        if(self.target != -1):
            self.canvas.delete(self.target)
        circle_off = max(5/2, int(self.line_width_entry.get())/2)
        x1, y1 = (event.x - circle_off), (event.y - circle_off)
        x2, y2 = (event.x + circle_off), (event.y + circle_off)
        # self.target = self.canvas.create_oval(x1, y1, x2, y2, fill="", outline=self.color, dash=(2,1)) # shows the outline of the area you'd paint
        self.target = self.canvas.create_oval(x1, y1, x2, y2, fill="", outline=self.color) # shows the outline of the area you'd paint

    def set_color(self, color):
        self.color = color

    def delete_last_drawing(self, *args): #*args to deal with event if given   
        if self.drawings:
            d = self.drawings.pop()
            d.delete_from_canvas()
            self.deleted_drawings.append(d)

            # init connection to db
            conn = sqlite3.connect(self.full_path)
            c = conn.cursor()

            # get highest id
            c.execute('SELECT id FROM drawings ORDER BY id DESC LIMIT 1')
            id_ = c.fetchone()[0]

            print("id", id_)

            #delete from db
            c.execute('DELETE FROM drawings WHERE id = ?', [id_])

            conn.commit()
            conn.close()

            self.client_socket.send(("delete " + str(id_)).encode())
              
    def redo_last_deleted_drawing(self, *args): #*args to deal with event if given
        if self.deleted_drawings:
            d = self.deleted_drawings.pop()
            self.drawings.append(d)
            d.draw_drawing()

            self.save_row(d)

    def width_entry_validation(self, value):
        return value == "" or (value.isnumeric() and int(value) <= 45)


    # def save_canvas_sql(self):
    #     conn = sqlite3.connect(self.full_path)
    #     c = conn.cursor()

    #     c.execute('DROP TABLE IF EXISTS drawings')  # Drop the table

    #     c.execute('CREATE TABLE IF NOT EXISTS drawings (color TEXT, width INTEGER, pt_list TEXT)')

    #     for d in self.drawings:
    #         self.save_row(d)

    #     conn.commit()
    #     conn.close()


    def load_canvas_sql(self):
        conn = sqlite3.connect(self.full_path)
        c = conn.cursor()

        c.execute('SELECT * FROM drawings')

        for row in c.fetchall():
            id = row[0]
            color = row[1]
            width = row[2]
            pt_list = row[3]

            d = Drawing(self.canvas, color, width, eval(pt_list), id)
            d.draw_drawing()
            self.drawings.append(d)

        conn.close()


    def create_new_db(self):
        conn = sqlite3.connect(self.full_path)
        c = conn.cursor()

        #                                 
        c.execute('CREATE TABLE drawings (id INTERGER, color TEXT, width INTEGER, pt_list TEXT)')
        c.execute('CREATE TABLE variables (name TEXT, value INTEGER)')
        c.execute('INSERT INTO variables VALUES (?, ?)', ("id", 0))

        conn.commit()
        conn.close()


    def save_row(self, d): #d is a Drawing object
        conn = sqlite3.connect(self.full_path)
        c = conn.cursor()
        c.execute('INSERT INTO drawings VALUES (?, ?, ?, ?)', (d.id, d.color, d.width, str(d.pt_list)))

        conn.commit()
        conn.close()


    def init_connection_to_server(self):
        self.client_socket = socket.socket()
        
        server_address = ('localhost', 1729)
        self.client_socket.connect(server_address)

        print(f'Connected to server {server_address[0]}:{server_address[1]}')

        receive_thread = threading.Thread(target=self.receive_data, args=(self.client_socket,))
        receive_thread.start()


    def receive_data(self, client_socket):
        while self.window_open:
            try:
                # Set a timeout for the socket operation so it will know if the window is close
                client_socket.settimeout(1)  # 1 second
                
                action = client_socket.recv(1024).decode()

                if action == "new_line":
                    self.new_line()
                elif action.split()[0] == "delete":
                    self.delete_line(int(action.split()[1])) 
                

            except socket.timeout:
                # Timeout occurred, check the window state
                if not self.window_open:
                    break
                continue

    def get_id_from_db(self):
        conn = sqlite3.connect(self.full_path)
        c = conn.cursor()

        c.execute('SELECT * FROM variables')

        id_ = c.fetchall()[0][1]


        c.close()
        conn.close()


        # print(id_)
        return id_


    def inc_id(self):
        conn = sqlite3.connect(self.full_path)
        c = conn.cursor()

        inc_cmd = '''
            UPDATE variables
            SET value = ? '''
        
        c.execute(inc_cmd, (self.get_id_from_db()+1,))
        conn.commit()

        c.close()
        conn.close()


    def send_new_drawing(self, d): # d - Drawing object
        # Define the data to be sent
        data = pickle.dumps((d.id, d.color, d.width, d.pt_list))

        self.client_socket.send("new_line".encode())
        self.client_socket.sendall(data)
        # self.client_socket.sendall("hello my name is jeff im trying to make this string longer but its kinda hard to write a lot so im just writing bullshit until it gets past the chunk size did it get past the chunk size already who knows lets check".encode())


    def new_line(self):
        CHUNK_SIZE = 1024
        data = b''
        while True:
            chunk = self.client_socket.recv(CHUNK_SIZE)
            data += chunk
            if len(chunk) < CHUNK_SIZE:
                break
        
        d_tuple = pickle.loads(data)

        id_, color, width, pt_list = d_tuple

        drawing = Drawing(self.canvas, color=color, id=id_, width=width, pt_list=pt_list)

        self.drawings.append(drawing)
        drawing.draw_drawing()


    def delete_line(self, id_):
        for d in self.drawings:
            print("checking drawing")
            if d.id == id_:
                print("this drawing")

                self.drawings.remove(d)
                d.delete_from_canvas()
                self.deleted_drawings.append(d)

                # conn = sqlite3.connect(self.full_path)
                # c = conn.cursor()

                # c.execute('DELETE FROM drawings WHERE id = ?', [id_])

                # conn.commit()
                # conn.close()

                break

    # def print_table(self):
    #     conn = sqlite3.connect(self.full_path)
    #     c = conn.cursor()

    #     with conn:
    #         c.execute("SELECT * FROM drawings")
    #         print(c.fetchall())

    #     c.close()






class Select_project_GUI:
    def __init__(self):
        self.dir = r'C:\Users\hp\Desktop\Freeform project\projects (db)\\'
        files = os.listdir(self.dir)
        db_files = list(filter(self.is_db_file, files))
        
        self.root = tk.Tk()
        self.root.geometry("400x400")
        self.root.title("Select project")


        tk.Button(text = "START NEW PROJECT", command = self.new_project).pack(pady=20)

        for f in db_files:
            tk.Button(text = f, command = lambda name=f: self.open_project(name)).pack()

        self.root.mainloop()


    def is_db_file(self, file):
        return file[-3:] == ".db" #checks the last 3 characters in the string

    def open_project(self, file_name):
        self.root.destroy()

        # file = self.dir + file_name
        
        Canvas_GUI(file_name, True)

    def new_project(self):
        self.root.destroy()
        
        New_project_GUI()

    





class New_project_GUI:
    def __init__(self):
        self.dir = r'C:\Users\hp\Desktop\Freeform project\projects (db)\\'
        self.root = tk.Tk()
        self.root.geometry("400x400")
        self.root.title("Start new project")
        tk.Label(self.root, text="PICK A NAME FOR YOUR PROJECT")
        self.entry = tk.Entry(self.root)
        self.entry.pack()
        tk.Button(text="CREATE", command=self.button_pressed).pack()


    def button_pressed(self):
        name = self.entry.get() + ".db"
        if(name not in os.listdir(self.dir)):
            self.root.destroy()
            Canvas_GUI(name, False)
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