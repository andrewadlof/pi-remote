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
