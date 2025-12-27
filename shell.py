import os
import pty
import json
import asyncio

class Shell:
    def __init__(self, ws):
        self.ws = ws
        self.pid, self.fd = pty.fork()

        if self.pid == 0:
            os.execvp("/bin/bash", ["bash"])
        else:
            asyncio.create_task(self.read_pty())

    async def read_pty(self):
        try:
            while True:
                data = os.read(self.fd, 1024)
                await self.ws.send(json.dumps({
                    "type": "success",
                    "class": "terminal",
                    "msg": data.decode(errors="ignore")
                }))
        except Exception:
            pass

    def write_pty(self, data):
        os.write(self.fd, data.encode())
