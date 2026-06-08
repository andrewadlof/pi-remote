# IR / Broadlink

Some Android TV boxes only accept **power** over IR (everything else is Bluetooth
LE), and the box cuts USB power in standby — so USB-HID can turn it off but never
back on. A **Broadlink RM4** (Wi-Fi IR blaster) fills that gap: it stays powered
and speaks the box's native IR.

`ir_tool.py` learns and replays IR codes; the server exposes them at
`/ir?cmd=NAME`.

## Install python-broadlink

The HTTP bridge runs under the **system** Python (`/usr/bin/python3`), so
`broadlink` must be importable there. How you install it depends on the Pi's
architecture.

### Raspberry Pi Zero / Zero W (armv6)

There is no `uv` build for armv6 **and** no `cryptography` wheel for armv6, so a
plain `uv`/`pip` install would trigger a doomed source build. Reuse apt's prebuilt
`cryptography` and add broadlink on top with `--no-deps`:

```bash
sudo apt install -y python3-cryptography python3-pip
sudo pip3 install --break-system-packages --no-deps broadlink
python3 -c "import broadlink; print(broadlink.discover)"   # sanity check
```

### 64-bit Pi — Zero 2 W, Pi 3/4/5 (aarch64)

Here `cryptography` ships an aarch64 wheel and `uv` is available, so install it
into the system environment with uv:

```bash
uv pip install --system --break-system-packages broadlink
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
sudo python3 /opt/pi-remote/ir_tool.py learn power <rm4-ip>   # try each IP from `discover`
sudo python3 /opt/pi-remote/ir_tool.py use <rm4-ip>          # the one that printed "Saved"
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
