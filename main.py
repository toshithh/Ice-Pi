import asyncio
import json
import websockets
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from views import *



async def handler(ws: websockets.ServerConnection):
    print("Client connected")
    await ws.send(json.dumps({"type": "connected"}))
    try:
        # ---- AUTH ----
        auth = json.loads(await ws.recv())
        if auth.get("type") != "auth":
            await ws.close()
            return
        if auth.get("password") != PASSWORD:
            await ws.send(reject("Wrong password"))
            await ws.close()
            return
        await ws.send(success({"msg": "Authenticated"}))
        print("Authenticated")
        shell = Shell(ws)
        async for message in ws:
            packet = json.loads(message)
            if packet["type"] == "ping":
                await ws.send(success({"class": "pong"}))
            elif packet["type"] == "terminal":
                await shell.write_pty(packet["cmd"])
            else:
                Response(ws, packet)
    except Exception as e:
        print("WS closed:", e)


async def start_ws():
    async with websockets.serve(
        handler,
        "0.0.0.0",
        PORT_WS,
        ssl=ssl_ctx,
        max_size=2**20
    ):
        print(f"WSS running on wss://0.0.0.0:{PORT_WS}")
        await asyncio.Future()




class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/1c3P1":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"online"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *_):
        pass


def run_http():
    httpd = HTTPServer(("0.0.0.0", PORT_HTTP), Handler)
    httpd.socket = ssl_ctx.wrap_socket(httpd.socket, server_side=True)
    print(f"HTTPS running on https://0.0.0.0:{PORT_HTTP}")
    httpd.serve_forever()


# ---- START ----
threading.Thread(target=run_http, daemon=True).start()
asyncio.run(start_ws())
