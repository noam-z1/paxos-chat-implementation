A paxos protocol in an asynchronous 
ronment implementation

consists of 4 files:

ChatWindow.py - Implementation of GUI interface for a chat room. connects with the client
Client.py - Implementation of the client side. connects via socket with a single server
Server.py - Implementation of a server side, connects via socket to clients and to the environment simulator.
Also implementing the paxos protocol. The server can fail if getting a message from the simulator.
Simulator.py - Implementation of the environment. Enabaling delaying of messages, and connection of servers to each other. 
Also consist a mechanism of choosing a server that will be faulty(omission failure), and making sure only one is faulty.

Strating the program:

1. start the Simulator.py script, no arguments
(Simulator.py)
2. start the server script 3 times, each time with a different id as argument 
(Server.py 0, Server.py 1, Server.py 2)
3. start client scripts, each time with a string representing it's name, and the id of the server it will connect to as arguments:
(Client.py "Noam"0)

Some design notes:

- The delay of the messages is between 1 sec, and 1 minute. A new faulty Server is elected randomly between the servers connected 
every 3-5 minutes
- Every 5 minutes, each server checks it's state. if it's in the same state as the previous check, it resends the messages from 
the current\previous state. This makes sure that if a server was faulty and now returns to normal, it can resend it's messages 
and continue the protocol
- Every messages that is sent between the servers and the simulator is being acked, so messages won't be lost. It used to happen
before the mechanism, so I've created it
- The primary selection proccess happens in the simulator, but the messages aren't delayed, to simulate a coin toss mechanism,
which needs to happen in the servers, but I couldn't implement that way
- If a server doesn't have the value that was selected in primary selection mechanism, it drops the view. 
Probably if the clients were not depended on a single server but on a more "general"concept of server it would work fully that way,
but implementing it was probably more complicated, so I''ve chose no to
- Every time a socket is closing, the other end crashes, probably should have fixed it, but it doesn't effect the paxos 
protocol(since a server is closed when I'm exiting it's script) so I've skipped it
