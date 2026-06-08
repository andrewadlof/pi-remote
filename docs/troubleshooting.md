# Troubleshooting

A field guide to the gotchas, most of which the docs/Ansible already prevent.

## `/dev/hidg0` doesn't exist

Work through the chain:

```bash
lsmod | grep -E 'dwc2|libcomposite'        # both should be listed
cat /proc/device-tree/soc/usb@*/dr_mode    # -> peripheral
ls /sys/class/udc/                         # must be NON-empty
ls -l /dev/hidg0 /dev/hidg1
systemctl status usb-gadget
```

- **`udc` empty / `dr_mode` not "peripheral"** → the `dtoverlay=dwc2` line isn't
  taking effect. Most common cause: it's under a `[cm4]`/`[cm5]` section instead
  of `[all]`. See [USB Gadget](usb-gadget.md).
- **`dwc_otg` in `dmesg` instead of `dwc2`** → same root cause; the overlay never
  swapped the driver.
- **modules not loaded** → missing `modules-load=dwc2` in `cmdline.txt` (it must
  stay on the single existing line).

## Nothing types into the host

- Confirm the cable is in the Pi's inner **`USB`** port (not `PWR`) and the box is
  on.
- Check the service: `journalctl -u hid-keyboard-server -e`.
- Hit the API directly: `curl http://localhost:8800/key?key=ENTER`.

## Android-specific key behaviour

| Want | Use | Notes |
| --- | --- | --- |
| Back | `/media?key=MEDIABACK` | keyboard `ESC` often ignored |
| Home | `/media?key=HOME` | consumer AC Home |
| Menu/Settings | — | `KEYCODE_MENU` ignored by most apps; use Search or IR |
| Search | `/media?key=SEARCH` | AC Search |

## Power turns off but won't turn on

Expected: the box cuts USB power in standby, so HID can't wake it. Use the
**Broadlink IR** power code instead (`/ir?cmd=power`). See [IR / Broadlink](ir.md).

## Broadlink not found / multiple found

- `No Broadlink device found` → Pi and RM4 on different subnets/VLANs (discovery
  is UDP broadcast), or the RM4 isn't set up in the Broadlink app yet.
- `Multiple devices found` → choose with `ir_tool.py use <host>`; identify the
  right one via the learn-until-"Saved" trick (only the in-room RM4 hears the
  original remote).

## broadlink install errors

- `AttributeError: module 'broadlink' has no attribute '__version__'` → harmless;
  the import worked. Test with `broadlink.discover`.
- pip trying to **build cryptography** → you skipped the apt step. Install
  `python3-cryptography` from apt and use `pip install --no-deps broadlink`.

## Service won't start after reboot

```bash
systemctl status usb-gadget hid-keyboard-server
journalctl -u hid-keyboard-server -e
```

`hid-keyboard-server` waits up to 30s for `/dev/hidg0`; if the gadget service
failed, fix that first (it's the dependency).
