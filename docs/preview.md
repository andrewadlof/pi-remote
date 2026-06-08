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

1. Open the remote (`http://<pi>:8800/`).
2. In **Live preview**, paste a URL and press **Load**:
   - **`rtsp://…`** → the Pi starts the ffmpeg relay and plays the result
     (≈3 s latency).
   - **`https://….m3u8`** (HLS) → played directly by the browser, no Pi load.
   - **`.mp4` / `.webm`** → played directly.
3. **Stop preview** stops playback and the relay.

The last URL is remembered in the browser (localStorage).

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
- **Latency**: HLS adds a few seconds. For near-real-time, run a dedicated
  RTSP→WebRTC server such as [go2rtc](https://github.com/AlexxIT/go2rtc) or
  [MediaMTX](https://github.com/bluenviron/mediamtx) on a capable host and paste
  its HLS/WHEP URL instead — the panel will play an `.m3u8` directly.
