import socket
import threading
import time

# server config
HOST = '10.0.0.115'  # Server IP address
PORT = 1024  # Choose any port number above 1024

# stores connected clients and their usernames
clients = []
usernames = {}


# creates socket object
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
                    broadcast(f"{username} has joined the chat!", client)
                    client.send("Connected to HumberChat server!".encode('ascii'))
                elif client in usernames:
                    if message.startswith('/pm'):
                        parts = message.split(" ", 2)
                        if len(parts) < 3:
                            client.send("Invalid private message format. Use /pm <username> <message>".encode('ascii'))
                            continue
                        receiver = parts[1]
                        message_body = parts[2]
                        timestamp = time.strftime("%H:%M:%S")
                        if receiver in usernames.values():
                            for receiver_client, username in usernames.items():
                                if username == receiver:
                                    receiver_client.send(f"PM from {usernames[client]}: {message_body}"
                                                         .encode('ascii'))
                                    client.send(f"PM to {username}: {message_body}".encode('ascii'))
                        else:
                            client.send(f"No user found with name {receiver}".encode('ascii'))
                    else:
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


if __name__ == "__main__":
    start_server()