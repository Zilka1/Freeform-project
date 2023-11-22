#Make a list of clients - DONE
#When data is received, update the db and send the data to all clients beside the client that sent the data - 1/2
#Choose project to work on through the server
#   Send the client only the names of the files, and when they choose a file send them all of it
#Clients will not edit the db they receive, it's only for initalization
#Clients need to handle getting data from the server and implementing it
#
#Need to add IDs to the drawings in the db


import socket
import threading

class Client:
    def __init__(self, socket, address): #needs project parameter
        self.socket = socket
        self.address = address

    def print_connection(self):
        print(f'Client connected: {self.address[0]}:{self.address[1]}')
    
    def close(self):
        socket.close()
    

        
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
            

            # Create a new thread to handle the client
            client_thread = threading.Thread(target=self.handle_client, args=(new_client,))
            client_thread.start()
    
    
    def handle_client(self, client):
        while True:
            try:
                data = client.socket.recv(1024).decode()
                print(data)
                if data == "exit":
                    break
                
                for c in self.client_list:
                    if c != client:
                        c.socket.send(data.upper().encode())
                
            except:
                break
        
        # Close the client socket
        client.socket.close()
        self.client_list.remove(client)


        # print("clients:")
        # for c in self.client_list:
        #     print(c.address)




    

# Start the server
Server()