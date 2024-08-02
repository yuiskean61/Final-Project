import socket
import threading
import time

# client config
HOST = '10.111.13.180'  # server IP address
PORT = 1024         # The port used by the server

# Create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

messages = []

def print_messages():
    print("\nChat History:")
    for msg in messages[-20:]:  # Show last 20 messages
        print(msg)
    print("\nEnter your message: ", end="")

def connect():
    client.connect((HOST, PORT))
    print(f"""
    Welcome to HumberChat
    =====================
    Connected to server at {HOST}:{PORT}
    You are logged in as: {username}

    Instructions:
    - Type your message and press Enter to send
    - Type 'history' to view recent messages
    - Type 'quit' to exit the chat
    """)
    
    # Send username to server
    client.send(f"USERNAME:{username}".encode('ascii'))
    
    receive_thread = threading.Thread(target=receive_messages)
    receive_thread.start()
    
    send_messages()

def receive_messages():
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            timestamp = time.strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
            messages.append(formatted_message)
            print(f"\nNew message: {formatted_message}")
            print("Enter your message: ", end="")
        except:
            print("An error occurred!")
            client.close()
            break

def send_messages():
    while True:
        message = input("Enter your message: ")
        if message.lower() == 'quit':
            client.close()
            break
        elif message.lower() == 'history':
            print_messages()
        else:
            client.send(message.encode('ascii'))

if __name__ == "__main__":
    username = input("Enter your username: ")
    connect()