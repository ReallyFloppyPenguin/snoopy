import socket
import socket

def start_server(host='127.0.0.1', port=65432):
    """
    Start a simple TCP server that listens for incoming connections.
    
    Args:
        host (str): The hostname or IP address to bind the server to. Default is localhost.
        port (int): The port number to listen on. Default is 65432.
    """
    # Create a TCP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Bind the socket to the specified host and port
        server_socket.bind((host, port))
        # Enable the server to accept connections (max 5 queued connections)
        server_socket.listen(5)
        print(f"Server started at {host}:{port}. Waiting for connections...")

        while True:
            # Accept a new connection
            client_socket, client_address = server_socket.accept()
            with client_socket:
                print(f"Connection established with {client_address}")
                # Receive data from the client
                data = client_socket.recv(1024)
                if not data:
                    break  # Exit if no data is received
                print(f"Received data: {data.decode('utf-8')}")
                # Send a response back to the client
                response = "Data received"
                client_socket.sendall(response.encode('utf-8'))

# Uncomment the following line to start the server when this script is run
# start_server()
