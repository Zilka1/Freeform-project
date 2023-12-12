import struct
import pickle

class SocketHelper:
    def send_msg(socket, msg):
        # Prefix each message with a 4-byte length (network byte order)
        msg = struct.pack('>I', len(msg)) + msg
        socket.sendall(msg)

    def recv_msg(socket):
        # Read message length and unpack it into an integer
        raw_msglen = SocketHelper.recvall(socket, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return SocketHelper.recvall(socket, msglen)

    def recvall(socket, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < n:
            packet = socket.recv(n - len(data))
            # print(pickle.loads(packet))
            if not packet:
                return None
            data.extend(packet)
        return data