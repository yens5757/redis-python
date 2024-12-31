import asyncio


async def handle_client(reader, writer):
    while True:
        print("TRue")
        data = await reader.read(1024)
        if not data:
            break
        if "PING" in data.decode():
            writer.write("+PONG\r\n".encode())
            await writer.drain()

async def main():
    # await for more clients while handling the connected client socket
    server = await asyncio.start_server(handle_client, "localhost", 6379)
    address = server.sockets[0].getsockname()
    print(f"Server running on {address}")
    
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())