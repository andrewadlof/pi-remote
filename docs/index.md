# pi-remote

Turn a **Raspberry Pi Zero (W)** into a USB **keyboard + media remote** for an
Android TV box — controllable over a simple **HTTP API**, a built-in
**web remote**, and **Home Assistant**. An optional **Broadlink RM4**
integration adds true IR **power on/off** for boxes whose power button is IR.

## How it works

The Pi's USB-OTG port is switched into **peripheral mode** and presents itself to
the Android box as two USB HID devices:

| Device | Purpose |
| --- | --- |
| `/dev/hidg0` | standard boot **keyboard** (navigation, typing, combos) |
| `/dev/hidg1` | **consumer control** (volume, play/pause, home, search…) |

A tiny stdlib-only HTTP server (`hid_keyboard_server.py`) turns web requests into
HID reports, serves the web remote, and shells out to `ir_tool.py` for IR.

```
Home Assistant / curl ──HTTP──▶ Pi Zero ──USB HID──▶ Android box
                                  │
                                  └──Wi-Fi──▶ Broadlink RM4 ──IR──▶ Android box (power)
```

## Why both USB and IR?

Most Android TV remotes send navigation over **Bluetooth LE** and only the
**power** button over **IR** (so the box can cold-start). The Pi covers everything
BLE/HID can do; the Broadlink RM4 covers the one thing only IR can: turning the
box back on from standby (the box cuts USB power when off, so HID can't wake it).

## Quick links

- **[Installation](installation.md)** — one-command Ansible provisioning, or manual steps
- **[Configuration](configuration.md)** — port, API key, paths
- **[HTTP API](api.md)** — every endpoint with examples
- **[IR / Broadlink](ir.md)** — learn and send IR codes
- **[Home Assistant](home-assistant.md)** — control with REST + embed the remote
- **[Troubleshooting](troubleshooting.md)** — the gotchas, solved

## Feature summary

- D-pad / OK / Back navigation, text entry, key combos (Ctrl+A, Alt+Tab)
- Media transport + volume via HID consumer control
- IR power (and any other IR button) via a Broadlink RM4
- Mobile-friendly web remote (Add-to-Home-Screen capable)
- Optional shared-secret auth, CORS enabled
- Boot-persistent via systemd; reproducible via Ansible
- No third-party Python deps for the core server (stdlib only)
