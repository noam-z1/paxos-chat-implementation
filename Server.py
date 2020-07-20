import random
import time
from socket import *
import sys
import select
import pickle
from threading import Thread


# Connection information
HOST = "127.0.0.1"
START_PORT = 33333
SIMULATOR_PORT = 33332
BUFFER = 1024

# Server information
REPLICA_ID = int(sys.argv[1])
VALUES = []  # messages from client
messages_queue = []  # messages from other servers
current_view = 0
view_status = 0
# what status is the primary in, Of: 0 - pre-val,
# 0 - ask for values, 1 -  before purpose, 2 - waiting for answers,
# 3 - commit, 4 - done,
# 5 - get the selected primary
current_values = {}
NUM_OF_REPLICAS = 3
ACKS_THREADS = []
ACKED_MESSAGES = []
global are_clients_connected

ADDR = (HOST, START_PORT + REPLICA_ID)
my_socket = socket(AF_INET, SOCK_STREAM)
my_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
my_socket.bind(ADDR)

simulator_socket = socket(AF_INET, SOCK_STREAM)
simulator_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
sockets_list = [my_socket]
client_sockets = {}
my_socket.listen(10)

# Try connecting to the environment simulator
try:
    simulator_socket.connect((HOST, SIMULATOR_PORT))
    simulator_socket.send(bytes(str(REPLICA_ID), "utf8"))
    print("Connected to the \"Web\".")
    sockets_list.append(simulator_socket)
    are_clients_connected = False
except error as err:
    print("Unable to connect. Try again")
    sys.exit(0)


def timer_5_minutes():
    """
    A timer that checks every 5 minutes, and updates a variable
    :return:
    """
    global is_check
    while True:
        time.sleep(300)
        is_check = True


def ack_sent_message(message):
    """
    Sends a message to the simulator, sends it until it acks the message
    :param message: The message to send
    :return: True when the message was acked
    """
    while True:
        if message in ACKED_MESSAGES:
            ACKED_MESSAGES.remove(message)
            return True
        else:
            simulator_socket.send(pickle.dumps(message))
            time.sleep(0.5)


def notify_client_log_in(name, is_mine):
    """
    Notify the other chat clients with the new connected client
    :param name: The new client's name
    :param is_mine: is it connected to my server
    :return: all the names of my connected servers
    """
    names = []
    newly_con_msg = "Client " + name + " joined the chat!\n"
    if is_mine:
        if len(client_sockets) > 0:
            for socket_name in client_sockets:
                if name != socket_name:
                    client_sockets[socket_name].send(bytes(newly_con_msg,
                                                           "utf8"))
                    names.append(socket_name)
    else:
        for socket_name in client_sockets:
            client_sockets[socket_name].send(bytes(newly_con_msg, "utf8"))
            names.append(socket_name)
    return names


def notify_client_log_out(name, is_mine):
    """
    Notify the other chat clients about the disconnected client
    :param name: The client's name
    :param is_mine: is it connected to my server
    """
    newly_dis_msg = "Client " + name + " disconnected!\n"
    if is_mine:
        if len(client_sockets) > 0:
            for socket_name in client_sockets:
                client_sockets[socket_name].send(
                    bytes(newly_dis_msg, "utf8"))
    else:
        for socket_name in client_sockets:
            client_sockets[socket_name].send(
                bytes(newly_dis_msg, "utf8"))


