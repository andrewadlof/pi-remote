# Embedding in Home Assistant

The remote page is frame-friendly (the server sends no `X-Frame-Options`/CSP), so
Home Assistant can embed it directly.

## Dashboard card

Add a Webpage (iframe) card:

```yaml
type: iframe
url: http://192.168.1.XXX:8800/?token=YOURKEY
aspect_ratio: 75%
```

Drop `?token=YOURKEY` if you didn't set `PI_REMOTE_API_KEY`. Prefer a
DHCP-reserved IP or hostname so the URL stays stable.

## Sidebar panel

To add a left-menu item, in `configuration.yaml`:

```yaml
panel_iframe:
  pi_remote:
    title: Pi Remote
    icon: mdi:remote
    url: http://192.168.1.XXX:8800/?token=YOURKEY
```

## HTTP vs HTTPS — the mixed-content rule

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

## Homey

Homey has no generic web-page/iframe widget, so you can't embed the remote in the
Homey app. Drive pi-remote from Homey via **Flows** (see
[Homey integration](homey.md)); view the visual remote in a browser or in Home
Assistant.
