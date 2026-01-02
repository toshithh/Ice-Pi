import os
import re
import logging
from dbConn import DB
import subprocess, time, threading, asyncio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


interface_names= "ethernet wifi ap storage hid tor"

DNSBlock = {
    "Ads & Trackers": ["94.140.14.14", "94.140.15.15"],
    "Malware": ["1.1.1.3"],
    "NSFW & Malware": ["1.1.1.2"],
    "Allow all": ["1.1.1.1", "8.8.8.8"]
}

class USBGadget:
    def __init__(self):
        self.DB = DB()
        self.enableGadget()
        self.__start()
        self.last_scan = time.time()
        

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


    def update_cmdline_modules(self, add_modules=None, remove_modules=None, path="/boot/firmware/cmdline.txt"):
        add_modules = list(add_modules or [])
        remove_modules = set(remove_modules or [])

        BASE_MODULES = ["dwc2", "libcomposite"]

        with open(path, "r+") as f:
            parts = f.read().strip().split(" ")

            existing_modules = []
            new_parts = []
            for part in parts:
                if part.startswith("modules-load="):
                    existing_modules = part.split("=", 1)[1].split(",")
                else:
                    new_parts.append(part)
            modules = [m for m in existing_modules if m not in remove_modules]
            for m in add_modules:
                if m not in modules:
                    modules.append(m)
            has_functions = any(m.startswith("usb_f_") for m in modules)
            final_modules = []
            if has_functions:
                for m in BASE_MODULES:
                    if m not in modules:
                        final_modules.append(m)
            for m in modules:
                if m not in final_modules:
                    final_modules.append(m)

            modules_part = None
            if final_modules:
                modules_part = "modules-load=" + ",".join(final_modules)

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
        interfaces = {x: self.DB.Interfaces[x]["enabled"] for x in interface_names.split()}
        self.__enable_interfaces(interfaces["ap"], interfaces["ethernet"], interfaces["storage"], interfaces["hid"], interfaces["tor"])

    
    def __setitem__(self, key: str, value: int):
        """
        Options: ethernet, wifi, ap, storage, hid
        0 -> Disable
        1 -> Enable
        2 -> Bridge (wifi, ap)
        """
        try:
            interfaces = {x: self.DB.Interfaces[x]["enabled"] for x in interface_names.split()}
            self.DB.Interfaces[key] = value
            interfaces[key] = value
            self.__enable_interfaces(interfaces["ap"], interfaces["ethernet"], interfaces["storage"], interfaces["hid"], interfaces["tor"])
        except Exception as err:
            logging.error(f"USBGadget[${key}]\t${err}")
    
    def __getitem__(self, key):
        return self.DB.Interfaces[key]  
    

    def __enable_interfaces(self, ap0, usb0, storage, hid, tor):
        """
        Enable/disable USB functions by loading/unloading kernel modules
        """
        G = "/sys/kernel/config/usb_gadget/g1"
        
        # Unbind gadget before making module changes
        try:
            with open(f"{G}/UDC", "w") as f:
                f.write("")
            logging.info("[-] Unbound USB gadget")
            time.sleep(0.3)
        except:
            pass
        
        # ========== USB ETHERNET (ECM + RNDIS) ==========
        if usb0:
            logging.info("[+] Enable usb_ethernet")
            
            # Load modules
            subprocess.run(["modprobe", "usb_f_ecm"], check=False, capture_output=True)
            subprocess.run(["modprobe", "usb_f_rndis"], check=False, capture_output=True)
            
            # Configure network interface
            if not os.path.exists("/etc/network/interfaces.d/usb0"):
                os.system(f"sudo cp -r {os.path.join(BASE_DIR, 'bash', 'config', 'usb0')} /etc/network/interfaces.d")
                os.system("sudo systemctl restart networking")
            
            # Enable IP forwarding if bridge mode
            if usb0 == 2:
                os.system(f"sudo {os.path.join(BASE_DIR, 'bash', 'scripts', 'ipForward.sh')} forward usb0 wlan0")
        else:
            logging.info("[-] Disable usb_ethernet")
            
            # Stop forwarding and bring down interface
            os.system(f"sudo {os.path.join(BASE_DIR, 'bash', 'scripts', 'ipForward.sh')} stop usb0 wlan0")
            os.system("sudo ifconfig usb0 down")
            
            # Unload modules
            subprocess.run(["modprobe", "-r", "usb_f_ecm"], check=False, capture_output=True)
            subprocess.run(["modprobe", "-r", "usb_f_rndis"], check=False, capture_output=True)
        
        # ========== USB MASS STORAGE ==========
        if storage:
            logging.info("[+] Enable mass_storage")
            subprocess.run(["modprobe", "usb_f_mass_storage"], check=False, capture_output=True)
        else:
            logging.info("[-] Disable mass_storage")
            subprocess.run(["modprobe", "-r", "usb_f_mass_storage"], check=False, capture_output=True)
        
        # ========== USB HID KEYBOARD ==========
        if hid:
            logging.info("[+] Enable hid")
            subprocess.run(["modprobe", "usb_f_hid"], check=False, capture_output=True)
            time.sleep(0.3)
            os.system("sudo chmod 666 /dev/hidg0 2>/dev/null")
        else:
            logging.info("[-] Disable hid")
            subprocess.run(["modprobe", "-r", "usb_f_hid"], check=False, capture_output=True)
        
        # ========== ACCESS POINT (AP0) ==========
        if ap0:
            logging.info("[+] Enable AP")
            
            if not os.path.exists("/etc/network/interfaces.d/ap0"):
                os.system(f"sudo cp -r {os.path.join(BASE_DIR, 'bash', 'config', 'ap0')} /etc/network/interfaces.d")
                os.system("sudo systemctl restart networking")
            
            if not os.path.exists("/etc/systemd/system/ap-interface.service"):
                os.system(f"sudo cp -r {os.path.join(BASE_DIR, 'bash', 'service', 'ap-interface.service')} /etc/systemd/system")
                os.system("sudo systemctl enable --now ap-interface.service")
                os.system("sudo systemctl restart networking")
            if ap0 == 2:
                os.system(f"sudo {os.path.join(BASE_DIR, 'bash', 'scripts', 'ipForward.sh')} forward ap0 wlan0")
        else:
            logging.info("[-] Disable AP")
            os.system("sudo ifconfig ap0 down")
            os.system("sudo systemctl disable --now ap-interface.service")
            os.system(f"sudo {os.path.join(BASE_DIR, 'bash', 'scripts', 'ipForward.sh')} stop ap0 wlan0")

        # ========== Tor ==========
        if tor:
            if ap0 == 2:
                os.system(f"sudo {os.path.join(BASE_DIR, 'bash', 'scripts', 'ipForward.sh')} stop ap0 wlan0")
            os.system(f"sudo {os.path.join(BASE_DIR, 'bash', 'scripts', 'tor.sh')} forward ap0 wlan0")
            if usb0 == 2:
                os.system(f"sudo {os.path.join(BASE_DIR, 'bash', 'scripts', 'ipForward.sh')} stop usb0 wlan0")
            os.system(f"sudo {os.path.join(BASE_DIR, 'bash', 'scripts', 'tor.sh')} forward usb0 wlan0")
            replace_dnsmasq_servers(["127.0.0.1#5353"])
            os.system("sudo systemctl restart dnsmasq")
        else:
            os.system(f"sudo {os.path.join(BASE_DIR, 'bash', 'scripts', 'tor.sh')} stop ap0 wlan0")
            if ap0 == 2:
                os.system(f"sudo {os.path.join(BASE_DIR, 'bash', 'scripts', 'ipForward.sh')} forward ap0 wlan0")
            os.system(f"sudo {os.path.join(BASE_DIR, 'bash', 'scripts', 'tor.sh')} stop usb0 wlan0")
            if usb0 == 2:
                os.system(f"sudo {os.path.join(BASE_DIR, 'bash', 'scripts', 'ipForward.sh')} forward usb0 wlan0")
            replace_dnsmasq_servers(DNSBlock[self.DB.Settings["DNSBlock"]])
            os.system("sudo systemctl restart dnsmasq")
        
        # Wait for module changes to settle
        time.sleep(0.5)
        
        # Restart USB gadget service to apply modules
        result = subprocess.run(
            ["systemctl", "restart", "usb-gadget.service"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info("[+] Restarted USB gadget service")
        else:
            logging.error(f"[-] Error Failed to restart gadget: {result.stderr}")

    
    def _ensure_modules_in_cmdline(self):
        """
        Ensure all USB function modules are loaded at boot
        This only needs to run once during setup
        """
        required_modules = [
            "dwc2",
            "libcomposite", 
        ]
        
        path = "/boot/firmware/cmdline.txt"
        
        with open(path, "r") as f:
            cmdline = f.read().strip()
        if "modules-load=" in cmdline:
            parts = cmdline.split()
            for part in parts:
                if part.startswith("modules-load="):
                    current_modules = part.split("=", 1)[1].split(",")
                    missing = [m for m in required_modules if m not in current_modules]
                    
                    if missing:
                        self.update_cmdline_modules(add_modules=missing, path=path)
                        logging.info(f"[+] Added to cmdline.txt {', '.join(missing)}")
                    break
        else:
            self.update_cmdline_modules(add_modules=required_modules, path=path)
            logging.info(f"[+] Added to cmdline.txt All USB modules")

    
    async def wifi_scan(self, option="list", interface="wlan0"):
        loop = asyncio.get_running_loop()
        def _list():
            try:
                return subprocess.run(
                    ["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY",
                    "device", "wifi", "list", "ifname", interface, "--rescan", "no"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                ).stdout.splitlines()
            except:
                return []
        _aps = await loop.run_in_executor(None, _list)
        aps = []
        for x in _aps:
            if not x:
                continue
            res = x.split(":")
            if len(res) >= 4:
                aps.append({
                    "in-use": res[0].strip(),
                    "ssid": res[1],
                    "strength": res[2],
                    "auth": res[3],
                })
        if option == "rescan":
            ls = time.time()
            if ls - self.last_scan > 5:
                self.last_scan = ls
                threading.Thread(
                    target=lambda: os.system(f"nmcli device wifi rescan ifname {interface}"),
                    daemon=True
                ).start()
        return aps

    def wifi_connect(self, ssid, password=None, interface="wlan0"):
        cmd = [
            "nmcli", "device", "wifi", "connect", f"{ssid}",
        ]
        if password:
            cmd.extend(["password", password])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        print(result)
        if result.returncode == 0:
            logging.info(f"USBGadget:wifi_connect\t{result.stdout}")
            return True
        else:
            try:
                result = subprocess.run(
                    ["nmcli", "connection", "delete", ssid],
                    capture_output=True,
                    text=True,
                    timeout=5
                    )
            except: pass
            logging.error(f"USBGadget:wifi_connect\t{result.stderr}")
            return result.stderr


    def changeDNS(self, value: str):
        try:
            if value in DNSBlock.keys():
                self.DB.Settings["DNSBlock"] = value
                replace_dnsmasq_servers(DNSBlock[value])
                logging.info(f"USBGadget:ChangeDNS\tDNS changed to ${value}:${DNSBlock[value]}")
            return True
        except Exception as err:
            logging.error(f"USBGadget:ChangeDNS\t{err}")
            return False
        


    def reboot(self):
        os.system("sudo reboot now")

    def shutdown(self):
        os.system("sudo shutdown now")


def replace_dnsmasq_servers(servers, conf_path="/etc/dnsmasq.conf"):
    """
    Replace all 'server=' lines in dnsmasq
    """
    with open(conf_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        if not line.lstrip().startswith("server="):
            new_lines.append(line)

    for srv in servers:
        new_lines.append(f"server={srv}\n")

    with open(conf_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    USBGadget()