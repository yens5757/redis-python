import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    client_socket, client_address = server_socket.accept() # wait for client
    data = client_socket.recv(1024).decode('utf-8')
    split_data = data.split("PING")
    reply_string = ""
    for _ in len(split_data):
        reply_string += b"+PONG\r\n"
    client_socket.sendall(reply_string)  # Convert string to bytes before sending

if __name__ == "__main__":
    main()
