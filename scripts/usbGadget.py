import os
import re
from dbConn import DB



class USBGadget:
    def __init__(self, DB: DB):
        self.DB = DB
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
        else:
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
        
        if ap0 and not os.path.exists("/etc/network/interfaces.d/ap0"):
            os.system("sudo cp -r config/ap0 /etc/network/interfaces.d && sudo systemctl restart networking")
        if usb0 and not os.path.exists("/etc/network/interfaces.d/usb0"):
            os.system("sudo cp -r config/usb0 /etc/network/interfaces.d && sudo systemctl restart networking")


    def reboot():
        os.system("sudo reboot now")

    def shutdown():
        os.system("sudo shutdown now")

if __name__ == "__main__":
    USBGadget(DB())