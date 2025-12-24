import asyncio
import json
import secrets
import websockets
import qrcode

PORT = 9000

# Generate one-time QR secret
QR_SECRET = secrets.token_hex(16)

def show_qr():
    payload = {
        "ip": "192.168.0.232",  # CHANGE THIS
        "port": PORT,
        "secret": QR_SECRET
    }
    qr = qrcode.make(json.dumps(payload))
    qr.show()
    print("QR secret:", QR_SECRET)

async def handler(ws):
    print("Client connected")
    await ws.send(json.dumps({ "type": "hello" }))

    try:
        auth = json.loads(await ws.recv())
        if auth["type"] != "auth":
            await ws.close()
            return

        secret = decrypt(auth["data"])
        if secret != QR_SECRET:
            await ws.send(json.dumps({ "type": "error" }))
            await ws.close()
            return

        print("Authenticated")
        await ws.send(json.dumps({ "type": "ok" }))

        async for message in ws:
            packet = json.loads(message)
            if packet["type"] == "ping":
                await ws.send(json.dumps({"type": "pong"}))
            if packet["type"] == "key":
                combo = decrypt(packet["data"])
                print("KEY:", combo)

    except Exception as e:
        print("Connection closed:", e)

async def main():
    show_qr()
    async with websockets.serve(handler, "0.0.0.0", PORT):
        print(f"Server running on ws://0.0.0.0:{PORT}")
        await asyncio.Future()

asyncio.run(main())
