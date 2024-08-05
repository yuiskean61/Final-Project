import socket
import threading
import time
import sqlite3

# server config
HOST = '127.0.0.1'  # Localhost
PORT = 1024  # Choose any port number above 1024

# stores connected clients and their usernames
clients = []
usernames = {}

# creates socket object
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Set up SQLite Database
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
                if message.startswith("USERNAME:"):
                    username = message.split(":")[1]
                    usernames[client] = username
                    #send_recent_messages(client)
                    broadcast(f"{username} has joined the chat!", client)
                    client.send("Connected to HumberChat server!".encode('ascii'))
                elif message.lower() == 'history':
                    send_recent_messages(client)
                else:
                    if client in usernames:
                        save_message(usernames[client], message)
                        broadcast(f"{usernames[client]}: {message}", client)
                    else:
                        client.send("Please set your username first.".encode('ascii'))
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

if __name__ == "__main__":
    start_server()