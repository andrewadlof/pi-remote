#!/bin/bash
# pi-remote USB HID gadget setup (configfs).
# Creates two HID functions on the Pi's USB-OTG port:
#   hid.usb0 -> /dev/hidg0  standard boot keyboard (8-byte reports)
#   hid.usb1 -> /dev/hidg1  consumer control       (2-byte LE usage codes)
#
# Run once at boot by usb-gadget.service. Requires:
#   - dtoverlay=dwc2,dr_mode=peripheral in config.txt (under [all])
#   - modules-load=dwc2 in cmdline.txt
# Based on the isticktoit.net composite-gadget recipe.

modprobe libcomposite

cd /sys/kernel/config/usb_gadget/
mkdir -p pi-remote
cd pi-remote

echo 0x1d6b > idVendor    # Linux Foundation
echo 0x0104 > idProduct   # Multifunction Composite Gadget
echo 0x0100 > bcdDevice   # v1.0.0
echo 0x0200 > bcdUSB      # USB 2.0

mkdir -p strings/0x409
echo "0123456789"     > strings/0x409/serialnumber
echo "pi-remote"      > strings/0x409/manufacturer
echo "pi-remote HID"  > strings/0x409/product

mkdir -p configs/c.1/strings/0x409
echo "Config 1: keyboard+consumer" > configs/c.1/strings/0x409/configuration
echo 250 > configs/c.1/MaxPower

# --- Function 1: standard keyboard -> /dev/hidg0 ---
mkdir -p functions/hid.usb0
echo 1 > functions/hid.usb0/protocol
echo 1 > functions/hid.usb0/subclass
echo 8 > functions/hid.usb0/report_length
echo -ne \\x05\\x01\\x09\\x06\\xa1\\x01\\x05\\x07\\x19\\xe0\\x29\\xe7\\x15\\x00\\x25\\x01\\x75\\x01\\x95\\x08\\x81\\x02\\x95\\x01\\x75\\x08\\x81\\x03\\x95\\x05\\x75\\x01\\x05\\x08\\x19\\x01\\x29\\x05\\x91\\x02\\x95\\x01\\x75\\x03\\x91\\x03\\x95\\x06\\x75\\x08\\x15\\x00\\x25\\x65\\x05\\x07\\x19\\x00\\x29\\x65\\x81\\x00\\xc0 > functions/hid.usb0/report_desc
ln -s functions/hid.usb0 configs/c.1/

# --- Function 2: consumer control (media/home/volume) -> /dev/hidg1 ---
mkdir -p functions/hid.usb1
echo 0 > functions/hid.usb1/protocol
echo 0 > functions/hid.usb1/subclass
echo 2 > functions/hid.usb1/report_length
echo -ne \\x05\\x0c\\x09\\x01\\xa1\\x01\\x15\\x00\\x26\\xff\\x03\\x19\\x00\\x2a\\xff\\x03\\x75\\x10\\x95\\x01\\x81\\x00\\xc0 > functions/hid.usb1/report_desc
ln -s functions/hid.usb1 configs/c.1/

# --- bind to the USB Device Controller (activate the gadget) ---
ls /sys/class/udc > UDC
