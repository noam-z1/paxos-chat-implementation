import tkinter as tk


class ChatWindow:

    WINDOW_WIDTH = 500
    WINDOW_HEIGHT = 500
    MSG_BOX_HEIGHT = 100

    def __init__(self, window, name, send_function):
        """
        constructor of the gui board
        :param window: A tkinter object to use
        :param name: The nickname of the client
        :param send_function: The function that send messages
        """

        self.__nick_name = name
        self.__window = window
        self.__send_message = send_function
        self.__window.minsize(ChatWindow.WINDOW_WIDTH,
                              ChatWindow.WINDOW_HEIGHT)
        self.__window.resizable(0, 0)
        self.__headline = tk.Label(self.__window, width=20, height=1,
                                   font=("Arial",30), text="Welcome to the "
                                                           "chat")
        self.__headline.pack(side="top")
        self.__nick = tk.Label(self.__window, width=20, height=1, fg="green",
                               font=("Arial", 10), text="Your nickname "
                                                            "is: "+self.__nick_name)
        self.__nick.pack(anchor="w")

        self.__chat_box = tk.Text(self.__window, width=70, height=29,
                                  bg="#DDDDDD")
        self.__chat_box.insert(tk.INSERT, "Waiting for other clients...\n")
        self.__chat_box.insert(tk.INSERT, "Exit at any time by sending "
                                          "\"quit\" message.\n")
        self.__chat_box.configure(state='disabled')
        self.__chat_box.pack(side="top")
        self.__chat_box.tag_config('name', foreground="green")
        self.__chat_box.tag_config('server', foreground="red")
        self.__text_box = tk.Text(self.__window, width=65, height=2)
        self.send_but = tk.Button(self.__window, width=5, height=2,
                                    text="Send!", command=self.button_click)
        self.send_but.pack(side="right")
        self.__text_box.pack(side="left")
        self.__window.bind("<Return>", self.__return_click)

    def button_click(self, is_return=False, event=None):
        """
        The method to call whenever when is clicked
        :return:
        """
        text = self.__text_box.get("1.0", "end")
        if is_return:
            text = text[:-1]
        self.__text_box.delete("1.0", "end")
        if len(text) > 0:
            self.__chat_box.configure(state='normal')
            self.__send_message(self.__nick_name, text)
            self.__chat_box.configure(state='disabled')

    def __return_click(self, event=None):
        event = None
        self.button_click(True)

    def receive_message(self, msg, name=None):
        """
        This method receives a message from another user and prints it
        :param name: The nickname of the user
        :param msg: The message
        :return:
        """
        self.__chat_box.configure(state='normal')
        if name:
            self.__chat_box.insert(tk.INSERT, name + ": ", 'name')
            self.__chat_box.insert(tk.INSERT, msg)
        else:
            self.__chat_box.insert(tk.INSERT, msg, 'server')
        self.__chat_box.configure(state='disabled')

