#Make a list of clients
#When data is received, update the db and send the data to all clients beside the client that sent the data
#Choose project to work on through the server
#   Send the client only the names of the files, and when they choose a file send them all of it
#Clients will not edit the db they receive, it's only for initalization
#Clients need to handle getting data from the server and implementing it
#
#Need to add IDs to the drawings in the db


import socket
import threading

class Client:
    def __init__(self, socket, address):
        self.socket = socket
        self.address = address
    

        

def handle_client(client_socket):
    
    while True:
        try:
            data = client_socket.recv(1024).decode()
            print(data)
            if data == "exit":
                break
            
            client_socket.send(data.upper().encode())
            
        except:
            break
    
    # Close the client socket
    client_socket.close()

def start_server():
    server_socket = socket.socket()
    
    server_address = ("localhost", 1729)
    server_socket.bind(server_address)
    
    server_socket.listen(20)
    
    print(f'Server started. Listening on {server_address[0]}:{server_address[1]}')
    
    while True:
        # Accept a client connection
        client_socket, client_address = server_socket.accept()
        print(f'Client connected: {client_address[0]}:{client_address[1]}')
        
        # Create a new thread to handle the client
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

# Start the server
start_server()