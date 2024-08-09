class ChatRoom:
    name = ""  # the name of the room
    clients = []  # clients in the room

    def __init__(self, name):
        self.name = name
        self.clients = []

    def add_user(self, client):
        self.clients.append(client)

    def remove_user(self, client):
        if client in self.clients:
            self.clients.remove(client)

