#!/bin/bash
set -e

CFG=/sys/kernel/config
G=$CFG/usb_gadget/g1
DB_PATH="/var/local/IcePi/icepi.db"

# Read state from SQLite DB (defaults to all enabled)
ENABLE_ETHERNET=$(sqlite3 "$DB_PATH" "SELECT enabled FROM interfaces WHERE name='ethernet';" 2>/dev/null || echo "1")
ENABLE_STORAGE=$(sqlite3 "$DB_PATH" "SELECT enabled FROM interfaces WHERE name='storage';" 2>/dev/null || echo "0")
ENABLE_HID=$(sqlite3 "$DB_PATH" "SELECT enabled FROM interfaces WHERE name='hid';" 2>/dev/null || echo "1")

[ "$ENABLE_ETHERNET" != "0" ] && ENABLE_ETHERNET=true || ENABLE_ETHERNET=false
[ "$ENABLE_STORAGE" != "0" ] && ENABLE_STORAGE=true || ENABLE_STORAGE=false
[ "$ENABLE_HID" != "0" ] && ENABLE_HID=true || ENABLE_HID=false

echo "Configuration: Ethernet=$ENABLE_ETHERNET, Storage=$ENABLE_STORAGE, HID=$ENABLE_HID"

# Mount configfs if not mounted
mountpoint -q $CFG || mount -t configfs none $CFG

# Clean up existing gadget
if [ -d "$G" ]; then
    echo "Cleaning up existing gadget..."
    echo "" > $G/UDC 2>/dev/null || true
    rm -f $G/configs/c.1/ecm.usb0 2>/dev/null || true
    rm -f $G/configs/c.1/rndis.usb0 2>/dev/null || true
    rm -f $G/configs/c.1/hid.usb0 2>/dev/null || true
    rm -f $G/configs/c.1/mass_storage.usb0 2>/dev/null || true
    rm -f $G/os_desc/c.1 2>/dev/null || true
    rmdir $G/functions/ecm.usb0 2>/dev/null || true
    rmdir $G/functions/rndis.usb0 2>/dev/null || true
    rmdir $G/functions/hid.usb0 2>/dev/null || true
    rmdir $G/functions/mass_storage.usb0 2>/dev/null || true
    rmdir $G/configs/c.1/strings/0x409 2>/dev/null || true
    rmdir $G/configs/c.1 2>/dev/null || true
    rmdir $G/strings/0x409 2>/dev/null || true
    rmdir $G 2>/dev/null || true
fi

echo "Creating USB gadget..."
mkdir -p $G

# ---------- Device identity ----------
echo 0x1d6b > $G/idVendor
echo 0x0104 > $G/idProduct
echo 0x0100 > $G/bcdDevice
echo 0x0200 > $G/bcdUSB

mkdir -p $G/strings/0x409
echo "IcePi-01" > $G/strings/0x409/serialnumber
echo "T05H1TH" > $G/strings/0x409/manufacturer
echo "IcePi" > $G/strings/0x409/product

# ---------- Configuration ----------
mkdir -p $G/configs/c.1
mkdir -p $G/configs/c.1/strings/0x409
echo "IcePi USB Gadget" > $G/configs/c.1/strings/0x409/configuration
echo 250 > $G/configs/c.1/MaxPower

# ---------- Microsoft OS descriptors ----------
echo 1 > $G/os_desc/use
echo 0xcd > $G/os_desc/b_vendor_code
echo "MSFT100" > $G/os_desc/qw_sign

# ---------- Ethernet: ECM (Linux/macOS) ----------
if [ "$ENABLE_ETHERNET" = "true" ] && [ -d /sys/module/usb_f_ecm ]; then
    echo "Adding ECM ethernet..."
    mkdir -p $G/functions/ecm.usb0
    echo "48:6f:73:74:50:43" > $G/functions/ecm.usb0/host_addr
    echo "42:61:64:55:53:42" > $G/functions/ecm.usb0/dev_addr
    ln -s $G/functions/ecm.usb0 $G/configs/c.1/
fi

# ---------- Ethernet: RNDIS (Windows) ----------
if [ "$ENABLE_ETHERNET" = "true" ] && [ -d /sys/module/usb_f_rndis ]; then
    echo "Adding RNDIS ethernet..."
    mkdir -p $G/functions/rndis.usb0
    echo "48:6f:73:74:50:43" > $G/functions/rndis.usb0/host_addr
    echo "42:61:64:55:53:42" > $G/functions/rndis.usb0/dev_addr
    ln -s $G/functions/rndis.usb0 $G/configs/c.1/
    ln -s $G/configs/c.1 $G/os_desc
fi

# ---------- USB Mass Storage ----------
if [ "$ENABLE_STORAGE" = "true" ] && [ -d /sys/module/usb_f_mass_storage ]; then
    echo "Adding mass storage..."
    mkdir -p $G/functions/mass_storage.usb0
    echo 1 > $G/functions/mass_storage.usb0/stall
    echo 0 > $G/functions/mass_storage.usb0/lun.0/ro
    # Configure storage file if needed
    # echo /path/to/image.img > $G/functions/mass_storage.usb0/lun.0/file
    ln -s $G/functions/mass_storage.usb0 $G/configs/c.1/
fi

# ---------- USB HID Keyboard ----------
if [ "$ENABLE_HID" = "true" ] && [ -d /sys/module/usb_f_hid ]; then
    echo "Adding HID keyboard..."
    mkdir -p $G/functions/hid.usb0
    echo 1 > $G/functions/hid.usb0/protocol
    echo 1 > $G/functions/hid.usb0/subclass
    echo 8 > $G/functions/hid.usb0/report_length
    echo -ne \\x05\\x01\\x09\\x06\\xa1\\x01\\x05\\x07\\x19\\xe0\\x29\\xe7\\x15\\x00\\x25\\x01\\x75\\x01\\x95\\x08\\x81\\x02\\x95\\x01\\x75\\x08\\x81\\x03\\x95\\x05\\x75\\x01\\x05\\x08\\x19\\x01\\x29\\x05\\x91\\x02\\x95\\x01\\x75\\x03\\x91\\x03\\x95\\x06\\x75\\x08\\x15\\x00\\x25\\x65\\x05\\x07\\x19\\x00\\x29\\x65\\x81\\x00\\xc0 > $G/functions/hid.usb0/report_desc
    ln -s $G/functions/hid.usb0 $G/configs/c.1/
fi

# ---------- Bind gadget ----------
echo "Binding gadget to UDC..."
UDC=$(ls /sys/class/udc | head -n1)
echo $UDC > $G/UDC

sleep 1

# Fix permissions
if [ -e /dev/hidg0 ]; then
    chmod 666 /dev/hidg0
    echo "✓ HID device ready"
fi

echo "USB gadget initialized successfully"
