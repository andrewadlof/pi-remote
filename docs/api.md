# HTTP API

Base URL: `http://<pi-host>:8800`. All endpoints accept **GET** (query string) or
**POST** (JSON body). If `PI_REMOTE_API_KEY` is set, add `?token=YOURKEY` or the
header `X-API-Key: YOURKEY`. Responses are JSON.

## `GET /`

Serves the web remote (`remote.html`). Always available, even with auth enabled,
so the page can read the token from its own URL.

## `POST|GET /type` — type a string

Types text on the USB keyboard. Unsupported characters are skipped.

```bash
curl -X POST http://pi:8800/type -d '{"text":"hello world 123!"}'
curl "http://pi:8800/type?text=hello"
```

Response: `{"typed": 16}` (number of characters sent).

## `POST|GET /key` — single key

`key` is a named key or a single character. Optional `mod`/`mods`.

```bash
curl "http://pi:8800/key?key=DOWN"
curl "http://pi:8800/key?key=ENTER"
```

**Named keys:** `ENTER` `OK` `SELECT` `ESC` `BACK` `BACKSPACE` `TAB` `SPACE`
`DELETE` `INSERT` `HOME` `END` `PAGEUP` `PAGEDOWN` `CAPSLOCK` `UP` `DOWN` `LEFT`
`RIGHT` `APP` `F1`–`F12`.

## `POST|GET /press` — key combo

Same as `/key` but intended for modifier combos.

```bash
curl "http://pi:8800/press?key=a&mod=CTRL"                 # Ctrl+A
curl "http://pi:8800/press?key=TAB&mod=ALT"                # Alt+Tab
curl -X POST http://pi:8800/press -d '{"key":"t","mods":["CTRL","SHIFT"]}'
```

**Modifiers:** `CTRL` `SHIFT` `ALT` `GUI`/`WIN`/`META` (and right-side
`RCTRL` `RSHIFT` `RALT`/`ALTGR`).

## `POST|GET /media` — consumer control

Sends a USB HID **consumer** usage (separate from the keyboard).

```bash
curl "http://pi:8800/media?key=PLAYPAUSE"
curl "http://pi:8800/media?key=VOLUP"
```

**Names:** `PLAYPAUSE` `PLAY` `PAUSE` `STOP` `NEXT` `PREV` `FF` `REWIND`
`MUTE` `VOLUP` `VOLDOWN` `HOME` `MEDIABACK` `MENU` `SEARCH` `POWER` `SLEEP`.

!!! tip "Android mapping notes"
    - **Back** that Android honors as the system back is `MEDIABACK` (AC Back),
      not keyboard `ESC`.
    - **Home** is `HOME` (consumer AC Home).
    - `KEYCODE_MENU` is ignored by most Android TV apps — `MENU`/`APP` often do
      nothing. Prefer `SEARCH`, or use IR for box-specific buttons.

## `POST|GET /ir` — Broadlink IR

Sends a previously learned IR code (see **[IR / Broadlink](ir.md)**).

```bash
curl "http://pi:8800/ir?cmd=power"
```

Response: `{"ir":"power"}`. Errors return `502` with the helper's message.

## Status / errors

| Code | Meaning |
| --- | --- |
| `200` | OK |
| `400` | unknown key/name |
| `401` | missing/invalid API key |
| `502` | IR send failed (no device, unknown code) |
| `503` | HID device missing (`/dev/hidg*` not present) |
