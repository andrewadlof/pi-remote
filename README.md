# pi-remote

Turn a **Raspberry Pi Zero (W)** into a USB **keyboard + media remote** for an
Android TV box — driven by a small **HTTP API**, a built-in **web remote**, and
your **Homey** hub. An optional **Broadlink RM4** integration adds true IR
**power on/off** for boxes whose power button is IR-only.

```
Homey / phone / curl ──HTTP──▶ Pi Zero ──USB HID──▶ Android box
                                  │
                                  └──Wi-Fi──▶ Broadlink RM4 ──IR──▶ Android box (power)
```

The Pi enumerates as two USB HID devices — `/dev/hidg0` (keyboard) and
`/dev/hidg1` (consumer control) — and a stdlib-only Python server turns web
requests into HID reports, serves the remote UI, and shells out to a Broadlink
helper for IR.

## Features

- D-pad / OK / Back navigation, free-text entry, key combos (Ctrl+A, Alt+Tab)
- Media transport + volume via HID consumer control
- IR **power** (and any other IR button) via a Broadlink RM4
- Mobile-friendly **web remote** (Add-to-Home-Screen capable)
- Optional shared-secret auth; CORS enabled
- Boot-persistent via **systemd**; reproducible via **Ansible**
- No third-party Python deps for the core server

## Hardware requirements

### Required

| Item | Notes |
| --- | --- |
| **Raspberry Pi with USB-OTG** | Pi Zero, **Zero W** (used here), Zero 2 W, or any Pi whose USB port supports peripheral/gadget mode. The Zero W is armv6 — see the [IR install notes](docs/ir.md). |
| **microSD card** | 8 GB+, with Raspberry Pi OS (Bookworm or Trixie). |
| **USB data cable** | Micro-USB that carries **data**, not charge-only. Plug it into the Pi's inner **`USB`** (OTG) port — **not** the `PWR` port. |
| **Android TV box (the target)** | With a spare USB port. It powers the Pi over that data port, so no separate Pi power supply is usually needed. |
| **Wi-Fi network** | For the HTTP API / web remote / Homey (and to reach a Broadlink). The Zero W has built-in Wi-Fi. |

### Optional

| Item | Enables |
| --- | --- |
| **Broadlink RM4 Mini** (or similar Wi-Fi IR blaster) | True IR **power on/off** for boxes whose power button is IR-only (USB power is cut in standby, so HID can't wake them). |
| **The box's original IR remote** | One-time IR **learning** of the power (or any) code into the RM4. |
| **Homey hub** | Automating buttons via Flows. Any HTTP-capable controller works too. |

> [!NOTE]
> **Why the inner USB port matters:** on the Pi Zero family the inner port
> labelled **`USB`** is the OTG/data port that can act as a USB device; the
> `PWR` port is power-only. The gadget only enumerates against a real USB host
> (the box), not a dumb charger.

## Repository layout

```
src/                     runtime files deployed to the Pi
  hid_keyboard_server.py   HTTP -> USB HID + /ir bridge (stdlib only)
  ir_tool.py               Broadlink RM4 learn/send helper
  remote.html              self-contained web remote UI
  usb_gadget.sh            configfs USB HID gadget setup
config/
  config.example.env       configuration template (-> /etc/pi-remote/config.env)
ansible/                   one-command provisioning of a Pi from scratch
  site.yml, group_vars/, roles/{common,usb_gadget,hid_server,broadlink_ir}
docs/                      MkDocs documentation site
```

## Quick start (Ansible)

```bash
git clone https://github.com/andrewadlof/pi-remote.git
cd pi-remote/ansible
cp inventory.example.ini inventory.ini      # set host/user
$EDITOR group_vars/all.yml                   # set pi_remote_api_key
ansible-playbook site.yml                     # provisions + reboots the Pi
```

Then open `http://<pi-host>:8800/` (add `?token=YOURKEY` if you set an API key)
and learn your IR power code:

```bash
sudo python3 /opt/pi-remote/ir_tool.py discover
sudo python3 /opt/pi-remote/ir_tool.py learn power
sudo python3 /opt/pi-remote/ir_tool.py send power
```

Manual installation, the full API, and every gotcha are documented in **[docs/](docs/index.md)**.

## API at a glance

| Endpoint | Example |
| --- | --- |
| `GET /` | web remote UI |
| `/type` | `curl -X POST .../type -d '{"text":"hello"}'` |
| `/key` | `.../key?key=DOWN` |
| `/press` | `.../press?key=a&mod=CTRL` |
| `/media` | `.../media?key=VOLUP` |
| `/ir` | `.../ir?cmd=power` |

## Button map (as shipped)

| Button | Transport | Action |
| --- | --- | --- |
| D-pad / OK / Back / Home | USB HID | navigation |
| Media / Volume | USB HID | consumer control |
| 🔍 Search | USB HID | AC Search |
| ⏻ Power | Broadlink IR | on **and** off |
| 🌙 Screen off | USB HID | standby |
| Text + Send | USB HID | type strings |

## Documentation

Browse `docs/`, or build the site locally with [uv](https://docs.astral.sh/uv/):

```bash
uv run --extra docs mkdocs serve
```

## Credits & license

USB composite-gadget approach based on the
[isticktoit.net](https://www.isticktoit.net/?p=1383) recipe. IR via
[python-broadlink](https://github.com/mjg59/python-broadlink).
Licensed under the [MIT License](LICENSE).
