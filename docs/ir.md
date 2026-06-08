# IR / Broadlink

Some Android TV boxes only accept **power** over IR (everything else is Bluetooth
LE), and the box cuts USB power in standby — so USB-HID can turn it off but never
back on. A **Broadlink RM4** (Wi-Fi IR blaster) fills that gap: it stays powered
and speaks the box's native IR.

`ir_tool.py` learns and replays IR codes; the server exposes them at
`/ir?cmd=NAME`.

## Install python-broadlink (armv6-safe)

The Pi Zero is **armv6**, which has no prebuilt `cryptography` wheel — installing
from PyPI would trigger a doomed source build. Use the apt build instead:

```bash
sudo apt install -y python3-cryptography python3-pip
sudo pip3 install --break-system-packages --no-deps broadlink
python3 -c "import broadlink; print(broadlink.discover)"   # sanity check
```

!!! note
    `broadlink.__version__` does not exist — test with `broadlink.discover`.

## Learn a code

You need the box's **original IR remote**. Point it at the RM4 when prompted.

```bash
# 1. See what's on the LAN
sudo python3 /opt/pi-remote/ir_tool.py discover

# 2. Learn the power button (aim original remote at the RM4 within 10s)
sudo python3 /opt/pi-remote/ir_tool.py learn power

# 3. Confirm + test
sudo python3 /opt/pi-remote/ir_tool.py list
sudo python3 /opt/pi-remote/ir_tool.py send power     # box toggles
```

## Multiple Broadlink devices

If `discover` lists several, pick the one aimed at the box. Since power is IR,
**only the RM4 in the box's room captures the remote** — try learning via each
until one prints "Saved", then lock it in:

```bash
sudo python3 /opt/pi-remote/ir_tool.py learn power 192.168.1.134   # try each IP
sudo python3 /opt/pi-remote/ir_tool.py use 192.168.1.134           # the one that saved
```

`use` writes the chosen device to `PI_REMOTE_IR_DEVFILE` so future sends are fast
(no rediscovery).

## Wire it to a button

The web remote's Power button already calls `/ir?cmd=power`. To add more IR
buttons (e.g. a soundbar, a source/input key):

```bash
sudo python3 /opt/pi-remote/ir_tool.py learn input
```

Then add to `remote.html`:

```html
<button class="sec" onclick="ir('input')">Input</button>
```

## Notes

- The Pi and the Broadlink must be on the **same subnet/VLAN** — discovery is UDP
  broadcast.
- Give the RM4 a **DHCP reservation**; if its IP changes, delete
  `/var/lib/pi-remote/ir_device.json` to force rediscovery.
- The RM4 is IR-only — it cannot replay the box's **Bluetooth** buttons.
