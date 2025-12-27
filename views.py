import json
from settings import *
import websockets

######## Helpers ########
def reject(msg):
    return json.dumps({"type": "error", "msg": msg})

def success(payload):
    payload["type"] = "success"
    return json.dumps(payload)


######### Main Functions #########

def Response(ws: websockets.ServerConnection, packet):
    routes = {
        "interfaces": interface_info,
        "base_info": base_info,
    }
    return (routes[packet["class"]](ws, packet))




######### VIEWS #########


async def base_info():
    pass



async def interface_info(ws: websockets.ServerConnection, packet):
    await ws.send(
        success({
            "wifi": usbGadget["wifi"],
            "ap": usbGadget["ap"],
            "ethernet": usbGadget["ethernet"],
            "storage": usbGadget["storage"],
            "hid": usbGadget["hid"],
            "msg_stamp": packet["msg_stamp"]
        })
    )