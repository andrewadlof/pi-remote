# Remote UI

`remote.html` is a single self-contained page (no build step, no dependencies)
served by the bridge at `/`. Open it on any phone, tablet, or desktop browser:

```
http://<pi-host>:8800/
```

If an API key is set, open it with the token so the buttons authenticate:

```
http://<pi-host>:8800/?token=YOURKEY
```

On a phone, use the browser's **Add to Home Screen** to get a full-screen,
app-like remote icon.

## Layout

| Group | Buttons |
| --- | --- |
| Navigation | D-pad ▲▼◀▶, OK, Back, Home, 🔍 Search |
| Media | ⏮ ⏯ ⏭, Vol −, Mute, Vol + |
| System | ⏻ Power (IR), 🌙 Screen off |
| Type text | text field + Send, Del, Space, Enter |

## How buttons map to the API

The page has three one-line helpers:

```js
function k(n){ hit('/key','key='+n); }    // keyboard / named key
function m(n){ hit('/media','key='+n); }  // consumer control
function ir(n){ hit('/ir','cmd='+n); }    // Broadlink IR
```

So a button is just:

```html
<button onclick="k('UP')">▲</button>
<button onclick="m('VOLUP')">Vol +</button>
<button onclick="ir('power')">Power</button>
```

## Customising

Edit `/opt/pi-remote/remote.html` directly on the Pi — **no restart needed**,
just reload the page (the server reads the file per request). Copy an existing
`<button>` line and change the call:

- `k('NAME')` for a [keyboard/named key](api.md#postget-key-single-key)
- `m('NAME')` for a [consumer control](api.md#postget-media-consumer-control)
- `ir('NAME')` for a [learned IR code](ir.md)

Keep the canonical copy in the repo's `src/remote.html` in sync if you want
Ansible re-runs to preserve your changes.
