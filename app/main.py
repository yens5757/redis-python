import asyncio
import argparse
import os
import struct

server_config = {
    "dir": None,
    "dbfilename": None
}

meta_data = {}

global_hashmap = {}

def parse_input(data):
    """
    Redis protocol parser
    """
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

def is_file_in_dir(directory, filename):
    """
    Check if file exist in directory
    """
    try:
        file_path = os.path.join(directory, filename)
        return os.path.isfile(file_path)
    except:
        return False

async def handle_client(reader, writer):
    """
    Handle an indiviual client
    """
    global global_hashmap
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
            global_hashmap[result[1]] = result[2]
            writer.write(b"+OK\r\n")
            print(result)
            print(len(result))
            # delete the key after ms waited
            if len(result) > 3 and result[3] == "px" and result[1] in global_hashmap:
                asyncio.create_task(delete_key_after_delay(result[1], int(result[4])))
        elif result[0] == "GET":
            if result[1] in global_hashmap:
                writer.write(f"${len(global_hashmap[result[1]])}\r\n{global_hashmap[result[1]]}\r\n".encode())
            else:
                writer.write(b"$-1\r\n")
        elif result[0] == "CONFIG" and result[1] == "GET":
            if result[2] == "dir":
                writer.write(f"*2\r\n$3\r\ndir\r\n${len(server_config["dir"])}\r\n{server_config["dir"]}\r\n".encode())
            elif result[2] == "dbfilename":
                writer.write(f"*2\r\n$10\r\ndbfilename\r\n${len(server_config["dbfilename"])}\r\n{server_config["dbfilename"]}\r\n".encode())

def parse_metadata(data):
    offset = 0
    while offset < len(data):
        marker = data[offset]
        offset += 1
        if marker == 0xFA:
            try:
                # Read the name of the metadata attribute
                name_length = data[offset]
                offset += 1
                name = data[offset:offset + name_length].decode('utf-8')
                offset += name_length
                
                # Read the value of the metadata attribute
                value_length = data[offset]
                print(data[offset])
                offset += 1
                value = data[offset:offset + value_length].decode('utf-8')
                offset += value_length
                
                meta_data[name] = value
                print(f"Key: {name}, Value: {value}")
            except IndexError:
                print("Error: Reached end of data unexpectedly while parsing metadata.")
                break
        elif marker == 0xFB:
            value = struct.unpack('>I', data[offset:offset+4])[0]
            offset += 4
            print("Numeric Value:", value)
        elif marker == 0xFF: 
            checksum = data[offset:offset+6]
            offset += 6
            print("Checksum:", checksum.hex())
        else:
            print("Unknown marker:", hex(marker))
            break 
        




def read_file(directory, filename):
    file_path = os.path.join(directory, filename)
    with open(file_path, 'rb') as file:
        rdb_content = file.read()
        print(rdb_content)
        header = rdb_content[:9].decode('ascii')
        magic, version = header[:5], header[5:]
        print(f"Magic: {magic}, Version: {version}")
        if magic != "REDIS":
            print("magic is not correct")
            return
        if not version.isdigit():
            print("version is not correct")
            return
        parse_metadata(rdb_content[9:])


async def delete_key_after_delay(key, delay_ms):
    """
    Wait for 'delay_ms' milliseconds and then delete the key.
    """
    await asyncio.sleep(delay_ms / 1000)  # Convert ms to seconds
    del global_hashmap[key]
    print(f"Key '{key}' deleted after {delay_ms} ms.")

async def main():
    # await for more clients while handling the connected client socket
    server = await asyncio.start_server(handle_client, "localhost", 6379)
    address = server.sockets[0].getsockname()
    print(f"Server running on {address}")
    
    async with server:
        await server.serve_forever()



if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Redis-like server")
    parser.add_argument("--dir", required=False, help="Directory to store data files")
    parser.add_argument("--dbfilename", required=False, help="Name of the database file")
    args = parser.parse_args()
    # Configure the server
    server_config["dir"] = args.dir
    server_config["dbfilename"] = args.dbfilename
    if server_config["dir"] and server_config["dbfilename"] and is_file_in_dir(server_config["dir"], server_config["dbfilename"]):
        print("read file")
        read_file(server_config["dir"], server_config["dbfilename"])
        
    asyncio.run(main())