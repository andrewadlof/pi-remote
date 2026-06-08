# Configuration

The server reads its settings from environment variables, supplied on the Pi by
`/etc/pi-remote/config.env` (loaded by the systemd unit). A template lives at
[`config/config.example.env`](https://github.com/andrewadlof/pi-remote/blob/main/config/config.example.env).

| Variable | Default | Description |
| --- | --- | --- |
| `PI_REMOTE_PORT` | `8800` | TCP port the HTTP bridge listens on |
| `PI_REMOTE_API_KEY` | *(empty)* | Shared secret. If set, requests need `?token=` or `X-API-Key` |
| `PI_REMOTE_KEY_DELAY` | `0.008` | Seconds between keystrokes when typing |
| `PI_REMOTE_HTML` | `/opt/pi-remote/remote.html` | Path to the web remote page |
| `PI_REMOTE_IR_TOOL` | `/opt/pi-remote/ir_tool.py` | Path to the IR helper |
| `PI_REMOTE_IR_STORE` | `/var/lib/pi-remote/ir_codes.json` | Learned IR codes |
| `PI_REMOTE_IR_DEVFILE` | `/var/lib/pi-remote/ir_device.json` | Cached Broadlink device |
| `PI_REMOTE_HID_KBD` | `/dev/hidg0` | Keyboard HID device node |
| `PI_REMOTE_HID_CONSUMER` | `/dev/hidg1` | Consumer-control HID device node |
| `PI_REMOTE_FFMPEG` | `ffmpeg` | ffmpeg binary for the RTSP live preview |
| `PI_REMOTE_STREAM_DIR` | `/dev/shm/pi-remote-stream` | HLS output dir (keep on tmpfs) |
| `PI_REMOTE_RTSP_TRANSPORT` | `tcp` | `tcp`/`udp`/`udp_multicast`/`http`/`auto` — use `udp_multicast` for multicast URLs |

After editing, restart the service:

```bash
sudo systemctl restart hid-keyboard-server
```

With Ansible, set values in `ansible/group_vars/all.yml` (e.g. `pi_remote_api_key`)
and re-run `ansible-playbook site.yml`; the config file is re-templated and the
service restarted automatically.

## Security

`pi-remote` can type into and power-cycle your devices, so treat the endpoint as
sensitive:

- **Set `PI_REMOTE_API_KEY`** to a long random string once it's reachable on your
  LAN. The web remote forwards the token automatically when you open it as
  `http://<pi>:8800/?token=YOURKEY`.
- Keep it on a trusted network segment; do **not** port-forward it to the
  internet.
- CORS is intentionally open (`Access-Control-Allow-Origin: *`) so the remote and
  ad-hoc tools work from any origin — the API key is the real gate.
