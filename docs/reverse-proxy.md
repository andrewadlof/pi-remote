# Reverse proxy / TLS

You only need this if you want to reach pi-remote over **HTTPS** — e.g. to embed
it in an HTTPS Home Assistant, expose it through one hostname, or sit it behind a
homelab proxy alongside other services (Proxmox/MS-01, etc.).

pi-remote and go2rtc run on the **Pi**; the proxy (on another host) terminates TLS
and forwards to the Pi over the LAN.

## What to proxy

| Backend | On the Pi | Why |
| --- | --- | --- |
| pi-remote | `http://<pi-ip>:8800` | the remote UI + API + HLS preview |
| go2rtc | `http://<pi-ip>:1984` | the WebRTC player + signaling |

Then set on the Pi (so the embedded WebRTC player URL is HTTPS):

```
PI_REMOTE_GO2RTC_PUBLIC=https://cam.example.com
```

!!! note "Two things that always apply"
    - **WebRTC media (port 8555) does NOT go through the proxy** — it flows
      directly between the browser and the Pi. Keep 8555 reachable on the LAN.
      HLS, by contrast, is fully proxied (same origin as pi-remote).
    - **The cert must be browser-trusted.** Self-signed / `tls internal` certs
      silently fail *inside an iframe* — use Let's Encrypt (a real domain;
      DNS-01 works for internal-only hostnames).

---

## Caddy (simplest)

Automatic HTTPS, ~2 lines per route. `Caddyfile`:

```
remote.example.com {
    reverse_proxy 127.0.0.1:8800
}

cam.example.com {
    reverse_proxy 127.0.0.1:1984
}
```

(Replace `127.0.0.1` with the Pi's IP if Caddy runs on a different host.) Embed
`https://remote.example.com/?token=YOURKEY` in HA; set
`PI_REMOTE_GO2RTC_PUBLIC=https://cam.example.com`.

---

## Traefik (good when fronting many services)

Best when you're already routing several apps. Because pi-remote/go2rtc are
**not containers**, define them with the **file provider** (Docker labels are for
your containerized apps).

### Static config — `traefik.yml`

```yaml
entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"

providers:
  docker: {}                 # your containerized services (via labels)
  file:
    directory: /etc/traefik/dynamic
    watch: true

certificatesResolvers:
  le:
    acme:
      email: you@example.com
      storage: /etc/traefik/acme.json
      dnsChallenge:          # DNS-01 also issues certs for internal-only hosts
        provider: cloudflare
```

### Dynamic config — `/etc/traefik/dynamic/pi-remote.yml`

```yaml
http:
  routers:
    pi-remote:
      rule: "Host(`remote.example.com`)"
      entryPoints: [websecure]
      service: pi-remote
      tls:
        certResolver: le
    go2rtc:
      rule: "Host(`cam.example.com`)"
      entryPoints: [websecure]
      service: go2rtc
      tls:
        certResolver: le
  services:
    pi-remote:
      loadBalancer:
        servers:
          - url: "http://<pi-ip>:8800"     # the Pi
    go2rtc:
      loadBalancer:
        servers:
          - url: "http://<pi-ip>:1984"     # the Pi
```

### Running Traefik (Docker Compose)

```yaml
services:
  traefik:
    image: traefik:v3.1
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    environment:
      - CF_DNS_API_TOKEN=__your_cloudflare_token__   # for the DNS-01 challenge
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik.yml:/etc/traefik/traefik.yml:ro
      - ./dynamic:/etc/traefik/dynamic:ro
      - ./acme.json:/etc/traefik/acme.json
```

`touch acme.json && chmod 600 acme.json` before first start. Swap the DNS provider
/ token for whatever runs your domain.

### Containerized services on the same host

Those use labels instead of the file provider, e.g.:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.foo.rule=Host(`foo.example.com`)"
  - "traefik.http.routers.foo.entrypoints=websecure"
  - "traefik.http.routers.foo.tls.certresolver=le"
```

---

## WebRTC behind a proxy — recap

- Proxy go2rtc's **HTTP** (1984) for the player + signaling (done above).
- WebRTC **media** uses **8555** directly between browser and Pi — keep it open on
  the LAN. Same-LAN host candidates work out of the box; cross-subnet/remote
  access would need go2rtc WebRTC candidate/TURN configuration (out of scope).
- If WebRTC still won't embed, fall back to the **HLS** button — it's fully
  proxied and needs no extra ports.
