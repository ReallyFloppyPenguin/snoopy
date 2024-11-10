import socket
from socket import ConnectionError

def start_server(host='0.0.0.0', port=65432):
    """
    Start a TCP server that listens for incoming connections from any network.
    
    Args:
        host (str): The hostname or IP address to bind the server to. 
                   '0.0.0.0' means listen on all available network interfaces.
        port (int): The port number to listen on. Default is 65432.
    """
    # Create a TCP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Allow port reuse to avoid "Address already in use" errors
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            # Bind the socket to all interfaces
            server_socket.bind((host, port))
            # Enable the server to accept connections (max 5 queued connections)
            server_socket.listen(5)
            print(f"Server started on all interfaces at port {port}")
            print(f"Local IP addresses:")
            # Display all available network interfaces for connection
            addresses = socket.getaddrinfo(socket.gethostname(), None)
            for addr in addresses:
                if addr[0] == socket.AF_INET:  # Only show IPv4 addresses
                    print(f"  - {addr[4][0]}")

            while True:
                try:
                    # Accept a new connection
                    client_socket, client_address = server_socket.accept()
                    with client_socket:
                        print(f"Connection established with {client_address}")
                        # Receive data from the client
                        data = client_socket.recv(1024)
                        if not data:
                            continue  # Skip to next iteration if no data
                        print(f"Received data: {data.decode('utf-8')}")
                        # Send a response back to the client
                        response = "Data received"
                        client_socket.sendall(response.encode('utf-8'))
                except ConnectionError as e:
                    print(f"Connection error: {e}")
                    continue
                
        except KeyboardInterrupt:
            print("\nServer shutting down...")
        except Exception as e:
            print(f"Error starting server: {e}")