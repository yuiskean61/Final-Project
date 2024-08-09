import socket
import threading
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox
from PIL import Image, ImageTk

# client config
HOST = '127.0.0.1'
PORT = 1024

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
messages = []

class ChatApp:
    def __init__(self, master):
        self.master = master
        self.master.title("HumberChat")
        self.master.geometry("400x600")
        self.master.minsize(300, 400)
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
        
        self.create_login_window()
        # Schedule logo loading after mainloop starts
        self.master.after(100, self.load_and_display_logo)

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

        connect_button = tk.Button(self.login_frame, text="Connect", command=self.connect, 
                                   bg=self.primary_color, fg="white", font=self.bold_font)
        connect_button.pack(pady=10)

    def load_and_display_logo(self):
        try:
            image = Image.open("humber_logo.jpg")
            image = image.resize((150, 75), Image.Resampling.LANCZOS)
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

    def on_entry_click(self, event):
        if self.message_entry.get() == "Type here to chat!":
            self.message_entry.delete(0, tk.END)
            self.message_entry.config(fg=self.text_color)

    def on_focusout(self, event):
        if self.message_entry.get() == "":
            self.message_entry.insert(0, "Type here to chat!")
            self.message_entry.config(fg='grey')

    def connect(self):
        self.username = self.username_entry.get()
        if not self.username:
            messagebox.showerror("Error", "Please enter a username")
            return

        try:
            client.connect((HOST, PORT))
            client.send(f"USERNAME:{self.username}".encode('ascii'))
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
                if ':' in message:
                    username, content = message.split(':', 1)
                    formatted_message = f"{username}: {content.strip()} - {timestamp}"
                    alignment = 'right' if username == self.username else 'left'
                else:
                    formatted_message = f"{message} - {timestamp}"
                    alignment = 'left'
                self.master.after(0, self.display_message, formatted_message, alignment)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def send_message(self, event=None):
        message = self.message_entry.get()
        if message and message != "Type here to chat!":
            client.send(message.encode('ascii'))
            timestamp = time.strftime("%H:%M")
            formatted_message = f"{self.username}: {message} - {timestamp}"
            self.display_message(formatted_message, 'right')
            self.message_entry.delete(0, tk.END)

    def display_message(self, message, alignment):
        self.chat_log.config(state='normal')
        self.chat_log.insert(tk.END, message + '\n\n')
        last_line_index = self.chat_log.index(tk.END + "-2l")
        self.chat_log.tag_add(alignment, last_line_index, tk.END)
        self.chat_log.tag_config('left', justify='left')
        self.chat_log.tag_config('right', justify='right')
        
        if ':' in message:
            username_end = message.index(':')
            self.chat_log.tag_add('bold', last_line_index, f"{last_line_index}+{username_end}c")
            self.chat_log.tag_config('bold', font=self.bold_font)
        
        self.chat_log.config(state='disabled')
        self.chat_log.see(tk.END)

def main():
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()