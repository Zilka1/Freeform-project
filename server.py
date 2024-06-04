# Notes on some problems:
# client checks if new project name is valid based on the list it got before
# client receiving from server with threading lock can be problematic

from drawing import Drawing
from rect_oval import Rect, Oval
from socket_helper import SocketHelper
import socket
from pathlib import Path
import threading
import pickle
import sqlite3
# import os
# import time
from cipher import Cipher
from constants import NONCE

class Client:
    def __init__(self, socket, address, shared_key, project=None):
        self.dir = Path(r'C:\Users\hp\Desktop\Freeform project\projects (db)')
        
        self.socket = socket
        self.address = address
        self.shared_key = shared_key
        self.project = project
        
        self.cipher = Cipher(self.shared_key, NONCE)

    def print_connection(self):
        """Prints the client connection details."""
        print(f'Client connected to main server: {self.address[0]}:{self.address[1]}')
    
    def close(self):
        '''Closes the client connection.'''
        socket.close()

    def set_project(self, project_name):
        '''Assigns a project to the client'''
        self.project = project_name
        self.path = self.dir.joinpath(self.project).with_suffix('.db')
    
    def encrypt(self, msg):
        return self.cipher.aes_encrypt(msg)

    def decrypt(self, msg):
        return self.cipher.aes_decrypt(msg)
        

# Example usage:
# client = Client(socket, address)
# project_name = "Project1"
# set_project(client, project_name)
    

        
class MainServer:
    def __init__(self):
        """Initializes the Server object and starts listening for client connections."""
        self.client_list = []

        server_socket = socket.socket()
        
        server_address = ("0.0.0.0", 1729)
        server_socket.bind(server_address)
        
        server_socket.listen(100)
        
        print(f'Main server started. Listening on {server_address[0]}:{server_address[1]}')
        

        # Handle new connections
        while True:
            # Accept a client connection
            client_socket, client_address = server_socket.accept()


            #generate shared key
            dh, pk = Cipher.get_dh_public_key()
            client_pk = client_socket.recv(1024)
            shared_key = Cipher.get_dh_shared_key(dh, client_pk)
            print("shared key:", shared_key)
            client_socket.send(pk)

            new_client = Client(client_socket, client_address, shared_key)
            self.client_list.append(new_client)
            new_client.print_connection()

            # Create a new thread to handle the client
            client_thread = threading.Thread(target=self.handle_client, args=(new_client,))
            client_thread.start()
    
    
    def handle_client(self, client: Client):
        '''Handles a single client connection.'''
        while True:
            # try:
                # data = b'' + client.socket.recv(1024)

            data = SocketHelper.recv_msg(client.socket)
            
            if data is None:
                break

            action, content = pickle.loads(data)


            print(f'Client {client.address[0]}:{client.address[1]}: action: {action}, content: {content}')

            if action == "set_project_name":
                client.set_project(content)
            elif action == "get_projects_names":
                self.get_projects_names(client)
            elif action == "new_line":
                self.new_line(client, pickle.loads(client.decrypt(content)))
            elif action == "new_rect":
                self.new_rect_oval(client, pickle.loads(client.decrypt(content)), 'rect')
            elif action == "new_oval":
                self.new_rect_oval(client, pickle.loads(client.decrypt(content)), 'oval')
            elif action == "delete":
                self.delete_line(client, content) #client, id
            # elif action == "get_and_inc_id":
            #     self.get_and_inc_id(client)
            elif action == "create_new_db":
                self.create_new_db(client)
            elif action == "load_canvas":
                self.load_canvas_sql(client)

                # elif action == "get_id":
                #     self.send_id(client)
                # elif action == "inc_id":
                #     self.inc_id(client)
                
            # except ConnectionResetError:
            #     break
                
            # except Exception as e:
            #     # ... PRINT THE ERROR MESSAGE ... #
            #     print(e)
            #     # print("couldnt get data from client")
            #     break
        
        # Close the client socket
        print(f"Client disconnected: {client.address[0]}:{client.address[1]}")
        client.socket.close()
        self.client_list.remove(client)


        # print("clients:")
        # for c in self.client_list:
        #     print(c.address)


    def new_line(self, client, d): # d - Drawing object
        """Updates the database with a new drawing and sends it to other clients."""
        # Update DB
        conn = sqlite3.connect(client.path)
        c = conn.cursor()
        c.execute('INSERT INTO drawings VALUES (?, ?, ?, ?)', (d.id, d.color, d.width, str(d.pt_list)))

        conn.commit()
        conn.close()

        # Send to other clients
        for c in self.client_list:
            print(c.project)
            if (c != client and c.project == client.project):
                SocketHelper.send_msg(c.socket, pickle.dumps(("new_line", d)))



        

    def delete_line(self, client, id_):
        """Deletes a drawing from the database and sends a delete message to other clients."""
        # Delete from db
        conn = sqlite3.connect(client.path)
        c = conn.cursor()

        # Delete from either table
        c.execute('DELETE FROM drawings WHERE id = ?', (id_,))
        c.execute('DELETE FROM rects WHERE id = ?', (id_,))
        c.execute('DELETE FROM ovals WHERE id = ?', (id_,))

        conn.commit()
        conn.close()

        for c in self.client_list:
            if (c != client and c.project == client.project):
                SocketHelper.send_msg(c.socket, pickle.dumps(("delete", id_)))




    def create_new_db(self, client):
        '''Initializes a new database'''
        conn = sqlite3.connect(client.path)
        c = conn.cursor()

        c.execute('CREATE TABLE drawings (id INTERGER PRIMARY KEY, color TEXT, width INTEGER, pt_list TEXT)')
        c.execute('CREATE TABLE rects (id INTERGER PRIMARY KEY, color TEXT, width INTEGER, x1 INTEGER, y1 INTEGER, x2 INTEGER, y2 INTEGER)')
        c.execute('CREATE TABLE ovals (id INTERGER PRIMARY KEY, color TEXT, width INTEGER, x1 INTEGER, y1 INTEGER, x2 INTEGER, y2 INTEGER)')
        c.execute('CREATE TABLE int_variables (name TEXT, value INTEGER)')
        c.execute('INSERT INTO int_variables VALUES (?, ?)', ("id", 0))

        conn.commit()
        conn.close()
    
    def load_canvas_sql(self, client: Client):
        """Gets the current ID from the database, sends it to the client, and increments the ID."""
        print(f"path:{client.path}, project:{client.project}")
        conn = sqlite3.connect(client.path)
        c = conn.cursor()

        c.execute('SELECT * FROM drawings')

        drawings = []

        for row in c.fetchall():
            id = row[0]
            color = row[1]
            width = row[2]
            pt_list = row[3]

            d = Drawing(color, width, eval(pt_list), id)
            drawings.append(d)


        c.execute('SELECT * FROM rects')

        for row in c.fetchall():
            id = row[0]
            color = row[1]
            width = row[2]
            x1 = row[3]
            y1 = row[4]
            x2 = row[5]
            y2 = row[6]
            
            r = Rect(color, width, x1, y1, x2, y2, id)
            drawings.append(r)

        c.execute('SELECT * FROM ovals')
        for row in c.fetchall():
            id = row[0]
            color = row[1]
            width = row[2]
            x1 = row[3]
            y1 = row[4]
            x2 = row[5]
            y2 = row[6]
            
            r = Oval(color, width, x1, y1, x2, y2, id)
            drawings.append(r)

        drawings.sort(key = lambda d: d.id)
        SocketHelper.send_msg(client.socket, client.encrypt(pickle.dumps(drawings)))

        conn.close()

    # def is_db_file(self, file):
    #     return file.suffix == ".db" #checks the last 3 characters in the string

    def get_projects_names(self, client):
        """Gets a list of project names from the directory and sends it to the client."""
        
        files = Path.iterdir(client.dir)
        # db_files = list(filter(self.is_db_file, files))
        db_files = [file.stem for file in files if file.suffix == ".db"] # Filter the db files
        print(db_files)

        SocketHelper.send_msg(client.socket, pickle.dumps(db_files))

    def new_rect_oval(self, client, obj: Rect|Oval, type_):
        """Updates the database with a new drawing and sends it to other clients."""
        # Update DB
        conn = sqlite3.connect(client.path)
        c = conn.cursor()
        
        c.execute(f'INSERT INTO {type_}s VALUES (?,?,?,?,?,?,?)', (obj.id, obj.color, obj.width, obj.x1, obj.y1, obj.x2, obj.y2))

        conn.commit()
        conn.close()

        # Send to other clients
        for c in self.client_list:
            if (c!= client and c.project == client.project):
                SocketHelper.send_msg(c.socket, pickle.dumps((f"new_{type_}", obj)))




