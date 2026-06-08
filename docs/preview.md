# Live preview

The web remote has a **Live preview** panel below the buttons so you can watch the
Android box's screen and control it from the same page — handy for confirming what
each remote input does.

## The browser constraint

**No browser can play `rtsp://` directly.** To preview an RTSP source the Pi
relays it into a browser-playable format. `pi-remote` uses **ffmpeg to remux RTSP
→ HLS** (`-c copy`, *no* transcoding, so it's light enough for a Pi), and plays it
with [hls.js](https://github.com/video-dev/hls.js).

```
RTSP source ──▶ ffmpeg (remux, copy) ──▶ HLS in /dev/shm ──▶ hls.js in browser
```

## Requirements

- **ffmpeg** on the Pi (the Ansible `common` role installs it when
  `install_ffmpeg: true`; manually: `sudo apt install -y ffmpeg`).
- An **RTSP source** of the box's screen — e.g. an HDMI→RTSP capture device, or an
  IP camera pointed at the TV.
- The browser device needs internet for the hls.js CDN script (or vendor it
  locally).

## Using it

1. Open the remote (`http://<pi>:8800/`). The last URL is remembered and the
   preview **auto-starts in WebRTC** on open.
2. In **Live preview**, with a URL in the box:
   - **Load** → low-latency **WebRTC** via go2rtc (default).
   - **HLS** → the ffmpeg RTSP→HLS relay (works without go2rtc; also plays a
     pasted `.m3u8` / `.mp4` / `.webm` directly).
3. **Stop preview** stops playback (and the HLS relay).

## Endpoints

These power the panel (see the [HTTP API](api.md)):

| Endpoint | Action |
| --- | --- |
| `GET /stream/start?url=rtsp://…` | start the ffmpeg relay → returns `{"hls":"/stream/live.m3u8"}` |
| `GET /stream/stop` | stop the relay |
| `GET /stream/<file>.m3u8\|.ts` | serve the HLS playlist/segments |

`start`/`stop` honour the API key; the segment files are served without auth so any
HLS player can read them (LAN only).

## Performance & notes

- **Pi Zero (armv6) is weak.** Remuxing (copy) one modest-bitrate H.264 stream is
  fine, but a high-bitrate 1080p60 source may stutter. Lower the source bitrate if
  needed. Transcoding is intentionally **not** attempted on-device.
- **Codec**: `-c copy` requires the source video to be **H.264** (the usual case).
  Non-H.264 sources won't play without transcoding.
- **SD-card wear**: HLS segments are written to `/dev/shm` (RAM) by default — keep
  it that way. Override with `PI_REMOTE_STREAM_DIR` only if you know why.
- **RTSP transport**: defaults to `tcp`. **Multicast** camera URLs (those with
  `/multicast/` in the path) need `PI_REMOTE_RTSP_TRANSPORT=udp_multicast` — a
  forced TCP setup on a multicast stream fails with `461 Unsupported Transport`.
  Other values: `udp`, `http`, `auto`.
- **Latency**: HLS adds a few seconds (bounded by the camera keyframe interval).
  For **sub-second** latency, use the **WebRTC** button (go2rtc) — see below.

## Low-latency WebRTC (go2rtc)

**Load** (the default preview button) plays the stream through
[go2rtc](https://github.com/AlexxIT/go2rtc), which remuxes H.264 RTSP straight to
WebRTC (no transcode) for **sub-second** latency — ideal for seeing remote inputs
in real time. go2rtc has an **armv6** build that runs on the Pi Zero. (The **HLS**
button is the ffmpeg fallback.)

How it works: the server registers the URL you typed with go2rtc's API and the
page embeds go2rtc's WebRTC player (`http://<pi>:1984/webrtc.html?src=…`) in an
iframe. With no URL typed, it plays the preconfigured stream
(`PI_REMOTE_GO2RTC_STREAM`, default `android`).

### Install go2rtc

Ansible installs it automatically (`install_go2rtc: true`). Manually:

```bash
# Pi Zero / Zero W (armv6); for a 64-bit Pi use go2rtc_linux_arm64
sudo curl -L -o /usr/local/bin/go2rtc \
  https://github.com/AlexxIT/go2rtc/releases/latest/download/go2rtc_linux_armv6
sudo chmod +x /usr/local/bin/go2rtc

# minimal config
sudo tee /etc/go2rtc.yaml >/dev/null <<'YAML'
api:
  listen: ":1984"
streams:
  android: rtsp://192.168.1.176:554/live/second/unicast/av_stream
YAML

# service
sudo tee /etc/systemd/system/go2rtc.service >/dev/null <<'UNIT'
[Unit]
Description=go2rtc (RTSP -> WebRTC gateway)
After=network-online.target
Wants=network-online.target
[Service]
ExecStart=/usr/local/bin/go2rtc -config /etc/go2rtc.yaml
Restart=on-failure
RestartSec=2
[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable --now go2rtc
```

Check it: open `http://<pi>:1984/` (go2rtc's own UI) and confirm the stream plays.

### Notes

- **Ports**: the browser needs to reach go2rtc on **1984** (API/player) and
  **8555** (WebRTC, go2rtc's default) on the Pi.
- **Codec**: WebRTC needs **H.264** video (your source already is) — go2rtc copies
  it, so the Pi Zero isn't transcoding.
- If WebRTC won't connect but go2rtc's own UI works, it's almost always a
  port/ICE-candidate/firewall issue on 8555 — keep the Pi and viewer on the same
  LAN.
