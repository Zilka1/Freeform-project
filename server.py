#Make a list of clients - DONE
#When data is received, update the db and send the data to all clients beside the client that sent the data - 1/2
#Choose project to work on through the server
#   Send the client only the names of the files, and when they choose a file send them all of it
#Clients will not edit the db they receive, it's only for initalization
#Clients need to handle getting data from the server and implementing it
#
#Need to add IDs to the drawings in the db

from drawing import Drawing
import socket
import threading
import pickle
import sqlite3
import time

class Client:
    def __init__(self, socket, address, project=None): #needs project parameter
        self.socket = socket
        self.address = address
        self.project = project

    def print_connection(self):
        print(f'Client connected: {self.address[0]}:{self.address[1]}')
    
    def close(self):
        socket.close()

    def set_project(self, project_name):
        self.project = project_name
        self.path = r'C:\Users\hp\Desktop\Freeform project\projects (db)\\' + self.project

# Example usage:
# client = Client(socket, address)
# project_name = "Project1"
# set_project(client, project_name)
    

        
class Server:
    def __init__(self):
        self.client_list = []

        server_socket = socket.socket()
        
        server_address = ("localhost", 1729)
        server_socket.bind(server_address)
        
        server_socket.listen(100)
        
        print(f'Server started. Listening on {server_address[0]}:{server_address[1]}')
        

        # Handle new connections
        while True:
            # Accept a client connection
            client_socket, client_address = server_socket.accept()

            new_client = Client(client_socket, client_address)
            self.client_list.append(new_client)
            new_client.print_connection()

            # for c in self.client_list:
            #     print(c.address)
            

            # Create a new thread to handle the client
            client_thread = threading.Thread(target=self.handle_client, args=(new_client,))
            client_thread.start()
    
    
    def handle_client(self, client):
        while True:
            try:
                if client.project == None:
                    project_name = client.socket.recv(1024).decode()
                    client.set_project(project_name)


                # data = b'' + client.socket.recv(1024)

                CHUNK_SIZE = 1024
                data = b''
                while True:
                    chunk = client.socket.recv(CHUNK_SIZE)
                    data += chunk
                    if len(chunk) < CHUNK_SIZE:
                        break
                
                action, content = pickle.loads(data)


                print("action:", action)
                print("content:", content)

                if action == "new_line":
                    self.new_line(client, content)
                elif action.split()[0] == "delete":
                    self.delete_line(client, content) #client, id
                elif action == "get_and_inc_id":
                    self.get_and_inc_id(client)
                # elif action == "get_id":
                #     self.send_id(client)
                # elif action == "inc_id":
                #     self.inc_id(client)
                
                
                
            except Exception as e:
                # ... PRINT THE ERROR MESSAGE ... #
                print(e)
                print("couldnt get data from client")
                break
        
        # Close the client socket
        client.socket.close()
        self.client_list.remove(client)


        # print("clients:")
        # for c in self.client_list:
        #     print(c.address)


    def new_line(self, client, d): # d - Drawing object
        # Update DB
        conn = sqlite3.connect(client.path)
        c = conn.cursor()
        c.execute('INSERT INTO drawings VALUES (?, ?, ?, ?)', (d.id, d.color, d.width, str(d.pt_list)))

        conn.commit()
        conn.close()

        # Send to other clients
        for c in self.client_list:
            if (c != client and c.project == client.project):
                c.socket.send("new_line".encode())
                time.sleep(0.01) # Solves TCP timing
                c.socket.send(pickle.dumps(d))



        

    def delete_line(self, client, id_):
        # Delete from db
        conn = sqlite3.connect(client.path)
        c = conn.cursor()
        c.execute('DELETE FROM drawings WHERE id = ?', [id_])

        conn.commit()
        conn.close()

        for c in self.client_list:
            if (c != client and c.project == client.project):
                c.socket.send(("delete " + str(id_)).encode())


    # def get_id_from_db(self, client):
    #     conn = sqlite3.connect(client.path)
    #     c = conn.cursor()

    #     c.execute('SELECT * FROM variables')

    #     id_ = c.fetchall()[0][1]


    #     c.close()
    #     conn.close()

    #     # client.socket.send(str(id_).encode())

    #     return id_


    #     # print(id_)
    #     # return id_
    
    # def inc_id(self, client):
    #     cur_id = self.get_id_from_db(client)

    #     print(cur_id)

    #     conn = sqlite3.connect(client.path)
    #     c = conn.cursor()

    #     inc_cmd = '''
    #         UPDATE variables
    #         SET value = ? '''
        
    #     c.execute(inc_cmd, (cur_id+1,))
    #     conn.commit()

    #     c.close()
    #     conn.close()

    # def send_id(self, client):
    #     client.socket.send(str(self.get_id_from_db(client)).encode())

    def get_and_inc_id(self, client):
        conn = sqlite3.connect(client.path)
        c = conn.cursor()

        c.execute('SELECT * FROM variables')

        id_ = c.fetchall()[0][1]

        print(id_)

        client.socket.send(str(id_).encode())

        inc_cmd = '''
            UPDATE variables
            SET value = ? '''
        
        c.execute(inc_cmd, (id_+1,))
        conn.commit()
        conn.close()

        

        # return id_

    

# Start the server
Server()