class CommandServer():
    def __init__(self):
        """Initializes the Server object and starts listening for client connections."""
        # self.client_list = []

        server_socket = socket.socket()
        
        server_address = ("0.0.0.0", 1730)
        server_socket.bind(server_address)
        
        server_socket.listen(100)
        
        print(f'Command server started. Listening on {server_address[0]}:{server_address[1]}')
        

        # Handle new connections
        while True:
            # Accept a client connection
            client_socket, client_address = server_socket.accept()

            print(f'Client connected to command server: {client_address[0]}:{client_address[1]}')

            
            # project_path = client_socket.recv(1024).decode()

            # dir = Path(r'C:\Users\hp\Desktop\Freeform project\projects (db)')
            
            # project_path = dir.joinpath(project_name)

            # print("set project:", project_path)

            # Create a new thread to handle the client
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()
        

    def handle_client(self, client_socket):
        '''Handles a single client connection.'''
        data = SocketHelper.recv_msg(client_socket)
        if data is None:
            client_socket.close()
            return
        
        dir = Path(r'C:\Users\hp\Desktop\Freeform project\projects (db)')
        project_name = data.decode()
        project_path = dir.joinpath(project_name).with_suffix('.db')

        print("COMMAND SERVER:", project_path)
        while True:
            data = SocketHelper.recv_msg(client_socket)
            if data is None:
                break

            action, content = pickle.loads(data)
            print(f"COMMAND SERVER: action: {action}, content: {content}")
            
            if action == "get_and_inc_id":
                self.get_and_inc_id(client_socket, project_path)
        
        client_socket.close()
        # self.client_list.remove(client_socket)

    
    def get_and_inc_id(self, client_socket, project_path):
        """Gets the current ID from the database, sends it to the client, and increments the ID."""
        print(project_path)
        conn = sqlite3.connect(project_path)
        c = conn.cursor()

        c.execute('SELECT value FROM int_variables WHERE name = "id"')

        id_ = c.fetchone()[0]

        # print(id_)

        SocketHelper.send_msg(client_socket, str(id_).encode())

        inc_cmd = '''
            UPDATE int_variables
            SET value = ?
            WHERE name = "id"'''
        
        c.execute(inc_cmd, (id_+1,))
        conn.commit()
        conn.close()
    
    

if __name__ == "__main__":
    # Start the server
    t1 = threading.Thread(target=lambda: MainServer())
    t1.start()
    threading.Thread(target=lambda: CommandServer()).start()
    t1.join()