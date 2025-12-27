import os
import re
from dbConn import DB
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class USBGadget:
    def __init__(self):
        print("[USB Gadget]")
        self.DB = DB()
        self.enableGadget()
        self.__start()
        

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
        add_modules = list(add_modules or [])
        remove_modules = set(remove_modules or [])

        BASE_MODULES = ["dwc2", "libcomposite"]

        with open(path, "r+") as f:
            parts = f.read().strip().split(" ")

            existing_modules = []
            new_parts = []

            # Extract existing modules-load
            for part in parts:
                if part.startswith("modules-load="):
                    existing_modules = part.split("=", 1)[1].split(",")
                else:
                    new_parts.append(part)

            # Remove explicitly removed modules
            modules = [m for m in existing_modules if m not in remove_modules]

            # Add requested modules (preserve order)
            for m in add_modules:
                if m not in modules:
                    modules.append(m)

            # Detect whether any libcomposite function is enabled
            has_functions = any(m.startswith("usb_f_") for m in modules)

            final_modules = []

            # Enforce required base modules only if functions exist
            if has_functions:
                for m in BASE_MODULES:
                    if m not in modules:
                        final_modules.append(m)

            # Append remaining modules in preserved order
            for m in modules:
                if m not in final_modules:
                    final_modules.append(m)

            modules_part = None
            if final_modules:
                modules_part = "modules-load=" + ",".join(final_modules)

            # Rebuild cmdline
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

    def __start(self):
        print("[Start]")
        interfaces = {x: self.DB.Interfaces[x]["enabled"] for x in "ethernet wifi ap storage hid".split()}
        self.__enable_interfaces(interfaces["ap"], interfaces["ethernet"], interfaces["storage"], interfaces["hid"])

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

    def __getitem__(self, key):
        return self.DB.Interfaces[key]
        

    def __enable_interfaces(self, ap0, usb0, storage, hid):
        enabled_modules = ["dwc2"]
        disabled_modules = []
        if usb0:
            enabled_modules.append("usb_f_ecm")
            enabled_modules.append("usb_f_rndis")
            print("[Enable] usb_ethernet")
            if not os.path.exists("/etc/network/interfaces.d/usb0"):
                os.system(f"sudo cp -r {os.path.join(BASE_DIR, "config", "usb0")} /etc/network/interfaces.d && sudo systemctl restart networking")
            if usb0 == 2:
                os.system(f"sudo {os.path.join(BASE_DIR, "scripts", "ipForward.sh")} forward usb0 wlan0")
        else:
            print("[Disable] usb_ethernet")
            os.system(f"sudo {os.path.join(BASE_DIR, "scripts", "ipForward.sh")} stop usb0 wlan0")
            os.system("sudo ifconfig usb0 down")
            disabled_modules.append("usb_f_ecm")
            disabled_modules.append("usb_f_rndis")
        if storage:
            enabled_modules.append("usb_f_mass_storage")
        else:
            disabled_modules.append("usb_f_mass_storage")
        if hid:
            enabled_modules.append("usb_f_hid")

        else: 
            disabled_modules.append("usb_f_hid")
        if ap0:
            print("[Enable] AP")
            if not os.path.exists("/etc/network/interfaces.d/ap0"):
                os.system(f"sudo cp -r {os.path.join(BASE_DIR, "config", "ap0")} /etc/network/interfaces.d && sudo systemctl restart networking")
            if not os.path.exists("/etc/systemd/system/ap-interface.service"):
                os.system(f"sudo cp -r {os.path.join(BASE_DIR, "service", "ap-interface.service")} /etc/systemd/system && sudo systemctl enable --now ap-interface.service && sudo systemctl restart networking")
            if ap0 == 2:
                os.system(f"sudo {os.path.join(BASE_DIR, "scripts", "ipForward.sh")} forward ap0 wlan0")
        else:
            print("[Disable] AP")
            os.system("sudo ifconfig ap0 down")
            os.system("sudo systemctl disable --now ap-interface.service")
            os.system(f"sudo {os.path.join(BASE_DIR, "scripts", "ipForward.sh")} stop ap0 wlan0")

        self.update_cmdline_modules(add_modules=enabled_modules, remove_modules=disabled_modules, path="/boot/firmware/cmdline.txt")


    def reboot():
        os.system("sudo reboot now")

    def shutdown():
        os.system("sudo shutdown now")

if __name__ == "__main__":
    USBGadget()