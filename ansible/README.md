# pi-remote — Ansible provisioning

Provisions a Raspberry Pi Zero (W) from a fresh Raspberry Pi OS install into a
working USB-HID + IR remote bridge.

## Usage

```bash
cp inventory.example.ini inventory.ini
$EDITOR inventory.ini            # ansible_host / ansible_user
$EDITOR group_vars/all.yml       # set pi_remote_api_key, review paths
ansible-playbook site.yml
```

The control machine needs Ansible; the Pi needs SSH + a sudo-capable user.

## Roles

| Role | Does |
| --- | --- |
| `common` | apt cache + base packages |
| `usb_gadget` | `dwc2` peripheral overlay, `modules-load`, gadget script, `usb-gadget.service` |
| `hid_server` | deploys app to `/opt/pi-remote`, writes `/etc/pi-remote/config.env`, installs/starts `hid-keyboard-server.service` |
| `broadlink_ir` | installs `python-broadlink` (armv6-safe) — runs when `install_broadlink: true` |

## Key variables (`group_vars/all.yml`)

| Variable | Default | Notes |
| --- | --- | --- |
| `pi_remote_api_key` | `""` | **set this** to a long random string |
| `pi_remote_port` | `8800` | HTTP port |
| `boot_config` / `boot_cmdline` | `/boot/firmware/...` | use `/boot/...` on older OS |
| `install_broadlink` | `true` | install IR support |
| `allow_reboot` | `true` | auto-reboot when boot settings change |

## Notes

- Changing the USB-gadget boot settings requires a **reboot**, handled
  automatically (set `allow_reboot: false` to do it yourself).
- File deploys copy from the repo's `../src` and `../config` so those stay the
  single source of truth.
- IR code **learning is interactive** (you press the original remote at the RM4)
  and is therefore a manual post-install step — see `../docs/ir.md`.
- `inventory.ini` is gitignored; only `inventory.example.ini` is committed.
