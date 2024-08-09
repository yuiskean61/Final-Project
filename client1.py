import socket
import threading
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
from PIL import Image, ImageTk
import queue
import re

# client config
HOST = '127.0.0.1'
PORT = 1024

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
messages = []

class ChatApp:
    def __init__(self, master):
        self.master = master
        self.master.title("HumberChat")
        self.master.geometry("500x700")
        self.master.minsize(400, 500)
        self.username = ""
        
        # color scheme
        self.bg_color = "#FFFFFF"
        self.primary_color = "#003C71"  # humber navy blue
        self.accent_color = "#FDB714"   # humber yellow
        self.text_color = "#333333"
        
        # fonts
        self.font = ("Helvetica", 10)
        self.bold_font = ("Helvetica", 10, "bold")
        
        # Store image reference
        self.logo_image = None
        self.logo_label = None
        
        # Message queue
        self.message_queue = queue.Queue()
        
        self.create_login_window()
        # Schedule logo loading after mainloop starts
        self.master.after(100, self.load_and_display_logo)
        
        # Start checking for messages
        self.check_messages()

    def create_login_window(self):
        self.login_frame = tk.Frame(self.master, bg=self.bg_color)
        self.login_frame.pack(expand=True, fill=tk.BOTH)

        # Placeholder for logo
        self.logo_label = tk.Label(self.login_frame, bg=self.bg_color)
        self.logo_label.pack(pady=20)

        tk.Label(self.login_frame, text="Welcome to HumberChat!", font=self.bold_font, bg=self.bg_color, fg=self.primary_color).pack(pady=10)

        tk.Label(self.login_frame, text="Username:", font=self.font, bg=self.bg_color, fg=self.text_color).pack()
        self.username_entry = tk.Entry(self.login_frame, font=self.font, bg="white", fg=self.text_color)
        self.username_entry.pack(pady=5)

        tk.Label(self.login_frame, text="Password:", font=self.font, bg=self.bg_color, fg=self.text_color).pack()
        self.password_entry = tk.Entry(self.login_frame, font=self.font, bg="white", fg=self.text_color, show="*")
        self.password_entry.pack(pady=5)

        login_button = tk.Button(self.login_frame, text="Login", command=self.login, 
                                 bg=self.primary_color, fg="white", font=self.bold_font)
        login_button.pack(pady=5)

        register_button = tk.Button(self.login_frame, text="Register", command=self.register, 
                                    bg=self.accent_color, fg="white", font=self.bold_font)
        register_button.pack(pady=5)

    def load_and_display_logo(self):
        try:
            image = Image.open("humber_logo.jpg")
            image = image.resize((350, 300), Image.Resampling.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(image)
            self.logo_label.config(image=self.logo_image)
        except Exception as e:
            print(f"Error loading logo: {e}")
            self.logo_label.config(text="HUMBER", font=("Helvetica", 24, "bold"), fg=self.primary_color)

    def create_chat_window(self):
        self.chat_frame = tk.Frame(self.master, bg=self.bg_color)
        self.chat_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.chat_log = scrolledtext.ScrolledText(self.chat_frame, state='disabled', font=self.font, 
                                                  bg="white", fg=self.text_color)
        self.chat_log.pack(expand=True, fill=tk.BOTH)
        
        # Add a tag for bold text
        self.chat_log.tag_configure('bold', font=self.bold_font)

        input_frame = tk.Frame(self.chat_frame, bg=self.bg_color)
        input_frame.pack(fill=tk.X, pady=5)

        self.message_entry = tk.Entry(input_frame, font=self.font, bg="white", fg=self.text_color)
        self.message_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.message_entry.bind("<Return>", self.send_message)
        self.message_entry.insert(0, "Type here to chat!")
        self.message_entry.bind("<FocusIn>", self.on_entry_click)
        self.message_entry.bind("<FocusOut>", self.on_focusout)
        self.message_entry.config(fg='grey')

        send_button = tk.Button(input_frame, text="↵", command=self.send_message, 
                                bg=self.primary_color, fg="white", font=self.bold_font)
        send_button.pack(side=tk.RIGHT, padx=5)

        # Add buttons for additional functionality
        button_frame = tk.Frame(self.chat_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=5)

        help_button = tk.Button(button_frame, text="Help", command=self.show_help,
                                bg=self.accent_color, fg="white", font=self.font)
        help_button.pack(side=tk.LEFT, padx=2)

        history_button = tk.Button(button_frame, text="History", command=self.show_history,
                                   bg=self.accent_color, fg="white", font=self.font)
        history_button.pack(side=tk.LEFT, padx=2)

        room_button = tk.Button(button_frame, text="Change Room", command=self.change_room,
                                bg=self.accent_color, fg="white", font=self.font)
        room_button.pack(side=tk.LEFT, padx=2)

        users_button = tk.Button(button_frame, text="User List", command=self.show_users,
                                 bg=self.accent_color, fg="white", font=self.font)
        users_button.pack(side=tk.LEFT, padx=2)

    def on_entry_click(self, event):
        if self.message_entry.get() == "Type here to chat!":
            self.message_entry.delete(0, tk.END)
            self.message_entry.config(fg=self.text_color)

    def on_focusout(self, event):
        if self.message_entry.get() == "":
            self.message_entry.insert(0, "Type here to chat!")
            self.message_entry.config(fg='grey')

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        self.username = username  # Store the username
        self.connect(f"login:{username}:{password}")

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        self.username = username  # Store the username
        self.connect(f"register:{username}:{password}")

    def connect(self, initial_message):
        try:
            client.connect((HOST, PORT))
            client.send(initial_message.encode('ascii'))
            self.login_frame.destroy()
            self.create_chat_window()
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def receive_messages(self):
        while True:
            try:
                message = client.recv(1024).decode('ascii')
                timestamp = time.strftime("%H:%M")
                formatted_message = f"[{timestamp}] {message}"
                self.message_queue.put(formatted_message)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break
        client.close()

    def check_messages(self):
        try:
            while True:
                message = self.message_queue.get_nowait()
                self.display_message(message)
        except queue.Empty:
            pass
        finally:
            self.master.after(100, self.check_messages)

    def send_message(self, event=None):
        message = self.message_entry.get()
        if message and message != "Type here to chat!":
            if message.lower() == '/quit':
                self.quit_chat()
            elif message.lower() == '/help':
                self.show_help()
            elif message.lower() == '/history':
                self.show_history()
            elif message.startswith('/pm'):
                client.send(message.encode('ascii'))
                self.display_own_message(message)
            else:
                client.send(message.encode('ascii'))
                self.display_own_message(message)
            self.message_entry.delete(0, tk.END)

    def display_own_message(self, message):
        timestamp = time.strftime("%H:%M")
        formatted_message = f"[{timestamp}] {self.username}: {message}"
        self.display_message(formatted_message)

    def display_message(self, message):
        self.chat_log.config(state='normal')
        
        # Regular expression to match the timestamp and username
        pattern = r'(\[\d{2}:\d{2}\]) ([^:]+): '
        
        # Split the message into parts
        parts = re.split(pattern, message)
        
        if len(parts) >= 4:
            timestamp, username, content = parts[1], parts[2], parts[3]
            
            # Insert timestamp
            self.chat_log.insert(tk.END, timestamp + ' ')
            
            # Insert username in bold
            self.chat_log.insert(tk.END, username + ': ', 'bold')
            
            # Insert the rest of the message
            self.chat_log.insert(tk.END, content + '\n')
        else:
            # If the message doesn't match the pattern, insert it as is
            self.chat_log.insert(tk.END, message + '\n')
        
        self.chat_log.config(state='disabled')
        self.chat_log.see(tk.END)

    def show_help(self):
        help_text = """
        Information
        ========================================
        - Type your message and press Enter to send
        - Type 'register:<username>:<password>' to register an account
        - Type 'login:<username>:<password>' to log in
        - Type '/' followed by a command word to use a command

        Command List
        =========================================
        - '/pm <user name> <message>' - sends a private message to user with given user name
        - '/history' - view recent messages
        - '/room <room name>' - switches chat room to matching name
        - '/rlist' - gets a list of chat rooms
        - '/ulist' - gets a list of users in a your chat room
        - '/listall' - get a list of ALL online users
        - '/myroom' - gets the name of your current chatroom
        - '/quit' - exit the chat
        """
        messagebox.showinfo("Help", help_text)

    def show_history(self):
        client.send('/history'.encode('ascii'))

    def change_room(self):
        room = simpledialog.askstring("Change Room", "Enter room name:")
        if room:
            client.send(f'/room {room}'.encode('ascii'))

    def show_users(self):
        client.send('/ulist'.encode('ascii'))

    def quit_chat(self):
        if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
            client.send('/quit'.encode('ascii'))
            self.master.quit()

def main():
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()