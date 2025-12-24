import os
import re


def enableGadget():
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


def update_cmdline_modules(
    add_modules=None,
    remove_modules=None,
    path="scripts/test.conf"
):
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



def enable_interfaces(ap0=True, usb0=True, storage=False, hid=True):
    enableGadget()
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
    update_cmdline_modules(add_modules=enabled_modules, remove_modules=disabled_modules)
    
    if ap0 and not os.path.exists("/etc/network/interfaces.d/ap0"):
        os.system("sudo cp -r config/ap0 /etc/network/interfaces.d && sudo systemctl restart networking")
    if usb0 and not os.path.exists("/etc/network/interfaces.d/usb0"):
        os.system("sudo cp -r config/usb0 /etc/network/interfaces.d && sudo systemctl restart networking")



if __name__ == "__main__":
    pass