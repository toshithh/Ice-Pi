import json
from settings import *
import websockets
from scripts.keyboard import KeyboardExecutor

######## Helpers ########
def reject(msg, hard=False):
    if hard:
        return json.dumps({"type": "authError", "msg": msg})    
    return json.dumps({"type": "error", "msg": msg})

def success(payload):
    payload["type"] = "success"
    return json.dumps(payload)


######### Main Functions #########

def Response(ws: websockets.ServerConnection, packet):
    async def empty():
        return
    routes = {
        "interfaces": interface_info,
        "base_info": base_info,
    }
    try:
        return (routes[packet["class"]](ws, packet))
    except Exception as err:
        print(err)
        return empty()
    

keyboard = KeyboardExecutor()

def HIDExecutor(ws: websockets.ServerConnection, packet):
    try:
        if(packet["type"] == "key"):
            keyboard.press_combo(packet["data"])
    except Exception as err:
        print("HIDExecutor:", err)





######### VIEWS #########


async def base_info():
    pass



async def interface_info(ws: websockets.ServerConnection, packet):
    print("Interfaces called")
    await ws.send(
        success({
            "wifi": usbGadget["wifi"],
            "ap": usbGadget["ap"],
            "ethernet": usbGadget["ethernet"],
            "storage": usbGadget["storage"],
            "hid": usbGadget["hid"],
            "stamp": packet["stamp"]
        })
    )