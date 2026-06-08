# Home Assistant

Two ways to use pi-remote with Home Assistant: **control it** from automations and
dashboards (REST calls to the API), and **embed** the web remote in a dashboard.

## Control with REST commands

Add to `configuration.yaml` (use the Pi's IP or a DHCP-reserved hostname):

```yaml
rest_command:
  pi_remote_key:
    url: "http://192.168.1.XXX:8800/key?key={{ key }}"
  pi_remote_media:
    url: "http://192.168.1.XXX:8800/media?key={{ key }}"
  pi_remote_ir:
    url: "http://192.168.1.XXX:8800/ir?cmd={{ cmd }}"
  pi_remote_type:
    url: "http://192.168.1.XXX:8800/type"
    method: POST
    content_type: "application/json"
    payload: '{"text": "{{ text }}"}'
```

If you set `PI_REMOTE_API_KEY`, add the header to each command:

```yaml
    headers:
      X-API-Key: !secret pi_remote_token
```

Reload REST commands (Developer Tools → YAML, or restart HA), then call them from
automations, scripts, or dashboard buttons:

```yaml
# navigation — UP/DOWN/LEFT/RIGHT/ENTER/BACK/...
service: rest_command.pi_remote_key
data:
  key: DOWN

# media / volume — PLAYPAUSE/VOLUP/VOLDOWN/MUTE/HOME/SEARCH/...
service: rest_command.pi_remote_media
data:
  key: VOLUP

# IR power via the RM4
service: rest_command.pi_remote_ir
data:
  cmd: power

# type into a focused field
service: rest_command.pi_remote_type
data:
  text: "my search term"
```

### Dashboard buttons

A single button card:

```yaml
type: button
name: ▼
tap_action:
  action: call-service
  service: rest_command.pi_remote_key
  data:
    key: DOWN
```

Lay several out in a `grid` for a D-pad, and add a Power button that calls
`rest_command.pi_remote_ir` with `cmd: power`. (See the [HTTP API](api.md) for the
full list of keys/media names/IR commands.)

## Embed the web remote

The page is frame-friendly (the server sends no `X-Frame-Options`/CSP), so HA can
embed it directly.

**Dashboard card** (Webpage / iframe):

```yaml
type: iframe
url: http://192.168.1.XXX:8800/?token=YOURKEY
aspect_ratio: 75%
```

Drop `?token=YOURKEY` if you didn't set `PI_REMOTE_API_KEY`.

**Sidebar panel** (adds a left-menu item) in `configuration.yaml`:

```yaml
panel_iframe:
  pi_remote:
    title: Pi Remote
    icon: mdi:remote
    url: http://192.168.1.XXX:8800/?token=YOURKEY
```

### HTTP vs HTTPS — the mixed-content rule

This is the thing that bites everyone:

- Open HA over **plain HTTP on your LAN** (`http://homeassistant.local:8123`) →
  the HTTP iframe works, and **both** preview modes (WebRTC + HLS) work.
  **Simplest setup — recommended.**
- Open HA over **HTTPS** (Nabu Casa cloud, or a TLS reverse proxy) → the browser
  **blocks** the plain-HTTP iframe as *mixed content*. You then need pi-remote
  over HTTPS too (next section).

!!! note
    The HA **companion mobile app** is stricter about insecure content than a
    desktop browser. If a card is blank in the app, confirm it works in a desktop
    browser first to isolate the mixed-content rule.

## Serving pi-remote over HTTPS

If your HA is HTTPS, put pi-remote (and go2rtc) behind a TLS reverse proxy and
embed the `https://` URL instead. In short:

- **HLS works through the proxy out of the box** (its segments are served by
  pi-remote itself — same origin).
- **WebRTC** additionally needs go2rtc proxied and
  `PI_REMOTE_GO2RTC_PUBLIC=https://cam.example.com` set on the Pi.
- The cert must be **browser-trusted** — a self-signed cert fails inside an
  iframe.

Full **Caddy** and **Traefik** configs are on the
**[Reverse proxy / TLS](reverse-proxy.md)** page.

## Other hubs

The API is just HTTP, so anything that can make web requests can drive pi-remote.
Using **Homey** instead? See **[Homey](homey.md)**.
