# server.py
"""
A multi-threaded TCP socket chat server that accepts multiple clients,
handles incoming messages, and reflects messages to all other active clients.

Each function includes documentation with:
- Function: Name of the function
- Variables: Key parameters or instance attributes
- Purpose: What the function accomplishes
"""

import socket
import threading

HOST = '127.0.0.1'  # Localhost or replace with IP address for deployment
PORT = 5000         # Port to listen on
clients = []        # List to track active client sockets
lock = threading.Lock()  # For thread-safe modifications to the client list

def broadcast(message, sender_socket):
    """
    Function: broadcast
    Variables:
        - message: Bytes message to send
        - sender_socket: The socket of the sender to exclude
    Purpose: Sends a message to all clients except the sender.
    """
    with lock:
        for client in clients:
            if client != sender_socket:
                try:
                    client.send(message)
                except:
                    clients.remove(client)

def handle_client(client_socket, addr):
    """
    Function: handle_client
    Variables:
        - client_socket: Socket connected to the client
        - addr: Client address
    Purpose: Handles incoming messages from a specific client and broadcasts them.
    """
    with client_socket:
        print(f"[NEW CONNECTION] {addr} connected.")
        while True:
            try:
                message = client_socket.recv(1024)
                if not message:
                    break
                broadcast(message, client_socket)
            except:
                break
        with lock:
            if client_socket in clients:
                clients.remove(client_socket)
        print(f"[DISCONNECT] {addr} disconnected.")

def start_server():
    """
    Function: start_server
    Purpose: Initializes and starts the chat server to accept multiple client connections.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[LISTENING] Server listening on {HOST}:{PORT}")

    try:
        while True:
            client_socket, addr = server.accept()
            with lock:
                clients.append(client_socket)
            thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            thread.start()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Server is shutting down.")
    finally:
        server.close()

if __name__ == '__main__':
    start_server()