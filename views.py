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
        "interface_info": interface_info,
        "base_info": base_info,
        "enable_interface": enable_interface,
        "disable_interface": disable_interface,
        "power_off": power_off
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
            "tor": usbGadget["tor"],
            "stamp": packet["stamp"]
        })
    )

async def enable_interface(ws: websockets.ServerConnection, packet):
    print("Enable Interface")
    print(packet)
    print()
    try:
        usbGadget[packet["name"]] = 2 if (packet["bridge"]) else 1
        await ws.send(success({
            "stamp": packet["stamp"]
        }))
    except Exception as err:
        print(err)
        await ws.send(reject({"stamp": packet["stamp"], "dtl": str(err)}))


async def disable_interface(ws: websockets.ServerConnection, packet):
    print("Disable Interface")
    print(packet)
    print()
    try:
        usbGadget[packet["name"]] = 0
        await ws.send(success({
            "stamp": packet["stamp"]
        }))
    except Exception as err:
        print(err)
        await ws.send(reject({"stamp": packet["stamp"], "dtl": str(err)}))


async def power_off(ws: websockets.ServerConnection, packet):
    if(packet["mode"] == "reboot"):
        await ws.send(success({
            "stamp": packet["stamp"],
            "dtl": "Rebooting!"
        }))
        usbGadget.reboot()
    elif (packet["mode"] == "shutdown"):
        await ws.send(success({
            "stamp": packet["stamp"],
            "dtl": "Rebooting!"
        }))
        usbGadget.shutdown()