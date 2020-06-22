import random
import time
from socket import *
import sys
import select
import pickle
from threading import Thread


# Connection information
HOST = "127.0.0.1"
MY_PORT = 33332
BUFFER = 1024

ADDR = (HOST, MY_PORT)
my_socket = socket(AF_INET, SOCK_STREAM)
my_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
my_socket.bind(ADDR)
server_sockets = {}
sockets_list = [my_socket]
my_socket.listen(20)
elected_primaries = {}
given_primaries = {}
ACKED_MESSAGES = []


def ack_sent_message(message, server, is_delay=True):
    """
    Sends a message to the simulator, sends it until it acks the message
    Also, delays the message to simulate asynchronous environment
    :param message: The message to send
    :param server: The destination server
    :param is_delay: Is the message supposed to be delayed?
    :return: True when the message was acked
    """
    if is_delay:
        time.sleep(random.randint(1, 60))
    while True:
        time.sleep(0.5)
        if message in ACKED_MESSAGES:
            ACKED_MESSAGES.remove(message)
            return True
        else:
            server_sockets[server].send(pickle.dumps(message))


def get_primary(primaries_of_views, all_primaries, new_primary, new_view,
                needed_primaries):
    """
    Gets a primary and a view, and if enough primaries finished,
    it randomly selects a primary.
    If already a primary was selected, the method returns the primary selected
    :param primaries_of_views: for every view, which replica is the primary
    in this view
    :param all_primaries: all the primaries that finished in every view
    :param new_primary: the primary that finished
    :param new_view: the view it finished in
    :param needed_primaries: the number of primaries needed for a selection
    :return: True if a primary is selected, False otherwise
    """
    if new_view not in primaries_of_views:
        if new_view not in all_primaries:
            all_primaries[new_view] = [new_primary]
            return False
        if new_primary not in all_primaries[new_view]:
            all_primaries[new_view].append(new_primary)
            if len(all_primaries[new_view]) == needed_primaries:
                primaries_of_views[new_view] = random.choice(all_primaries[
                                                             new_view])
                return True
        return False
    else:
        return True


def listen_thread_func():
    while True:
        read_sockets, _, exception_sockets = select.select(sockets_list, [],
                                                           sockets_list)
        # Iterate over notified sockets
        for notified_socket in read_sockets:
            if notified_socket == my_socket:
                # Receiving a new connection
                new_socket, _ = my_socket.accept()
                sockets_list.append(new_socket)
                name = new_socket.recv(BUFFER).decode("utf8")
                try:
                    # If the connected is a server
                    new_server_id = int(name)
                    server_sockets[new_server_id] = new_socket
                    print("Connected to server " + str(new_server_id) + ".")
                except error as err:
                    # If the name was not a server id, there something wrong
                    print("Server id unrecognized. please try again")
            else:
                message = notified_socket.recv(BUFFER)
                try:
                    msg = pickle.loads(message)
                    # If we pickled, we received a true message
                    if msg[0] == "ack" or msg[0] == 'ack':
                        # the message needs an ack
                        ACKED_MESSAGES.append(msg[1])
                    else:
                        src = msg[0]
                        dest = msg[1]
                        try:
                            print("Received \"" + msg[2] + "\" message from "
                                  "replica " + str(src) + ", dest to " + str(
                                dest) + ".")
                        except:
                            print("replica " + str(src) + " asked for the "
                                  "primary in view " + str(msg[2]))
                        if src in server_sockets:
                            server_sockets[src].send(pickle.dumps(["ack", msg]))
                        if dest == -1:
                            if get_primary(elected_primaries, given_primaries,
                                           src, msg[2],
                                           len(server_sockets) - 1):
                                for server in server_sockets:
                                    message = [-1, server, "primary "
                                               "elected", msg[2],
                                               elected_primaries[msg[2]]]
                                    message_thread = Thread(
                                        target=ack_sent_message, args=(message,
                                                                       server,
                                                                       False))
                                    message_thread.start()
                        else:
                            message_thread = Thread(
                                target=ack_sent_message, args=(msg, dest))
                            message_thread.start()
                except:
                    # Can't pickle, so a server sent a client's name
                    # A server has sent a name, logged in or logged out
                    if len(message) > 0:
                        msg = message.decode("utf8").split()
                        if msg[-1] == "0":
                            # A client logged in
                            names = []
                            for server in server_sockets:
                                if server_sockets[server] != notified_socket:
                                    server_sockets[server].send(message)
                                    names += pickle.loads(server_sockets[server].recv(
                                        BUFFER))
                            notified_socket.send(pickle.dumps(names))
                        else:
                            # A client logged out
                            for server in server_sockets:
                                if server_sockets[server] != notified_socket:
                                    server_sockets[server].send(message)


def set_faulty():
    """
    runs a thread that switches the faulty server, simulating an adaptive
    advarsery.
    Switching the faulty server will happen every 5-10 minutes
    """
    faulty = -1
    while True:
        if len(server_sockets.keys()) > 0:
            print("selecting faulty")
            new_faulty = random.choice(list(server_sockets.keys()))
            if faulty != new_faulty:
                if faulty in server_sockets:
                    ack_sent_message("fixed", faulty, False)
                ack_sent_message("faulty", new_faulty, False)
                faulty = new_faulty
            seconds = (random.randint(1, 5) + 5)*30
            time.sleep(seconds)


# one thread running, creating each time sub threads
listen_thread = Thread(target=listen_thread_func)
listen_thread.start()
faulty_selector = Thread(target=set_faulty)
faulty_selector.start()
