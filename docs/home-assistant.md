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

## Serving pi-remote over HTTPS (reverse proxy)

Put a reverse proxy in front and terminate TLS. **Caddy** is the easiest choice
(automatic HTTPS, ~2 lines per route — lighter than Traefik for a couple of static
backends). Example `Caddyfile` with a real domain (automatic Let's Encrypt):

```
remote.example.com {
    reverse_proxy 127.0.0.1:8800
}
```

Then embed `https://remote.example.com/?token=YOURKEY` in HA.

- **HLS preview works out of the box** behind HTTPS — its playlist/segments are
  served by pi-remote itself (same origin), so no mixed content. This is the
  reliable choice for HTTPS/remote embedding (and a good reason the HLS fallback
  exists).
- **WebRTC behind HTTPS** also needs go2rtc proxied over HTTPS, plus an
  HTTPS-aware embed URL. Add a second route:

  ```
  cam.example.com {
      reverse_proxy 127.0.0.1:1984
  }
  ```

  and set on the Pi:

  ```
  PI_REMOTE_GO2RTC_PUBLIC=https://cam.example.com
  ```

  so the player URL the page embeds is HTTPS. go2rtc's WebRTC **media** (port
  8555) still flows directly between the browser and the Pi.

!!! warning "Self-signed certs don't work in iframes"
    A browser won't let you click through a certificate warning *inside* an
    iframe, so a self-signed / `tls internal` cert silently fails to embed. Use a
    **browser-trusted** cert — a real domain with Let's Encrypt (HTTP-01 if
    reachable, or DNS-01 for LAN-only names) — or stick with the HTTP-LAN setup.

## Homey

Homey has no generic web-page/iframe widget, so you can't embed the remote in the
Homey app. Drive pi-remote from Homey via **Flows** (see
[Homey integration](homey.md)); view the visual remote in a browser or in Home
Assistant.
