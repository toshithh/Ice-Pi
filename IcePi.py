import asyncio
import json
import ssl
import websockets
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from dbConn import *
from shell import Shell

PORT_WS = 11280
PORT_HTTP = 11279

with open("SECRETS", "r") as f:
    secrets = json.loads(f.read())

PASSWORD = secrets["password"]


ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_ctx.load_cert_chain(
    certfile="certs/ice.pi.crt",
    keyfile="certs/ice.pi.key"
)

ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
ssl_ctx.set_ciphers("ECDHE+AESGCM")


def reject(msg):
    return json.dumps({"type": "error", "msg": msg})

def success(payload):
    payload["type"] = "success"
    return json.dumps(payload)



async def handler(ws):
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
            elif packet["type"] == "get":
                if packet["class"] == "interfaces":
                    wifi, ap, usb = update_interfaces()
                    await ws.send(success({
                        "wifi": wifi,
                        "ap": ap,
                        "ethernet": usb
                    }))
            elif packet["type"] == "terminal":
                await shell.write_pty(packet["cmd"])
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
