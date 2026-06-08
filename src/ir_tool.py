#!/usr/bin/env python3
"""pi-remote Broadlink RM4 IR helper (multi-device aware).

Requires the `broadlink` package (see docs/ir.md for armv6-safe install).

Usage:
  ir_tool.py discover              # list every Broadlink device on the LAN
  ir_tool.py use   <host>          # pick which device is the active blaster
  ir_tool.py learn <name> [host]   # learn an IR code from your original remote
  ir_tool.py send  <name> [host]   # send a learned IR code
  ir_tool.py list                  # list saved codes

Paths are configurable via environment (defaults shown):
  PI_REMOTE_IR_STORE   = /var/lib/pi-remote/ir_codes.json
  PI_REMOTE_IR_DEVFILE = /var/lib/pi-remote/ir_device.json
"""
import sys, os, json, time, base64
import broadlink

STORE   = os.environ.get("PI_REMOTE_IR_STORE",   "/var/lib/pi-remote/ir_codes.json")
DEVFILE = os.environ.get("PI_REMOTE_IR_DEVFILE", "/var/lib/pi-remote/ir_device.json")

def _load(p, d):
    try:
        with open(p) as f: return json.load(f)
    except Exception: return d
def _save(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f: json.dump(o, f, indent=2)

def _store_dev(dev):
    _save(DEVFILE, {"host": dev.host[0], "mac": dev.mac.hex(), "devtype": dev.devtype})

def get_device(host=None, save=True):
    if host:
        match = None
        for d in broadlink.discover(timeout=5):
            if d.host[0] == host: match = d; break
        if not match: sys.exit("No Broadlink device found at %s" % host)
        match.auth()
        if save: _store_dev(match)
        return match
    info = _load(DEVFILE, None)
    if info:
        try:
            dev = broadlink.gendevice(info["devtype"], (info["host"], 80), bytes.fromhex(info["mac"]))
            dev.auth(); return dev
        except Exception: pass
    devs = broadlink.discover(timeout=5)
    if not devs: sys.exit("No Broadlink device found.")
    if len(devs) > 1:
        lines = "\n".join("  - %s (%s)" % (d.host[0], d.mac.hex()) for d in devs)
        sys.exit("Multiple Broadlink devices found - pick one with 'ir_tool.py use <host>':\n" + lines)
    devs[0].auth(); _store_dev(devs[0]); return devs[0]

def cmd_discover():
    devs = broadlink.discover(timeout=5)
    if not devs: sys.exit("No Broadlink device found.")
    for d in devs:
        d.auth()
        print("Found %s  host=%s  mac=%s  devtype=0x%04x" % (d.type, d.host[0], d.mac.hex(), d.devtype))

def cmd_use(host):
    dev = get_device(host, save=True)
    print("Active IR blaster set to %s (%s)." % (dev.host[0], dev.mac.hex()))

def cmd_learn(name, host=None):
    dev = get_device(host, save=False); dev.enter_learning()
    print(">> Aim your ORIGINAL remote at Broadlink %s and press the '%s' button now (10s)..."
          % (dev.host[0], name))
    packet = None
    for _ in range(10):
        time.sleep(1)
        try: packet = dev.check_data()
        except Exception: packet = None
        if packet: break
    if not packet: sys.exit("Timed out - no IR captured. Right device? Aim closer.")
    codes = _load(STORE, {}); codes[name] = base64.b64encode(packet).decode(); _save(STORE, codes)
    print("Saved '%s' (%d bytes)." % (name, len(packet)))

def cmd_send(name, host=None):
    codes = _load(STORE, {})
    if name not in codes: sys.exit("No saved code named '%s'." % name)
    get_device(host, save=False).send_data(base64.b64decode(codes[name]))
    print("Sent '%s'%s." % (name, (" via %s" % host) if host else ""))

if __name__ == "__main__":
    a = sys.argv
    if   len(a) == 2 and a[1] == "discover": cmd_discover()
    elif len(a) == 2 and a[1] == "list":     print("\n".join(sorted(_load(STORE, {}).keys())) or "(none)")
    elif len(a) == 3 and a[1] == "use":      cmd_use(a[2])
    elif a[1:2] == ["learn"] and len(a) in (3, 4): cmd_learn(a[2], a[3] if len(a) == 4 else None)
    elif a[1:2] == ["send"]  and len(a) in (3, 4): cmd_send(a[2], a[3] if len(a) == 4 else None)
    else: sys.exit(__doc__)
