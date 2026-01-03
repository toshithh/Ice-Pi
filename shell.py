import os
import pty
import json
import asyncio
import threading
import select
import logging
from queue import Queue
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Shell:
    def __init__(self, ws, loop):
        self.ws = ws
        self.loop = loop
        self.running = True
        self.fd = None
        self.pid = None
        self.thread = None
        self.output_queue = Queue()
        
        try:
            self.pid, self.fd = pty.fork()
            
            if self.pid == 0:
                # Child process - start clean bash
                os.environ['TERM'] = 'dumb'  # ← Disable fancy formatting
                os.environ['PS1'] = '$ '  # ← Simple prompt via env
                os.execvp("/bin/bash", ["bash", "--norc", "--noprofile"])  # ← No configs
            else:
                # Parent process
                self.thread = threading.Thread(target=self._read_pty_thread, daemon=True)
                self.thread.start()
                
                asyncio.create_task(self._send_loop())
                
                logger.info(f"Shell started with PID {self.pid}")
        except Exception as e:
            logger.error(f"Failed to initialize shell: {e}")

    def _read_pty_thread(self):
        logger.info("PTY read thread started")
        
        while self.running:
            try:
                if self.fd is None:
                    break
                    
                readable, _, _ = select.select([self.fd], [], [], 0.08)
                
                if readable:
                    try:
                        data = os.read(self.fd, 1024)
                        if data:
                            decoded = data.decode(errors="ignore")
                            logger.info(f"Read from PTY: {repr(decoded[:50])}")
                            
                            # Schedule send with error handling
                            try:
                                future = asyncio.run_coroutine_threadsafe(
                                    self._send_output(decoded),
                                    self.loop
                                )
                                # Wait for result with timeout to catch errors
                                future.result(timeout=2.0)
                            except Exception as e:
                                logger.error(f"Error scheduling send: {e}", exc_info=True)
                                # Don't break - keep trying
                        else:
                            break
                    except OSError as e:
                        if self.running:
                            logger.error(f"OSError: {e}")
                        break
                        
            except Exception as e:
                logger.error(f"Read error: {e}", exc_info=True)
                if self.running:
                    continue
                break
        
        logger.info("PTY read thread stopped")
    
    async def _send_output(self, msg):
        try:
            logger.info(f"Sending output: {repr(msg[:50])}")
            message = json.dumps({
                "type": "success",
                "class": "terminal",
                "msg": msg
            })
            logger.info(f"JSON message: {message[:100]}")
            await self.ws.send(message)
            logger.info("Send successful")
        except Exception as e:
            logger.error(f"Send error: {e}", exc_info=True)
            self.running = False
    
    def write_pty(self, data):
        if not self.running or self.fd is None:
            logger.warning("PTY not available")
            return
            
        try:
            if not data.endswith('\n'):
                data = data + '\n'
            logger.info(f"Writing to PTY: {repr(data)}")
            os.write(self.fd, data.encode())
        except Exception as e:
            logger.error(f"Write error: {e}", exc_info=True)
    
    def close(self):
        logger.info("Closing shell...")
        self.running = False
        
        if self.fd is not None:
            try:
                os.close(self.fd)
                logger.info("FD closed")
            except Exception as e:
                logger.error(f"Error closing fd: {e}")
            finally:
                self.fd = None
        
        if self.pid is not None:
            try:
                os.kill(self.pid, 9)
                os.waitpid(self.pid, 0)
                logger.info(f"Process {self.pid} killed")
            except Exception as e:
                logger.error(f"Error killing process: {e}")
            finally:
                self.pid = None
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
            logger.info("Thread joined")