def receive_messages():
    """
    A method that handles receiving messages
    """
    global are_clients_connected
    while True:
        read_sockets, _, exception_sockets = select.select(sockets_list, [],
                                                           sockets_list)
        # Iterate over notified sockets
        for notified_socket in read_sockets:
            if notified_socket == my_socket:
                # Receiving a new connection from a client
                new_socket, _ = my_socket.accept()
                sockets_list.append(new_socket)
                name = new_socket.recv(BUFFER).decode("utf8")
                client_sockets[name] = new_socket
                are_clients_connected = True
                names = notify_client_log_in(name, True)
                simulator_socket.send(bytes(name + " 0", "utf8"))
                names += pickle.loads(simulator_socket.recv(BUFFER))
                if len(names) > 0:
                    already_con_msg = "Client"
                    if len(names) > 1:
                        already_con_msg += "s"
                    already_con_msg += " "
                    for name in names:
                        already_con_msg += name + ", "
                    already_con_msg = already_con_msg[:-2]
                    if len(names) > 1:
                        already_con_msg += " are"
                    else:
                        already_con_msg += " is"
                    already_con_msg += " already connected. You can " \
                                       "chat!\n"
                else:
                    already_con_msg = "No other clients connected. wait " \
                                      "for some others!\n"
                new_socket.send(bytes(already_con_msg, "utf8"))
            else:
                # An established connection sent a message
                message = notified_socket.recv(BUFFER)
                if notified_socket == simulator_socket:
                    # A message from the simulator
                    try:
                        msg = pickle.loads(message)
                        # If we pickled, we received a true message
                        if msg[0] == 'ack' or msg[0] == "ack":
                            ACKED_MESSAGES.append(msg[1])
                        else:
                            simulator_socket.send(pickle.dumps(["ack", msg]))
                            messages_queue.append(msg)
                    except pickle.UnpicklingError as err:
                        # Can't pickle, not a regular message
                        msg = message.decode("utf8").split()
                        # It's a message about a client
                        name = msg[0]
                        if msg[-1] == "0":
                            # A client logged in
                            are_clients_connected = True
                            names = notify_client_log_in(name, False)
                            notified_socket.send(pickle.dumps(names))
                        else:
                            # A client logged out
                            notify_client_log_out(name, False)
                else:
                    # A regular message from a client
                    try:
                        msg = pickle.loads(message)
                    except error as err:
                        # couldn't pickle, something happened
                        print("An error occured.")
                        sys.exit(0)
                    if msg[1] == "quit\n":
                        name = msg[0]
                        sockets_list.remove(notified_socket)
                        del client_sockets[name]
                        notify_client_log_out(name, True)
                        simulator_socket.send(bytes(name + " 1", "utf8"))
                        print("Closed connection from: ", name)
                        if len(client_sockets) == 0:
                                print("End of conversation. Bye!")
                                my_socket.close()
                                sys.exit(0)
                    else:
                        VALUES.append(message)


