import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    client_socket, client_address = server_socket.accept() # wait for client
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        # Assuming the client sends `PING\r\n`
        command = data.decode('utf-8').strip()
        print(f"Received: {command}")
        if command == "PING":
            client_socket.sendall(b"+PONG\r\n")
        else:
            client_socket.sendall(b"-ERR unknown command\r\n")

if __name__ == "__main__":
    main()
