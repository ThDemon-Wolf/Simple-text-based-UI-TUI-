# client.py
"""
A TCP socket-based chat client using Tkinter for GUI. Supports real-time messaging,
emoji parsing, URL highlighting, @mentions, and direct messages with co-admin assignment.

Each function includes documentation with:
- Function: Name of the function
- Variables: Key parameters or instance attributes
- Purpose: What the function accomplishes
"""

import socket
import threading
import tkinter as tk
import queue
import re
from tkinter import simpledialog, scrolledtext, messagebox

HOST = '127.0.0.1'
PORT = 5000

# Emoji replacement mapping
EMOJI_MAP = {
    ":thumbsup:": "\U0001F44D",
    ":smile:": "\U0001F604",
    ":heart:": "❤️",
    ":fire:": "\U0001F525",
    ":laugh:": "\U0001F606"
}

# Regex for detecting URLs and mentions
URL_PATTERN = r"(https?://\S+)"
MENTION_PATTERN = r"@(\w+)"

class ChatClient:
    def __init__(self, master):
        """
        Function: __init__
        Variables:
            - master: Tk root window
        Purpose: Initializes GUI layout, connects to server, starts message receiving thread.
        """
        self.master = master
        self.master.title("Simple Chat Client")

        self.chat_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, state='disabled', height=20)
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.entry_field = tk.Text(master, height=3)
        self.entry_field.pack(padx=10, pady=(0, 10), fill=tk.X)
        self.entry_field.bind("<Return>", self.send_message)

        self.send_button = tk.Button(master, text="Send", command=self.send_message)
        self.send_button.pack(pady=(0, 10))

        self.admin_button = tk.Button(master, text="Assign Co-Admin", command=self.assign_coadmin)
        self.admin_button.pack(pady=(0, 10))

        self.message_queue = queue.Queue()
        self.running = True
        self.admins = set()

        self.name = simpledialog.askstring("Username", "Enter your name:", parent=self.master)
        if not self.name:
            self.master.destroy()
            return

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((HOST, PORT))
        except:
            self.show_message("[ERROR] Could not connect to server.")
            return

        self.recv_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.recv_thread.start()
        self.update_chat_window()

    def receive_messages(self):
        """
        Function: receive_messages
        Purpose: Runs in a separate thread. Listens for messages from the server and queues them for GUI display.
        """
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode()
                if not message:
                    break
                self.message_queue.put(message)
            except:
                break

    def send_message(self, event=None):
        """
        Function: send_message
        Variables:
            - event: Trigger event (Return key or Send button)
        Purpose: Reads user's input, formats it, and sends to server. Displays locally as well.
        """
        message = self.entry_field.get("1.0", tk.END).strip()
        if message:
            full_message = f"{self.name}: {message}"
            try:
                self.client_socket.send(full_message.encode())
                self.show_message(full_message)
            except:
                self.show_message("[ERROR] Message could not be sent.")
        self.entry_field.delete("1.0", tk.END)
        return 'break'

    def show_message(self, message):
        """
        Function: show_message
        Variables:
            - message: Message string to display
        Purpose: Displays messages with emoji replacements, clickable URLs, and @mention highlights.
        """
        for code, emoji in EMOJI_MAP.items():
            message = message.replace(code, emoji)

        self.chat_area.config(state='normal')
        start_index = self.chat_area.index(tk.END)
        self.chat_area.insert(tk.END, message + '\n')
        end_index = self.chat_area.index(tk.END)

        urls = re.findall(URL_PATTERN, message)
        for url in urls:
            idx = self.chat_area.search(url, start_index, stopindex=end_index)
            if idx:
                self.chat_area.tag_add("url", idx, f"{idx}+{len(url)}c")
                self.chat_area.tag_config("url", foreground="blue", underline=True)

        mentions = re.findall(MENTION_PATTERN, message)
        for mention in mentions:
            m_str = f"@{mention}"
            idx = self.chat_area.search(m_str, start_index, stopindex=end_index)
            if idx:
                self.chat_area.tag_add("mention", idx, f"{idx}+{len(m_str)}c")
                self.chat_area.tag_config("mention", foreground="green", font="bold")

        self.chat_area.yview(tk.END)
        self.chat_area.config(state='disabled')

    def assign_coadmin(self):
        """
        Function: assign_coadmin
        Purpose: Promotes another user to co-admin by name and notifies them.
        """
        username = simpledialog.askstring("Assign Co-Admin", "Enter username to promote:", parent=self.master)
        if username:
            self.admins.add(username)
            self.send_direct_message(username, f"You are now a co-admin, @{username} :thumbsup:")
            self.show_message(f"[ADMIN] @{username} was promoted to co-admin!")

    def send_direct_message(self, recipient, message):
        """
        Function: send_direct_message
        Variables:
            - recipient: Username to receive the message
            - message: Message to send
        Purpose: Sends private message tagged with recipient’s name
        """
        if recipient:
            full_message = f"{self.name} (to @{recipient}): {message}"
            try:
                self.client_socket.send(full_message.encode())
                self.show_message(full_message)
            except:
                self.show_message("[ERROR] Direct message failed.")

    def update_chat_window(self):
        """
        Function: update_chat_window
        Purpose: Periodically checks for new messages from the queue and displays them.
        """
        try:
            while True:
                message = self.message_queue.get_nowait()
                self.show_message(message)
        except queue.Empty:
            pass
        if self.running:
            self.master.after(100, self.update_chat_window)

    def close(self):
        """
        Function: close
        Purpose: Gracefully shuts down socket and closes the window when exiting.
        """
        self.running = False
        try:
            self.client_socket.shutdown(socket.SHUT_RDWR)
            self.client_socket.close()
        except:
            pass
        self.master.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    client = ChatClient(root)
    root.protocol("WM_DELETE_WINDOW", client.close)
    root.mainloop()
