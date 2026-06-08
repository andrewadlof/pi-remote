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
    """Load JSON from a file, returning a default on any error.

    Parameters
    ----------
    p : str
        Path to the JSON file.
    d : object
        Value to return if the file is missing or unreadable.

    Returns
    -------
    object
        The parsed JSON, or `d` on failure.
    """
    try:
        with open(p) as f: return json.load(f)
    except Exception: return d
def _save(p, o):
    """Write an object to a file as pretty-printed JSON, creating parent dirs.

    Parameters
    ----------
    p : str
        Destination path.
    o : object
        JSON-serializable value to write.

    Returns
    -------
    None
    """
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f: json.dump(o, f, indent=2)

def _store_dev(dev):
    """Persist a device's host/MAC/type to ``DEVFILE`` for fast reconnection.

    Parameters
    ----------
    dev : broadlink.Device
        An authenticated Broadlink device.

    Returns
    -------
    None
    """
    _save(DEVFILE, {"host": dev.host[0], "mac": dev.mac.hex(), "devtype": dev.devtype})

def get_device(host=None, save=True):
    """Resolve and authenticate the Broadlink device to use.

    Resolution order: the explicit `host` (matched against discovery), then the
    cached device in ``DEVFILE``, then LAN discovery. With multiple devices and no
    `host`/cache, the user is asked to pick one and the process exits.

    Parameters
    ----------
    host : str, optional
        IP/host of a specific device to use. If omitted, use the cached device or
        auto-discover.
    save : bool, optional
        Whether to persist the resolved device to ``DEVFILE`` (default ``True``).

    Returns
    -------
    broadlink.Device
        An authenticated device.

    Raises
    ------
    SystemExit
        If no device is found, the requested `host` is not present, or multiple
        devices exist and none was selected.
    """
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
    """List every Broadlink device on the LAN (host, MAC, device type).

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        If no Broadlink device is found.
    """
    devs = broadlink.discover(timeout=5)
    if not devs: sys.exit("No Broadlink device found.")
    for d in devs:
        d.auth()
        print("Found %s  host=%s  mac=%s  devtype=0x%04x" % (d.type, d.host[0], d.mac.hex(), d.devtype))

def cmd_use(host):
    """Select and cache the active IR blaster by host.

    Parameters
    ----------
    host : str
        IP/host of the device to make the default (saved to ``DEVFILE``).

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        If no device is found at `host`.
    """
    dev = get_device(host, save=True)
    print("Active IR blaster set to %s (%s)." % (dev.host[0], dev.mac.hex()))

def cmd_learn(name, host=None):
    """Learn an IR code from the original remote and save it under `name`.

    Puts the device into learning mode and polls for up to ~10 seconds while you
    press the button on the source remote.

    Parameters
    ----------
    name : str
        Key to store the captured code under (e.g. ``"power"``).
    host : str, optional
        Specific device to learn on; otherwise the cached/auto-resolved device.

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        If no device is available or no IR signal is captured before timeout.
    """
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
    """Send a previously learned IR code.

    Parameters
    ----------
    name : str
        Name of the saved code to transmit.
    host : str, optional
        Specific device to send from; otherwise the cached/auto-resolved device.

    Returns
    -------
    None

    Raises
    ------
    SystemExit
        If no code named `name` exists, or no device is available.
    """
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
