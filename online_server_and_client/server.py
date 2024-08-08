import socket
import threading
import time
import sqlite3

# server config
local_host = '127.0.0.1'
HOST = '192.168.75.218'  # Server IP address
PORT = 1024  # Choose any port number above 1024

# stores connected clients and their usernames
clients = []
usernames = {}

# creates socket object
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Init SQLite database's
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
    server.bind((local_host, PORT))#Changed to local host for testing
    server.listen()
    
    print(f"""
    Welcome to HumberChat Server
    ============================
    Server started on: {HOST}:{PORT}
    Date: {time.strftime('%Y-%m-%d')}
    Time: {time.strftime('%H:%M:%S')}
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
                    print("here")
                    _, username, password = message.split(":")
                    register(client, username, password)
                    print("here 2")
                elif message.startswith("LOGIN:"):
                    _, username, password = message.split(":")
                    login(client, username, password)
                elif message.startswith("USERNAME:"):
                    username = message.split(":")[1]
                    usernames[client] = username
                    broadcast(f"{username} has joined the chat!", client)
                    client.send("Connected to HumberChat server!".encode('ascii'))
                elif message.lower() == 'history':
                    send_recent_messages(client)
                else:
                    if client in usernames:
                        save_message(usernames[client], message)
                        broadcast(f"{usernames[client]}: {message}", client)
                    else:
                        client.send("Please log in first.".encode('ascii'))
            else:
                # Empty message, client disconnected
                raise Exception("Client disconnected")
        except:
            # closes a client on error/disconnect
            if client in clients:
                clients.remove(client)
            if client in usernames:
                username = usernames[client]
                del usernames[client]
                broadcast(f'{username} left the chat!', client)
            client.close()
            break

def broadcast(message, sender_client):
    for client in clients:
        if client != sender_client:
            try:
                client.send(message.encode('ascii'))
            except:
                # if sending fails, assume client disconnected
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
    print(f"Saved MEssage: [{timestamp}] {username}: {message}")

def send_recent_messages(client):
    cursor.execute('SELECT timestamp, username, message FROM messages ORDER BY id DESC LIMIT 20')
    recent_msgs = cursor.fetchall()
    for timestamp, username, message in reversed(recent_msgs):
        client.send(f"[{timestamp}] {username}: {message}".encode('ascii'))

#Register Function
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

#Login function
def login(client, username, password):
    cursor.execute('''
        SELECT * FROM users WHERE username = ? AND password = ?
    ''', (username, password))
    user = cursor.fetchone()
    if user:
        usernames[client] = username
        client.send(f"Login successful. Welcome {username}!".encode('ascii'))
    else:
        client.send("Invalid username or password. Please try again.")

if __name__ == "__main__":
    start_server()