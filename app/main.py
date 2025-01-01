import asyncio

db = {}
def parse_input(data):
    if not data:
        raise ValueError("No data to parse")
    first_byte = data[0]
    if first_byte == b"+"[0]:  # Simple String
        return data[1:].decode().strip()
    elif first_byte == b"-"[0]:  # Error
        return {"error": data[1:].decode().strip()}
    elif first_byte == b":"[0]:  # Integer
        return int(data[1:].strip())
    elif first_byte == b"$"[0]:  # Bulk String
        lines = data.split(b"\r\n")
        length = int(lines[0][1:])
        if length == -1:
            return None  # Null bulk string
        return lines[1].decode()
    elif first_byte == b"*"[0]:  # Array
        lines = data.split(b"\r\n")
        num_elements = int(lines[0][1:])
        if num_elements == 0:
            return []  # Empty array
        result = []
        i = 1
        # go through each elements in the array
        while i < num_elements * 2:
            line = lines[i]
            if line.startswith(b"$"):
                result.append(lines[i + 1].decode())
                i += 1
            i += 1
        return result
    else:
        raise ValueError("Unknown RESP type")

async def handle_client(reader, writer):
    global db
    while True:
        data = await reader.read(1024)
        if not data:
            break
        result = parse_input(data)
        # after parsing, process the input
        if result[0] == "ECHO":
            writer.write(f"+{result[1]}\r\n".encode())
        elif result[0] == "PING":
            writer.write(b"+PONG\r\n")
        elif result[0] == "SET":
            db[result[1]] = result[2]
            writer.write(b"+OK\r\n")
        elif result[0] == "GET":
            if result[1] in db:
                writer.write(f"${len(db[result[1]])}\r\n{db[result[1]]}\r\n".encode())
            else:
                writer.write(b"$-1\r\n")
        
async def main():
    # await for more clients while handling the connected client socket
    server = await asyncio.start_server(handle_client, "localhost", 6379)
    address = server.sockets[0].getsockname()
    print(f"Server running on {address}")
    
    async with server:
        await server.serve_forever()



if __name__ == "__main__":
    asyncio.run(main())