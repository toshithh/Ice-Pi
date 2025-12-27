#!/bin/bash
set -e

CFG=/sys/kernel/config
G=$CFG/usb_gadget/g1

# Mount configfs if not mounted
mountpoint -q $CFG || mount -t configfs none $CFG

# Clean up existing gadget
if [ -d "$G" ]; then
    echo "Cleaning up existing gadget..."
    # Unbind UDC
    echo "" > $G/UDC 2>/dev/null || true
    # Remove symlinks
    rm -f $G/configs/c.1/ecm.usb0 2>/dev/null || true
    rm -f $G/configs/c.1/rndis.usb0 2>/dev/null || true
    rm -f $G/configs/c.1/hid.usb0 2>/dev/null || true
    rm -f $G/configs/c.1/mass_storage.usb0 2>/dev/null || true
    rm -f $G/os_desc/c.1 2>/dev/null || true
    # Remove functions
    rmdir $G/functions/ecm.usb0 2>/dev/null || true
    rmdir $G/functions/rndis.usb0 2>/dev/null || true
    rmdir $G/functions/hid.usb0 2>/dev/null || true
    rmdir $G/functions/mass_storage.usb0 2>/dev/null || true
    # Remove config
    rmdir $G/configs/c.1/strings/0x409 2>/dev/null || true
    rmdir $G/configs/c.1 2>/dev/null || true
    # Remove strings
    rmdir $G/strings/0x409 2>/dev/null || true
    # Remove gadget
    rmdir $G 2>/dev/null || true
fi

echo "Creating USB gadget..."
mkdir -p $G

# ---------- Device identity ----------
echo 0x1d6b > $G/idVendor  # Linux Foundation
echo 0x0104 > $G/idProduct # Multifunction Composite Gadget
echo 0x0100 > $G/bcdDevice # Device version
echo 0x0200 > $G/bcdUSB    # USB 2.0

mkdir -p $G/strings/0x409
echo "IcePi-01" > $G/strings/0x409/serialnumber
echo "T05H1TH" > $G/strings/0x409/manufacturer
echo "IcePi" > $G/strings/0x409/product

# ---------- Configuration ----------
mkdir -p $G/configs/c.1
mkdir -p $G/configs/c.1/strings/0x409
echo "ECM + RNDIS + HID Keyboard" > $G/configs/c.1/strings/0x409/configuration
echo 250 > $G/configs/c.1/MaxPower  # 250mA

# ---------- Microsoft OS descriptors (for RNDIS/Windows) ----------
echo 1 > $G/os_desc/use
echo 0xcd > $G/os_desc/b_vendor_code
echo "MSFT100" > $G/os_desc/qw_sign

# ---------- Ethernet: ECM (Linux/macOS) ----------
if [ -d /sys/module/usb_f_ecm ]; then
    echo "Adding ECM ethernet..."
    mkdir -p $G/functions/ecm.usb0
    echo "48:6f:73:74:50:43" > $G/functions/ecm.usb0/host_addr
    echo "42:61:64:55:53:42" > $G/functions/ecm.usb0/dev_addr
    ln -s $G/functions/ecm.usb0 $G/configs/c.1/
fi

# ---------- Ethernet: RNDIS (Windows) ----------
if [ -d /sys/module/usb_f_rndis ]; then
    echo "Adding RNDIS ethernet..."
    mkdir -p $G/functions/rndis.usb0
    echo "48:6f:73:74:50:43" > $G/functions/rndis.usb0/host_addr
    echo "42:61:64:55:53:42" > $G/functions/rndis.usb0/dev_addr
    ln -s $G/functions/rndis.usb0 $G/configs/c.1/
    ln -s $G/configs/c.1 $G/os_desc
fi

# ---------- USB HID Keyboard ----------
if [ -d /sys/module/usb_f_hid ]; then
    echo "Adding HID keyboard..."
    mkdir -p $G/functions/hid.usb0
    echo 1 > $G/functions/hid.usb0/protocol   # Keyboard
    echo 1 > $G/functions/hid.usb0/subclass   # Boot Interface
    echo 8 > $G/functions/hid.usb0/report_length
    
    # Standard USB HID Keyboard Report Descriptor (Fixed)
    echo -ne \\x05\\x01\\x09\\x06\\xa1\\x01\\x05\\x07\\x19\\xe0\\x29\\xe7\\x15\\x00\\x25\\x01\\x75\\x01\\x95\\x08\\x81\\x02\\x95\\x01\\x75\\x08\\x81\\x03\\x95\\x05\\x75\\x01\\x05\\x08\\x19\\x01\\x29\\x05\\x91\\x02\\x95\\x01\\x75\\x03\\x91\\x03\\x95\\x06\\x75\\x08\\x15\\x00\\x25\\x65\\x05\\x07\\x19\\x00\\x29\\x65\\x81\\x00\\xc0 > $G/functions/hid.usb0/report_desc
    
    ln -s $G/functions/hid.usb0 $G/configs/c.1/
fi

# ---------- Bind gadget to UDC ----------
echo "Binding gadget to UDC..."
UDC=$(ls /sys/class/udc | head -n1)
echo $UDC > $G/UDC

# Wait for device to be created
sleep 1

# Fix permissions on hidg0
if [ -e /dev/hidg0 ]; then
    chmod 666 /dev/hidg0
    echo "✓ HID device ready at /dev/hidg0"
else
    echo "✗ Warning: /dev/hidg0 not created"
fi

echo "USB gadget initialized successfully"