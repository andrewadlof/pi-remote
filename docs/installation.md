# Installation

There are two paths: **Ansible** (recommended, reproducible) or **manual**.

## Prerequisites

- A Raspberry Pi Zero / Zero W (or any Pi with a USB-OTG port) running
  Raspberry Pi OS (Bookworm or Trixie).
- The Pi connected to the Android box's **data USB port** with a cable in the
  Pi's inner **`USB`** port (not `PWR`).
- SSH access to the Pi.

## Option A — Ansible (recommended)

From a control machine (your laptop) with Ansible installed:

```bash
git clone https://github.com/andrewadlof/pi-remote.git
cd pi-remote/ansible

cp inventory.example.ini inventory.ini
$EDITOR inventory.ini          # set ansible_host / ansible_user

# set at least pi_remote_api_key (and review paths) in group_vars/all.yml
$EDITOR group_vars/all.yml

ansible-playbook site.yml
```

What the playbook does:

1. **usb_gadget** — enables `dtoverlay=dwc2,dr_mode=peripheral` under `[all]`,
   adds `modules-load=dwc2`, installs the gadget script + `usb-gadget.service`.
2. **hid_server** — deploys the app to `/opt/pi-remote`, writes
   `/etc/pi-remote/config.env`, installs and starts `hid-keyboard-server.service`.
3. **broadlink_ir** — installs `python-broadlink` (armv6-safe) for IR.

!!! note "First-run reboot"
    Changing the USB-gadget boot settings requires a reboot. The playbook
    reboots automatically (set `allow_reboot: false` to do it yourself). After
    the reboot, `/dev/hidg0` and `/dev/hidg1` appear and the service serves the
    remote at `http://<pi>:8800/`.

Verify:

```bash
ssh pi@<host> 'ls -l /dev/hidg0 /dev/hidg1; systemctl is-active hid-keyboard-server'
```

## Option B — Manual

See **[USB Gadget](usb-gadget.md)** for the full configfs/boot walkthrough, then:

```bash
sudo mkdir -p /opt/pi-remote /etc/pi-remote /var/lib/pi-remote
sudo cp src/hid_keyboard_server.py src/ir_tool.py /opt/pi-remote/
sudo cp src/remote.html /opt/pi-remote/
sudo cp src/usb_gadget.sh /usr/local/sbin/pi-remote-usb-gadget
sudo chmod +x /opt/pi-remote/*.py /usr/local/sbin/pi-remote-usb-gadget
sudo cp config/config.example.env /etc/pi-remote/config.env
$EDITOR /etc/pi-remote/config.env        # set PI_REMOTE_API_KEY
```

Create the two systemd units (`usb-gadget.service`, `hid-keyboard-server.service`)
— the exact contents are in the Ansible templates under
`ansible/roles/*/templates/`. Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now usb-gadget.service hid-keyboard-server.service
```

For IR, install broadlink. On the **armv6** Pi Zero / Zero W use apt's
`cryptography` (no armv6 wheel for `uv`/`pip`); on a **64-bit** Pi you can use
`uv pip install --system broadlink`. Full details in **[IR / Broadlink](ir.md)**:

```bash
# Pi Zero / Zero W (armv6)
sudo apt install -y python3-cryptography python3-pip
sudo pip3 install --break-system-packages --no-deps broadlink
```

## After install

- Open `http://<pi-host>:8800/` (append `?token=YOURKEY` if you set an API key).
- Learn your IR power code — see **[IR / Broadlink](ir.md)**.
- Wire it to Homey — see **[Homey integration](homey.md)**.
- Give the Pi (and any Broadlink) a DHCP reservation so addresses stay put.
