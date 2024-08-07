# concept class for a user class that has an associated client, username and room
# currently unused, if time allows, possible refactor server code to use it instead
class User:
    client = None
    username = ""
    current_room = "None"

    def __init__(self, client, username, current_room):
        self.client = client
        self.username = username
        self.current_room = current_room