def paxos_protocol(curr_values, messages, curr_view, status):
    """
    A method implementing Paxos protocol against adaptive adversary
    :param curr_values: The value to purpose on the current view
    :param messages: A set of messages
    :param curr_view: A dictionary of all the primaries VALUES in the
    current view
    :param status: The state of the protocol(as mentioned above in the code)
    """

    # message format - source id, destination id, type of message, view,
    # value(if there is a value)

    value_acks = set()
    commit_acks = set()
    done_acks = set()
    sent_messages = False
    global is_check
    prev_status = {'view': 0, 'status': 0}
    Thread(target=timer_5_minutes).start()

    while True:
        if are_clients_connected:

            if is_check:
                # check every 5 minutes if you are in the same status. If
                # so, go back to the previous status and resend some messages
                if prev_status['view'] == curr_view and prev_status[
                                                        'status'] == status:
                    print("checked, same place")
                    if REPLICA_ID not in curr_values:
                        status = 0
                        sent_messages = False
                    elif status == 4:
                        # resending done messages
                        for i in range(NUM_OF_REPLICAS):
                            print("sent done to " + str(i))
                            message = [([REPLICA_ID, i, "done", curr_view,
                                         curr_values[REPLICA_ID]])]
                            Thread(target=ack_sent_message,
                                   args=message).start()
                    elif status == 3:
                        # resending commit values messages
                        for i in range(NUM_OF_REPLICAS):
                            print("sent \"commit value\" to " + str(i))
                            message = [([REPLICA_ID, i, "commit value",
                                         curr_view, curr_values[REPLICA_ID]])]
                            Thread(target=ack_sent_message,
                                   args=message).start()
                    else:
                        # status is 2:
                        status = 1
                prev_status['view'] = curr_view
                prev_status['status'] = status
                is_check = False

            # check if you are in the current view, and if not,
            # act accordingly(delete previous messages\proceed to current view)
            highest_view = curr_view
            for in_message in messages:
                if in_message[3] > highest_view:
                    highest_view = in_message[3]
            if highest_view > curr_view:
                # asking for the new primary, in any case
                out_message = [([REPLICA_ID, -1, curr_view])]
                print("asked for the selected replica")
                Thread(target=ack_sent_message,
                       args=out_message).start()

                # if we moved to the next view, delete all the messages from
                # previous views
                to_remove = []
                for message in messages:
                    if message[3] < highest_view:
                        if not(message[0] == -1 and message[3] == message[3]):
                            # keep the messages that represent the replica
                            to_remove.append(message)
                if highest_view > curr_view:
                    status = 5

            if status == 0:
                if REPLICA_ID not in curr_values:
                    # getting a current value to send to other servers
                    if len(VALUES) > 0:
                        curr_values[REPLICA_ID] = VALUES[0]
                        VALUES.pop(0)
                        status = 1
                        print("Chose a value", curr_values[REPLICA_ID])
                    else:
                        messages_view = -1
                        for in_message in messages:
                            if in_message[2] == 'my propose':
                                if in_message[3] >= messages_view:
                                    messages_view = in_message[3]
                                    curr_values[REPLICA_ID] = in_message[4]
                                    status = 1
                                    print("Chose a value", curr_values[REPLICA_ID])
                                messages.remove(in_message)
                # send the a value ask message, only be sent once
                if not sent_messages and REPLICA_ID not in curr_values:
                    for i in range(NUM_OF_REPLICAS):
                        if i != REPLICA_ID:
                            print(REPLICA_ID, " asking for a value ", i)
                            message = [([REPLICA_ID, i, "value ask",
                                         curr_view])]
                            Thread(target=ack_sent_message,
                                   args=message).start()
                    sent_messages = True
            if status > 0:
                # after you have a value and someone asks for value, send them
                # yours
                if REPLICA_ID in curr_values:
                    to_remove = []
                    for in_message in messages:
                        if in_message[2] == 'value ask':
                            if in_message[3] == curr_view:
                                message = [([REPLICA_ID, in_message[0],
                                             "my propose", curr_view,
                                             curr_values[REPLICA_ID]])]
                                Thread(target=ack_sent_message,
                                       args=message).start()
                                print("Sent my value to replica " + str(
                                    in_message[0]))
                            to_remove.append(in_message)
                    for msg in to_remove:
                        messages.remove(msg)
            if status == 1:
                # after you have a value send it to everyone
                for i in range(NUM_OF_REPLICAS):
                    message = [([REPLICA_ID, i, "value propose", curr_view,
                               curr_values[REPLICA_ID]])]
                    Thread(target=ack_sent_message,
                           args=message).start()
                print("proposed my value to everyone")
                status = 2

            if status > 1:
                to_remove = []
                for in_message in messages:
                    #  try and see if anyone sent their value
                    if in_message[2] == 'value propose':
                        if in_message[3] == curr_view:
                            curr_values[in_message[0]] = in_message[4]
                            message = [([REPLICA_ID, in_message[0], "value ack",
                                       curr_view, curr_values[in_message[0]]])]
                            print("acked the value of", in_message[0], 
                                  "in view", in_message[3])
                            Thread(target=ack_sent_message,
                                   args=message).start()
                        to_remove.append(in_message)
                    elif in_message[2] == 'my propose':
                        to_remove.append(in_message)
                for msg in to_remove:
                    messages.remove(msg)

            if status == 2:
                # check if there are ack messages for you, and if there are at
                # least 2, go to the next stage
                to_remove = []
                for in_message in messages:
                    if in_message[2] == 'value ack':
                        if in_message[3] == curr_view and in_message[4] == \
                                curr_values[REPLICA_ID]:
                            value_acks.add(in_message[0])
                        to_remove.append(in_message)
                for msg in to_remove:
                    messages.remove(msg)
                if len(value_acks) > 1:
                    status = 3
                    print("Enough acks, commit to the value")
                    value_acks.clear()
                    for i in range(NUM_OF_REPLICAS):
                        print("sent \"commit value\" to " + str(i))
                        message = [([REPLICA_ID, i, "commit value", curr_view,
                                   curr_values[REPLICA_ID]])]
                        Thread(target=ack_sent_message,
                               args=message).start()

            to_remove = []
            for in_message in messages:
                # try and see if anyone sent commit
                if in_message[2] == "commit value":
                    if in_message[3] == curr_view:
                        if in_message[0] not in curr_values:
                            curr_values[in_message[0]] = in_message[4]
                        message = [([REPLICA_ID, in_message[0], "ack commit",
                                   curr_view, curr_values[in_message[0]]])]
                        print("acked the commit of " + str(in_message[0]))
                        Thread(target=ack_sent_message,
                               args=message).start()
                    to_remove.append(in_message)
            for msg in to_remove:
                messages.remove(msg)

            if status == 3:
                # check if there are ack messages for you, and if there are at
                # least 2, go to the next stage
                to_remove = []
                for in_message in messages:
                    if in_message[2] == "ack commit":
                        if in_message[3] == curr_view and in_message[4] == \
                                curr_values[REPLICA_ID]:
                            commit_acks.add(in_message[0])
                        to_remove.append(in_message)
                for msg in to_remove:
                    messages.remove(msg)
                if len(commit_acks) > 1:
                    print("enough commit acks. Now done")
                    commit_acks.clear()
                    status = 4
                    for i in range(NUM_OF_REPLICAS):
                        print("sent done to " + str(i))
                        message = [([REPLICA_ID, i, "done", curr_view,
                                   curr_values[REPLICA_ID]])]
                        Thread(target=ack_sent_message,
                               args=message).start()

            if status == 4:
                # check if there are done messages, and if there are at
                # least 2, go to the next stage
                to_remove = []
                for in_message in messages:
                    if in_message[2] == "done":
                        if in_message[3] == curr_view and in_message[4] == \
                                curr_values[in_message[0]]:
                            print("done from", in_message[0])
                            done_acks.add(in_message[0])
                        to_remove.append(in_message)
                for msg in to_remove:
                    messages.remove(msg)
                if len(done_acks) > 1:
                    print("enough done messages. Now check for primary")
                    status = 5
                    message = [([REPLICA_ID, -1, curr_view])]
                    print("asked for the selected replica")
                    Thread(target=ack_sent_message,
                           args=message).start()
                    done_acks.clear()

            if status == 5:
                to_remove = []
                for in_message in messages:
                    print(in_message)
                    if in_message[0] == -1:
                        # if the message is the elected primary
                        if in_message[3] == curr_view:
                            print("The elected primary is " + str(
                                in_message[4]))
                            if in_message[4] in curr_values:
                                # send the value only if you have it
                                value = curr_values[in_message[4]]
                                if value != curr_values[REPLICA_ID]:
                                    # if the value is not my value, return the
                                    # value to the queue
                                    VALUES.insert(0, curr_values[REPLICA_ID])
                                    print("returned the value")
                                for client in client_sockets:
                                    client_sockets[client].send(value)
                                    print("sent to client ", client)
                            curr_view = curr_view + 1
                            curr_values.clear()
                            status = 0
                            sent_messages = False
                        to_remove.append(in_message)
                for msg in to_remove:
                    messages.remove(msg)


# 2 Threads - one responsible for receiving messages, one for running the
# protocol
is_check = False
receive_thread = Thread(target=receive_messages)
protocol_thread = Thread(target=paxos_protocol,
                         args=(current_values, messages_queue,
                               current_view, view_status))
receive_thread.start()
protocol_thread.start()
