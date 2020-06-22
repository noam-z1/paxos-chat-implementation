from socket import *
import tkinter as tk
import ChatWindow
from pickle import *
import sys
from threading import Thread


def close():
    """
    Handles closing the Client
    :return:
    """
    msg = dumps([name, "quit\n"])
    client_socket.send(msg)
    client_socket.close()
    room.quit()


def receive():
    """Handles receiving of messages."""
    while True:
        try:
            socket_in = client_socket.recv(BUFFER)
        except OSError:  # Possibly client has left the chat.
            break
        try:
            msg = loads(socket_in)
            chat.receive_message(msg[1], msg[0])
        except PickleError:
            try:
                msg = socket_in.decode('utf-8')
                chat.receive_message(msg)
            finally:
                pass


def send(name, msg, event=None):  # event is passed by binders.
    """Handles sending of messages."""
    if msg == "quit\n":
        close()
    else:
        msg = dumps([name, msg])
        client_socket.send(msg)


name = sys.argv[1]
replica = sys.argv[2]
HOST = "127.0.0.1"
PORT = 33333
room = tk.Tk()
room.title("My Working Chat")
chat = ChatWindow.ChatWindow(room, name, send)

BUFFER = 1024
ADDR = (HOST, PORT + int(replica))

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
client_socket.connect(ADDR)
client_socket.send(bytes(name, "utf8"))

receive_thread = Thread(target=receive)
receive_thread.start()
room.protocol("WM_DELETE_WINDOW", close)

room.mainloop()
