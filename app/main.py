import asyncio
from app.redis_protocol_parser import RedisProtocolParser

async def handle_client(reader, writer):
    while True:
        data = await reader.read(1024)
        if not data:
            break
        parser = RedisProtocolParser()
        result = parser.parse(data)
        if result[0] == "ECHO":
            writer.write(result[1].encode())
        elif result[0] == "PING":
            writer.write(b"+PONG\r\n")

        
async def main():
    # await for more clients while handling the connected client socket
    server = await asyncio.start_server(handle_client, "localhost", 6379)
    address = server.sockets[0].getsockname()
    print(f"Server running on {address}")
    
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())