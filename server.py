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
        message TEXT
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

    """)
    print(f"""
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

    while True:
        try:
            # receives message from client
            message = client.recv(1024).decode('ascii')
            if message:
                if message.startswith("REGISTER:"):
                    _, username, password = message.split(":")
                    register(client, username, password)
                elif message.startswith("LOGIN:"):
                    _, username, password = message.split(":")
                    login(client, username, password)
                    broadcast(f"{username} has joined the chat!", client, get_client_room(client))
                    client.send("Connected to HumberChat server!".encode('ascii'))
                    client.send(f"Connected to chatroom: {get_client_room(client)}".encode('ascii'))
                elif message.lower() == '/history':
                    send_recent_messages(client)
                elif message.lower() == '/quit':
                    client.send("Signing out and closing...".encode('ascii'))
                    client.close()
                    break
                elif client in usernames:
                    if message.startswith('/pm'):
                        parts = message.split(" ", 2)
                        if len(parts) < 3:
                            client.send("Invalid private message format. Use /pm <username> <message>".encode('ascii'))
                            continue
                        receiver = parts[1]
                        message_body = parts[2]
                        if receiver in usernames.values():
                            for receiver_client, username in usernames.items():
                                if username == receiver:
                                    receiver_client.send(f"PM from {usernames[client]}: {message_body}"
                                                         .encode('ascii'))
                                    client.send(f"PM to {username}: {message_body}".encode('ascii'))
                        else:
                            client.send(f"No user found with name {receiver}".encode('ascii'))
                    elif message.startswith('/room'):
                        parts = message.split(" ", 2)
                        if len(parts) < 2:
                            client.send("Invalid command format. Use /room <room name>".encode('ascii'))
                            continue
                        target_room = parts[1]
                        change_client_room(client, target_room)
                    else:
                        save_message(usernames[client], message)
                        broadcast(f"{usernames[client]}: {message}",
                                  client, client_to_room[client].name)
                else:
                    client.send("Please log in or register first.".encode('ascii'))
            else:
                # Empty message, client disconnected
                raise Exception("Client disconnected")
        except Exception:
            if client in usernames:
                username = usernames[client]
                broadcast(f'{username} left the chat!', client, get_client_room(client))
                del usernames[client]
            # closes a client on error/disconnect
            if client in clients:
                clients.remove(client)

            client.close()
            break


def init_chat_rooms():
    general = chatroom.ChatRoom("general")
    comp_sci = chatroom.ChatRoom("comp-sci")
    accounting = chatroom.ChatRoom("accounting")
    chat_rooms.extend([general, comp_sci, accounting])


def add_user_to_room(client, room_name):
    for room in chat_rooms:
        if room.name == room_name:
            room.add_user(client)
            client_to_room[client] = room
        break  # exits early once unique room name is found
    return None  # no chatroom with name was found


def list_users_in_room(room_name):
    return_string = ""
    for room in chat_rooms:
        if room.name == room_name:
            for client in room.clients:
                if client in usernames:
                    return_string += usernames[client] + "\n"  # Append username to return_string
            break
    return return_string


def list_chat_rooms():
    return_string = ""
    for room in chat_rooms:
        return_string += room.name + " "
    return return_string


def get_client_room(client):
    if client in client_to_room:
        return client_to_room[client].name
    else:
        return None


def change_client_room(client, new_room):
    room_found = False  # Flag to determine if desired room was found or not
    for room in chat_rooms:
        if room.name == new_room:
            room_found = True  # set flag to true since room was found
            if client in client_to_room:
                current_room = client_to_room[client]
                current_room.remove_user(client)
            room.add_user(client)
            client_to_room[client] = room
            client.send(f"Room changed to {room.name}".encode('ascii'))
            broadcast(f"{usernames[client]} has joined the room {room.name}!", client, room.name)
            break
    if not room_found:
        client.send(f"Room with name {new_room} was not found.".encode('ascii'))


def broadcast(message, sender_client, room_name):
    for room in chat_rooms:
        if room.name == room_name:
            for client in room.clients:
                if client != sender_client and client in usernames:
                    try:
                        client.send(f"{message}".encode('ascii'))
                    except:
                        # if sending fails, assume client disconnected
                        if client in clients:
                            clients.remove(client)
                        if client in usernames:
                            del usernames[client]


def save_message(username, message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO messages (timestamp, username, message)
        VALUES (?, ?, ?)
    ''', (timestamp, username, message))
    connection.commit()
    print(f"Saved Message: [{timestamp}] {username}: {message}")


def send_recent_messages(client):
    cursor.execute('SELECT timestamp, username, message FROM messages ORDER BY id DESC LIMIT 20')
    recent_msgs = cursor.fetchall()
    for timestamp, username, message in reversed(recent_msgs):
        client.send(f"[{timestamp}] {username}: {message}".encode('ascii'))


# Register Function
def register(client, username, password):
    try:
        cursor.execute('''
            INSERT INTO users (username, password)
            VALUES (?, ?)
        ''', (username, password))
        connection.commit()
        client.send(f"Registration successful. You can now login as {username}!".encode('ascii'))
    except sqlite3.IntegrityError:
        client.send("Username already exists. Please try a different username".encode('ascii'))


# Login function
def login(client, username, password):
    cursor.execute('''
        SELECT * FROM users WHERE username = ? AND password = ?
    ''', (username, password))
    user = cursor.fetchone()
    if user:
        usernames[client] = username
        add_user_to_room(client, "general")
        client.send(f"Login successful. Welcome {username}!".encode('ascii'))
    else:
        client.send("Invalid username or password. Please try again.")


if __name__ == "__main__":
    start_server()
