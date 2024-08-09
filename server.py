import socket
import sqlite3
import threading
import time
import chatroom

# server config
HOST = '10.0.0.115'  # Server IP address
PORT = 1024  # Choose any port number above 1024

# stores connected clients and their usernames
clients = []
usernames = {}

# stores the chat rooms and a dictionary to store the room of each client
chat_rooms = []
client_to_room = {}

# creates socket object
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Init SQLite database's
connection = sqlite3.connect('messages.db', check_same_thread=False)
cursor = connection.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        username TEXT,
        message TEXT,
        chatroom TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
''')
connection.commit()


def start_server():
    # binds socket to a specific address and port
    server.bind((HOST, PORT))
    server.listen()

    print(f"""
    Welcome to HumberChat Server
    ============================
    Server started on: {HOST}:{PORT}
    Date: {time.strftime('%Y-%m-%d')}
    Time: {time.strftime('%H:%M:%S')}
    Creating chat rooms... 
    """)
    init_chat_rooms()
    print(f"""
    Rooms created.
    Server is ready to accept connections...
    """)
    while True:
        # waits for a client connection
        client, address = server.accept()
        print(f"New connection from {address}")

        # starts new thread to handle the client
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()


def handle_client(client):
    # adding clients to the list
    clients.append(client)
    try:
        while True:
            try:
                # receives message from client
                message = client.recv(1024).decode('ascii')
                print(f"raw msg {message}")
                if message:
                    # handle user registration command
                    if message.startswith("register:"):
                        _, username, password = message.split(":")
                        register_result = register(client, username, password)
                        if register_result:
                            login(client, username, password)
                    # handle user login command
                    elif message.startswith("login:"):
                        _, username, password = message.split(":")
                        login(client, username, password)
                    # handle chat history command
                    elif message.lower() == '/history':
                        send_recent_messages(client)
                    # Commands with access granted only to logged-in users
                    elif client in usernames:
                        # Private messaging command
                        if message.startswith('/pm'):
                            # Gets the target users name and the message by splitting original command string
                            parts = message.split(" ", 2)
                            # Handle invalid format
                            if len(parts) < 3:
                                client.send("Invalid private message format. Use /pm <username> <message>".encode('ascii'))
                                continue
                            # Set receiver and message to corresponding part
                            receiver = parts[1]
                            message_body = parts[2]
                            # If the receiver is signed in to server
                            if receiver in usernames.values():
                                '''
                                Used to search for the receiver client, since client is the key, some form of iteration
                                is required when only the name is given. A 'next' function could lower the line count,
                                but I found it was harder to make and maintain, and has the same time cost as a for loop.
                                '''
                                for receiver_client, username in usernames.items():
                                    if username == receiver:
                                        # Send message to receiver
                                        receiver_client.send(f"PM from {usernames[client]}: {message_body}"
                                                             .encode('ascii'))
                                        # Display copy of message to sender
                                        client.send(f"PM to {username}: {message_body}".encode('ascii'))
                                        break  # break early once a user with matching name is found
                            # Handle if no user is found
                            else:
                                client.send(f"No user found with name {receiver}".encode('ascii'))
                        # Command to switch users current chatroom
                        elif message.startswith('/room'):
                            parts = message.split(" ", 2)
                            # Handle invalid format
                            if len(parts) < 2:
                                client.send("Invalid command format. Use /room <room name>".encode('ascii'))
                                continue
                            # Get name of the room the user wishes to switch to
                            target_room = parts[1]
                            # switch their room
                            change_client_room(client, target_room)
                        # The command used to list all rooms
                        elif message.startswith('/rlist'):
                            client.send(list_chat_rooms().encode('ascii'))
                        # The command used to list all users in user's current room
                        elif message.startswith('/ulist'):
                            client.send(list_users_in_room(get_client_room_name(client)).encode('ascii'))
                        # The command used to list all users in the server
                        elif message.startswith('/listall'):
                            client.send(list_all_users().encode('ascii'))
                        # The command used to display users current room
                        elif message.startswith('/myroom'):
                            client.send(f"You are in chat room: {get_client_room_name(client)}".encode('ascii'))
                        # If user is logged in and the message was not a command; display message to the chat room
                        else:
                            save_message(usernames[client], message, client_to_room[client].name)
                            broadcast(f"{usernames[client]}: {message}",
                                      client, client_to_room[client].name)
                    else:
                        client.send("Please log in or register first.".encode('ascii'))
                else:
                    raise Exception("Client disconnected")
            except Exception as e:
                print(f"error {e}")
                break
    # Handle client quitting
    finally:
        if client in client_to_room:
            broadcast(f'{usernames[client]} left the chat!', client, get_client_room_name(client))
            del client_to_room[client]
        if client in usernames:
            del usernames[client]
        # closes a client on error/disconnect
        if client in clients:
            clients.remove(client)
        client.close()


# Initializes the server chat rooms
def init_chat_rooms():
    general = chatroom.ChatRoom("general")
    comp_sci = chatroom.ChatRoom("comp-sci")
    accounting = chatroom.ChatRoom("accounting")
    chat_rooms.extend([general, comp_sci, accounting])


# Adds a user to a chat room based on chat room name
def add_user_to_room(client, room_name):
    for room in chat_rooms:
        if room.name == room_name:
            room.add_user(client)
            client_to_room[client] = room
        break  # exits early once unique room name is found
    return None  # no chatroom with name was found


# Lists all users on the server
def list_all_users():
    return_string = f"Online Users: \n"
    for user in usernames.values():
        return_string += user + '\t'
    return return_string


# Lists the users in the clients current chat room
def list_users_in_room(room_name):
    return_string = f""
    '''
    As only a name is given, and no key value for the chatroom object in the dictionary,
    iteration is used to find the required room
    '''
    for room in chat_rooms:
        if room.name == room_name:
            return_string += f"Users in {room.name}: \n"
            for client in room.clients:
                if client in usernames:
                    return_string += usernames[client] + "\t"  # Append username to return_string
            break # Exit early once desired room is found
    return return_string


# Lists names of all chat rooms
def list_chat_rooms():
    return_string = "Chat Rooms: \n"
    for room in chat_rooms:
        return_string += room.name + "\t"
    return return_string


# Gets the name of the chat room the client is currently in, or none if they are not in a room
def get_client_room_name(client):
    if client in client_to_room:
        return client_to_room[client].name
    else:
        return None


# Changes the chat_room of a client to given room name
def change_client_room(client, new_room):
    room_found = False  # Flag to determine if desired room was found or not
    for room in chat_rooms:
        if room.name == new_room:
            room_found = True  # set flag to true since room was found
            if client in client_to_room:
                # Get their current room
                current_room = client_to_room[client]
                # Leave message in current room that user has left
                broadcast(f"{usernames[client]} has left the room!", client, current_room.name)
                # Remove them from current room
                current_room.remove_user(client)
            # Add them to new room
            room.add_user(client)
            client_to_room[client] = room
            # Tell user they have changed rooms
            client.send(f"Room changed to {room.name}".encode('ascii'))
            # Tell chatroom they have changed rooms
            broadcast(f"{usernames[client]} has joined the room {room.name}!", client, room.name)
            break
    if not room_found:
        # Error message if user tries to enter a room that does not exist
        client.send(f"Room with name {new_room} was not found.".encode('ascii'))


# Sends a message to everyone in a given chatroom, except the sender
def broadcast(message, sender_client, room_name):
    for room in chat_rooms:
        if room.name == room_name:
            for client in room.clients:
                if client != sender_client and client in usernames:
                    try:
                        client.send(f"{message}".encode('ascii'))
                    except Exception as e:
                        # if sending fails, assume client disconnected
                        print(f"error {e}")
                        if client in clients:
                            clients.remove(client)
                        if client in usernames:
                            del usernames[client]


# Saves message to the DB
def save_message(username, message, chatroom):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO messages (timestamp, username, message, chatroom)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, username, message, chatroom))
    connection.commit()
    print(f"Saved Message: [{timestamp}] {username} in {chatroom}: {message}")


# Fetches recent messages from the DB and sends to client
def send_recent_messages(client):
    cursor.execute('SELECT timestamp, username, message FROM messages ORDER BY id DESC LIMIT 20')
    recent_msgs = cursor.fetchall()
    for timestamp, username, message in reversed(recent_msgs):
        client.send(f"[{timestamp}] {username}: {message}".encode('ascii'))


# User Registration Function
def register(client, username, password):
    try:
        cursor.execute('''
            INSERT INTO users (username, password)
            VALUES (?, ?)
        ''', (username, password))
        print(f'Registration of user: {username}')
        connection.commit()
        client.send(f"Registration successful. You can now login as {username}!".encode('ascii'))
        return True
    except sqlite3.IntegrityError:
        client.send("Username already exists. Please try a different username".encode('ascii'))
        return False


# Login function
def login(client, username, password):
    if username in usernames.values():
        client.send("This user is already logged in from another device.".encode('ascii'))
        return

    cursor.execute('''
        SELECT * FROM users WHERE username = ? AND password = ?
    ''', (username, password))
    user = cursor.fetchone()
    if user:
        usernames[client] = username
        add_user_to_room(client, "general")
        client.send(f"Login successful. Welcome {username} to HumberChat server!".encode('ascii'))
        broadcast(f"{username} has joined the chat!", client, get_client_room_name(client))
        client.send(f"Connected to chatroom: {get_client_room_name(client)}".encode('ascii'))
    else:
        client.send("Invalid username or password. Please try again.".encode('ascii'))


if __name__ == "__main__":
    start_server()
