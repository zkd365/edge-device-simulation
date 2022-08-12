import struct
import threading
import time


def recv_msg(c):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(4, c)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        # print("mes len", msglen)
    #print("length=", msglen)
    return recvall(msglen, c)


def recvall(n, c):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = c.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    #print(len(data))
    return data


def send_msg(c, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    c.sendall(msg)


class setInterval :
    def __init__(self,interval,action) :
        self.interval=interval
        self.action=action
        self.stopEvent=threading.Event()
        thread=threading.Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self) :
        nextTime=time.time()+self.interval
        while not self.stopEvent.wait(nextTime-time.time()) :
            nextTime+=self.interval
            self.action()

    def cancel(self) :
        self.stopEvent.set()
