# USB Gadget

This is the layer that makes the Pi *be* a keyboard. The Ansible `usb_gadget`
role automates everything here; this page explains what it does and how to do it
by hand.

## 1. Peripheral mode

The Pi's USB-OTG controller defaults to a host-only driver (`dwc_otg`). To act as
a USB device it must load the `dwc2` driver in **peripheral** mode.

In `/boot/firmware/config.txt` (older OS: `/boot/config.txt`), under `[all]`:

```ini
[all]
dtoverlay=dwc2,dr_mode=peripheral
```

!!! warning "Watch the section filters"
    If this line lands under a section like `[cm4]` or `[cm5]`, it is **silently
    skipped** on a Pi Zero and you'll get an empty `/sys/class/udc/`. It must be
    under `[all]` (or unsectioned).

In `/boot/firmware/cmdline.txt` (single line), add after `rootwait`:

```
modules-load=dwc2
```

Reboot, then confirm:

```bash
cat /proc/device-tree/soc/usb@*/dr_mode   # -> peripheral
ls /sys/class/udc/                        # -> 20980000.usb (non-empty!)
```

## 2. The gadget script

[`src/usb_gadget.sh`](https://github.com/andrewadlof/pi-remote/blob/main/src/usb_gadget.sh)
builds a composite gadget via configfs with two HID functions and binds it to the
UDC. Installed to `/usr/local/sbin/pi-remote-usb-gadget` and run once at boot by
`usb-gadget.service`.

It creates:

- **`hid.usb0` → `/dev/hidg0`** — boot keyboard, 8-byte reports
  `[modifier][reserved][key1..key6]`.
- **`hid.usb1` → `/dev/hidg1`** — consumer control, 2-byte little-endian usage
  codes (HID usage page `0x0C`).

The script begins with `modprobe libcomposite` (which creates
`/sys/kernel/config/usb_gadget`) and ends with `ls /sys/class/udc > UDC` to
activate the gadget.

## 3. Autostart

Debian/Raspberry Pi OS **does not run `/etc/rc.local`** by default anymore, so a
systemd unit owns startup:

```ini
[Unit]
Description=pi-remote USB HID gadget
After=sys-kernel-config.mount
Requires=sys-kernel-config.mount

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/pi-remote-usb-gadget

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now usb-gadget.service
ls -l /dev/hidg0 /dev/hidg1
```

## HID report reference

**Keyboard** (`/dev/hidg0`) — 8 bytes. To press `a` then release:

```python
open('/dev/hidg0','rb+').write(bytes([0,0,0x04,0,0,0,0,0]))  # 0x04 = 'a'
open('/dev/hidg0','rb+').write(bytes(8))                      # release
```

Always send the release report or the host sees a stuck key.

**Consumer** (`/dev/hidg1`) — 2 bytes, little-endian usage code, then `0x0000` to
release. Example play/pause (`0x00CD`): `bytes([0xCD,0x00])`.
