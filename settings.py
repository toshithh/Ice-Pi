from scripts.usbGadget import USBGadget
import os
import ssl
from dbConn import *
from shell import Shell
import json


PORT_WS = 11280
PORT_HTTP = 11279

with open("SECRETS", "r") as f:
    secrets = json.loads(f.read())

PASSWORD = secrets["password"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_ctx.load_cert_chain(
    certfile="/var/local/IcePi/certs/ice.pi.crt",
    keyfile="/var/local/IcePi/certs/ice.pi.key"
)
ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
ssl_ctx.set_ciphers("ECDHE+AESGCM")


usbGadget = USBGadget()
db = DB()