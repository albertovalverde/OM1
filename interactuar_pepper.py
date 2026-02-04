import asyncio
import websockets
import sys

async def send_message():
    uri = "ws://localhost:8766"
    try:
        async with websockets.connect(uri) as websocket:
            print("--- Conectado a Pepper ---")
            print("Escribe tu mensaje y pulsa Enter para enviarlo (Ctrl+C para salir):")
            while True:
                message = input("> ")
                if message.strip():
                    await websocket.send(message)
                    response = await websocket.recv()
                    print(f"Pepper recibió: {message}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(send_message())
    except KeyboardInterrupt:
        print("\nDesconectado.")
