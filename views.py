import json
from settings import *
import websockets
from gadget.keyboard import KeyboardExecutor
import logging
import asyncio
from gadget.usbGadget import DNSBlock


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

######## Helpers ########
def reject(msg, hard=False):
    if hard:
        return json.dumps({"type": "authError", "msg": msg})    
    return json.dumps({"type": "error", "msg": msg})

def success(payload):
    payload["type"] = "success"
    return json.dumps(payload)

async def error(ws:websockets, packet, err=""):
    return await ws.send({"stamp": packet["stamp"], "type": "error", "msg": str(err)})


######### Main Functions #########

def Response(ws: websockets.ServerConnection, packet):
    
    routes = {
        "interface_info": interface_info,
        "base_info": base_info,
        "enable_interface": enable_interface,
        "disable_interface": disable_interface,
        "power_off": power_off,
        "wifi_scan": wifi_scan,
        "change_dns": change_dns,
        "wifi_connect": wifi_connect
    }
    try:
        return (routes[packet["class"]](ws, packet))
    except Exception as err:
        print("Response", err)
        return error(ws, packet, str(err))
    

keyboard = KeyboardExecutor()

def HIDExecutor(ws: websockets.ServerConnection, packet):
    try:
        if(packet["type"] == "key"):
            keyboard.press_combo(packet["data"])
        elif(packet["type"] == "bulk-type"):
            keyboard.bulk_type(packet["data"])
        elif(packet["type"] == "bulk-paste"):
            keyboard.bulk_type(packet["data"])
    except Exception as err:
        print("HIDExecutor:", err)





######### VIEWS #########


async def base_info(ws: websockets.ServerConnection, packet):
    logging.info("Request:base_info")
    try:
        await ws.send(
            success({
                "interfaces": {
                    "wifi": usbGadget["wifi"],
                    "ap": usbGadget["ap"],
                    "ethernet": usbGadget["ethernet"],
                    "storage": usbGadget["storage"],
                    "hid": usbGadget["hid"],
                    "tor": usbGadget["tor"],
                },
                "storage": {
                    "total": "",
                    "free": "",
                },
                "dns_block": db.Settings["DNSBlock"],
                "dns_options": list(DNSBlock.keys()),
                "stamp": packet["stamp"]
            })
        )
    except Exception as err:
        logging.error(f"Request:base_info\t${err}")
        print(err)
        await error(ws, packet, str(err))



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
    logging.info(f"Request:enable_interface\t${packet['name']}")
    try:
        usbGadget[packet["name"]] = 2 if (packet["bridge"]) else 1
        await ws.send(success({
            "stamp": packet["stamp"]
        }))
    except Exception as err:
        logging.error(f"Request:enable_interface\t${err}")
        await error(ws, packet, str(err))


async def disable_interface(ws: websockets.ServerConnection, packet):
    logging.info(f"Request:disable_interface\t${packet['name']}")
    try:
        usbGadget[packet["name"]] = 0
        await ws.send(success({
            "stamp": packet["stamp"]
        }))
    except Exception as err:
        logging.error(f"Request:disable_interface\t${err}")
        await error(ws, packet, str(err))


async def power_off(ws: websockets.ServerConnection, packet):
    if(packet["mode"] == "reboot"):
        await ws.send(success({
            "stamp": packet["stamp"],
            "dtl": "Rebooting!"
        }))
        asyncio.sleep(1)
        usbGadget.reboot()
    elif (packet["mode"] == "shutdown"):
        await ws.send(success({
            "stamp": packet["stamp"],
            "dtl": "Rebooting!"
        }))
        asyncio.sleep(1)
        usbGadget.shutdown()

async def wifi_scan(ws: websockets.ServerConnection, packet):
    try:
        await ws.send(success({
            "stamp": packet["stamp"],
            "wifi_list": await usbGadget.wifi_scan(option=packet["category"])
        }))
    except Exception as err:
        logging.error(f"Response:wifi_scan\t{packet['category']}\t{err}")
        await error(ws, packet, str(err))

async def wifi_connect(ws: websockets.ServerConnection, packet):
    try:
        connection = usbGadget.wifi_connect(packet["ssid"], packet["password"])
        if connection == True:
            await ws.send(success({
                "stamp": packet["stamp"],
                "msg": "Connected"
            }))
        else:
            await error(ws, packet, connection)
    except Exception as err:
        logging.error(f"Request:wifi_scan\t{packet['ssid']}\t{err}")
        await error(ws, packet, str(err))


async def change_dns(ws: websockets.ServerConnection, packet):
    logging.info(f"Request:ChangeDNS\tTO: {packet['data']}")
    try:
        usbGadget.changeDNS(packet["data"])
        await ws.send(success({"stamp": packet["stamp"]}))
    except Exception as err:
        logging.error(f"Request:ChangeDNS\t{packet['data']}\t{err}")
        await error(ws, packet, str(err))
        
