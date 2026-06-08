# Homey integration

Homey drives `pi-remote` by making HTTP calls to the bridge — the same endpoints
documented in the [HTTP API](api.md). Two common approaches:

## Option 1 — HomeyScript (most flexible)

Install the **HomeyScript** app, then use a "Run code" action card in a Flow:

```js
const BASE = 'http://pi-remote.local:8800';
const TOKEN = 'YOURKEY'; // omit if no API key
const q = TOKEN ? `&token=${TOKEN}` : '';

// press a navigation key
await fetch(`${BASE}/key?key=DOWN${q ? '?' + q.slice(1) : ''}`);

// or, cleaner helpers:
async function key(k){ await fetch(`${BASE}/key?key=${k}${q}`); }
async function media(m){ await fetch(`${BASE}/media?key=${m}${q}`); }
async function ir(c){ await fetch(`${BASE}/ir?cmd=${c}${q}`); }

await ir('power');             // turn the box on/off
```

To type text:

```js
await fetch(`${BASE}/type${TOKEN ? '?token=' + TOKEN : ''}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: 'my search term' }),
});
```

## Option 2 — HTTP request Flow cards

Install an HTTP-request Flow app (e.g. *HTTP request Flow* by Dorian Brunner) and
drop **GET** cards into a Flow's *Then* column pointing at, for example:

```
http://pi-remote.local:8800/key?key=UP&token=YOURKEY
http://pi-remote.local:8800/media?key=VOLUP&token=YOURKEY
http://pi-remote.local:8800/ir?cmd=power&token=YOURKEY
```

## Building a Homey remote

Create one Flow per action (Up/Down/Left/Right/OK/Back/Power/Volume) and trigger
them from:

- a Homey **virtual device** with buttons, or
- physical buttons / a wall remote, or
- voice ("Hey Google, turn on the TV box" → Flow → `/ir?cmd=power`).

!!! tip
    Use a DHCP reservation (or the `*.local` mDNS name) for the Pi so the URLs in
    your Flows don't break when the lease changes.
