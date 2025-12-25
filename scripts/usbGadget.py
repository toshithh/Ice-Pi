import os
import re
from dbConn import DB
from settings import BASE_DIR


class USBGadget:
    def __init__(self):
        self.DB = DB()
        self.enableGadget()

    def enableGadget(self):
        path = "/boot/firmware/config.txt"
        payload = "dtoverlay=dwc2"
        with open(path, "r+") as file:
            lines = file.readlines()
            if any(payload == line.strip() for line in lines):
                return
            insert_index = None
            for i, line in enumerate(lines):
                if re.match(r'^\s*\[[^\]]+\]\s*$', line):
                    insert_index = i
                    break
            if insert_index is not None:
                lines.insert(insert_index, payload + "\n\n")
            else:
                if lines and not lines[-1].endswith("\n"):
                    lines[-1] += "\n"
                lines.append(payload + "\n")
            file.seek(0)
            file.writelines(lines)
            file.truncate()


    def update_cmdline_modules(self, add_modules=None, remove_modules=None, path="scripts/test.conf"):
        add_modules = set(add_modules or [])
        remove_modules = set(remove_modules or [])
        with open(path, "r+") as f:
            parts = f.read().strip().split(" ")
            modules = set()
            new_parts = []
            for part in parts:
                if part.startswith("modules-load="):
                    modules = set(part.split("=", 1)[1].split(","))
                else:
                    new_parts.append(part)
            modules |= add_modules
            modules -= remove_modules
            modules_part = None
            if modules:
                modules_part = "modules-load=" + ",".join(sorted(modules))
            final_parts = []
            inserted = False
            for part in new_parts:
                final_parts.append(part)
                if part == "rootwait" and modules_part and not inserted:
                    final_parts.append(modules_part)
                    inserted = True
            if modules_part and not inserted:
                final_parts.append(modules_part)
            new_cmdline = " ".join(final_parts)
            f.seek(0)
            f.write(new_cmdline)
            f.truncate()


    def __setitem__(self, key: str, value: int):
        """
        ethernet, wifi, ap, storage, hid
        0 -> Disable
        1 -> Enable
        2 -> Bridge
        """
        interfaces = {x: self.DB.Interfaces[x]["enabled"] for x in "ethernet wifi ap storage hid".split()}
        interfaces[key] = value
        self.DB.Interfaces[key] = value
        self.__enable_interfaces(interfaces["ap"], interfaces["ethernet"], interfaces["storage"], interfaces["hid"])
        


    def __enable_interfaces(self, ap0, usb0, storage, hid):
        enabled_modules = ["dwc2"]
        disabled_modules = []
        if usb0:
            enabled_modules.append("g_ether")
            if not os.path.exists("/etc/network/interfaces.d/usb0"):
                os.system(f"sudo cp -r {os.path.join(BASE_DIR, "config", "usb0")} /etc/network/interfaces.d && sudo systemctl restart networking")
            if usb0 == 2:
                os.system(f"sudo {os.path.join(BASE_DIR, "scripts", "ipForward.sh")} forward usb0 wlan0")
        else:
            os.system(f"sudo {os.path.join(BASE_DIR, "scripts", "ipForward.sh")} stop usb0 wlan0")
            os.system("sudo ifconfig usb0 down")
            disabled_modules.append("g_ether")
        if storage:
            enabled_modules.append("g_mass_storage")
        else:
            disabled_modules.append("g_mass_storage")
        if hid:
            enabled_modules.append("g_hid")

        else: 
            disabled_modules.append("g_hid")
        self.update_cmdline_modules(add_modules=enabled_modules, remove_modules=disabled_modules)
        
        if ap0:
            if not os.path.exists("/etc/network/interfaces.d/ap0"):
                os.system(f"sudo cp -r {os.path.join(BASE_DIR, "config", "ap0")} /etc/network/interfaces.d && sudo systemctl restart networking")
            if not os.path.exists("/etc/systemd/system/ap-interface.service"):
                os.system(f"sudo cp -r {os.path.join(BASE_DIR, "service", "ap-interface.service")} /etc/systemd/system && sudo systemctl enable --now ap-interface.service && sudo systemctl restart networking")
            if ap0 == 2:
                os.system(f"sudo {os.path.join(BASE_DIR, "scripts", "ipForward.sh")} forward ap0 wlan0")
        else:
            os.system("sudo ifconfig ap0 down")
            os.system("sudo systemctl disable --now ap-interface.service")
            os.system(f"sudo {os.path.join(BASE_DIR, "scripts", "ipForward.sh")} stop ap0 wlan0")


    def reboot():
        os.system("sudo reboot now")

    def shutdown():
        os.system("sudo shutdown now")

if __name__ == "__main__":
    USBGadget()