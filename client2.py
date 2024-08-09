import socket
import threading
import time

# client config
HOST = '10.0.0.115'  # server IP address
PORT = 1024
# Create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

messages = []


def print_messages():
    print("\nChat History:")
    for msg in messages[-20:]:  # Show last 20 messages
        print(msg)
    # print("\nEnter your message: ", end="")


def connect():
    client.connect((HOST, PORT))
    print(f"""
    Welcome to HumberChat
    =====================
    Connected to server at {HOST}:{PORT}

    Instructions:
    - Type 'register:<username>:<password>' to register an account
    - Type 'login:<username>:<password>' to log in
    - Type your message and press Enter to send
    - Type '/help' to view more commands and info
    """)

    receive_thread = threading.Thread(target=receive_messages)
    receive_thread.start()

    send_messages()


def help_message():
    print(f"""
        Information
        ========================================
        Connected to server at {HOST}:{PORT}
        - Type your message and press Enter to send
        - Type 'register:<username>:<password>' to register an account
        - Type 'login:<username>:<password>' to log in
        - Type '/' followed by a command word to use a command

        Command List
        =========================================
        - '/pm <user name> <message>' - sends a private message to 
                                        user with given user name
        - '/history' - view recent messages
        - '/room <room name>' - switches chat room to matching name
        - '/rlist' - gets a list of chat rooms
        - '/ulist' - gets a list of users in a your chat room
        - '/listall' - get a list of ALL online users
        - '/myroom' - gets the name of your current chatroom
        - '/quit' - exit the chat
        """)


def receive_messages():
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            if not message:  # Check for socket closure
                print("Connection to server ended. Closing client.")
                break
            timestamp = time.strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
            messages.append(formatted_message)
            print(f"\n{formatted_message}")
            # print("Enter your message: ", end="")
        except:
            print("Connection to server ended.")
            break
    client.close()


def send_messages():
    while True:
        message = input("")
        if message.lower() == '/quit':
            print(f"Closing connection to the server.")
            client.close()
            break
        elif message.lower() == '/help':
            help_message()
        elif message.lower() == '/history':
            client.send('/history'.encode('ascii'))  # Client sends history to receive message history
            time.sleep(1)  # Give the server time to get the messages
        elif message.startswith('/pm'):
            client.send(message.encode('ascii'))
        else:
            client.send(message.encode('ascii'))


if __name__ == "__main__":
    connect()
