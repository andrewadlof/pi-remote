#!/usr/bin/env python3
"""pi-remote HID keyboard + consumer bridge + web remote + Broadlink IR.

Stdlib only (no third-party imports in this process). Endpoints:
  GET  /                       -> web remote UI (remote.html)
  GET/POST /type   text        -> type a string on the USB keyboard
  GET/POST /key    key[+mod]   -> single key (named or single char)
  GET/POST /press  key+mods    -> key combo, e.g. Ctrl+A, Alt+Tab
  GET/POST /media  name        -> consumer control (HOME/PLAYPAUSE/VOLUP/...)
  GET/POST /ir     cmd=NAME    -> send a learned IR code via Broadlink (ir_tool.py)

Auth (optional): set PI_REMOTE_API_KEY; then every request must pass
?token=... or the header X-API-Key. The remote UI is always served so it
can read the token from its own URL.

Configuration is read from environment variables (see config/config.example.env):
  PI_REMOTE_PORT, PI_REMOTE_API_KEY, PI_REMOTE_KEY_DELAY,
  PI_REMOTE_HTML, PI_REMOTE_IR_TOOL, PI_REMOTE_HID_KBD, PI_REMOTE_HID_CONSUMER
"""
import glob, json, os, re, subprocess, sys, time, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HID_KBD      = os.environ.get("PI_REMOTE_HID_KBD", "/dev/hidg0")
HID_CONSUMER = os.environ.get("PI_REMOTE_HID_CONSUMER", "/dev/hidg1")
REMOTE_HTML  = os.environ.get("PI_REMOTE_HTML", "/opt/pi-remote/remote.html")
IR_TOOL      = os.environ.get("PI_REMOTE_IR_TOOL", "/opt/pi-remote/ir_tool.py")
API_KEY      = os.environ.get("PI_REMOTE_API_KEY", "")
KEY_DELAY    = float(os.environ.get("PI_REMOTE_KEY_DELAY", "0.008"))
PORT         = int(os.environ.get("PI_REMOTE_PORT", "8800"))
STREAM_DIR   = os.environ.get("PI_REMOTE_STREAM_DIR", "/dev/shm/pi-remote-stream")
FFMPEG       = os.environ.get("PI_REMOTE_FFMPEG", "ffmpeg")
# RTSP transport: tcp | udp | udp_multicast | http | auto (auto = let ffmpeg choose)
RTSP_TRANSPORT = os.environ.get("PI_REMOTE_RTSP_TRANSPORT", "tcp")
# go2rtc (optional, for low-latency WebRTC preview)
GO2RTC_API    = os.environ.get("PI_REMOTE_GO2RTC", "http://127.0.0.1:1984")
GO2RTC_PORT   = os.environ.get("PI_REMOTE_GO2RTC_PORT", "1984")
GO2RTC_STREAM = os.environ.get("PI_REMOTE_GO2RTC_STREAM", "android")
# Public base URL of go2rtc when behind a TLS reverse proxy, e.g. https://cam.example.com
GO2RTC_PUBLIC = os.environ.get("PI_REMOTE_GO2RTC_PUBLIC", "")

SHIFT = 0x02
_MODS = {'CTRL':0x01,'SHIFT':0x02,'ALT':0x04,'GUI':0x08,'WIN':0x08,'META':0x08,
         'RCTRL':0x10,'RSHIFT':0x20,'RALT':0x40,'ALTGR':0x40}
_BASE = {
    'a':0x04,'b':0x05,'c':0x06,'d':0x07,'e':0x08,'f':0x09,'g':0x0a,'h':0x0b,
    'i':0x0c,'j':0x0d,'k':0x0e,'l':0x0f,'m':0x10,'n':0x11,'o':0x12,'p':0x13,
    'q':0x14,'r':0x15,'s':0x16,'t':0x17,'u':0x18,'v':0x19,'w':0x1a,'x':0x1b,
    'y':0x1c,'z':0x1d,
    '1':0x1e,'2':0x1f,'3':0x20,'4':0x21,'5':0x22,'6':0x23,'7':0x24,'8':0x25,
    '9':0x26,'0':0x27,'\n':0x28,'\t':0x2b,' ':0x2c,
    '-':0x2d,'=':0x2e,'[':0x2f,']':0x30,'\\':0x31,';':0x33,"'":0x34,'`':0x35,
    ',':0x36,'.':0x37,'/':0x38,
}
_SHIFTED = {
    '!':'1','@':'2','#':'3','$':'4','%':'5','^':'6','&':'7','*':'8','(':'9',')':'0',
    '_':'-','+':'=','{':'[','}':']','|':'\\',':':';','"':"'",'~':'`',
    '<':',','>':'.','?':'/',
}
_NAMED = {
    'ENTER':(0,0x28),'RETURN':(0,0x28),'OK':(0,0x28),'SELECT':(0,0x28),
    'ESC':(0,0x29),'BACK':(0,0x29),'BACKSPACE':(0,0x2a),'TAB':(0,0x2b),
    'SPACE':(0,0x2c),'DELETE':(0,0x4c),'INSERT':(0,0x49),'HOME':(0,0x4a),
    'END':(0,0x4d),'PAGEUP':(0,0x4b),'PAGEDOWN':(0,0x4e),'CAPSLOCK':(0,0x39),
    'RIGHT':(0,0x4f),'LEFT':(0,0x50),'DOWN':(0,0x51),'UP':(0,0x52),'APP':(0,0x65),
}
for i in range(1,13): _NAMED['F%d' % i] = (0, 0x39 + i)
_CONSUMER = {
    'PLAYPAUSE':0x00CD,'PLAY':0x00CD,'PAUSE':0x00CD,'SLEEP':0x0032,
    'NEXT':0x00B5,'PREV':0x00B6,'PREVIOUS':0x00B6,'STOP':0x00B7,'FF':0x00B3,'REWIND':0x00B4,
    'MUTE':0x00E2,'VOLUP':0x00E9,'VOLUMEUP':0x00E9,'VOLDOWN':0x00EA,'VOLUMEDOWN':0x00EA,
    'HOME':0x0223,'MEDIABACK':0x0224,'MENU':0x0040,'SEARCH':0x0221,'POWER':0x0030,
}

def char_to_report(c):
    if c in _SHIFTED: return (SHIFT, _BASE[_SHIFTED[c]])
    if c.isupper() and c.lower() in _BASE: return (SHIFT, _BASE[c.lower()])
    if c in _BASE: return (0, _BASE[c])
    return None
def _modmask(mods):
    m = 0
    for x in (mods or []): m |= _MODS.get(str(x).upper(), 0)
    return m
def _write_kbd(mod, code):
    with open(HID_KBD, 'rb+') as fd:
        fd.write(bytes([mod,0,code,0,0,0,0,0])); fd.write(bytes(8))
def type_text(text):
    n = 0
    for c in text:
        r = char_to_report(c)
        if r is None: continue
        _write_kbd(*r); n += 1; time.sleep(KEY_DELAY)
    return n
def press(key, mods=None):
    mod = _modmask(mods); key = str(key)
    if key.upper() in _NAMED:
        bm, code = _NAMED[key.upper()]; mod |= bm
    elif len(key) == 1:
        r = char_to_report(key)
        if r is None: raise KeyError(key)
        bm, code = r; mod |= bm
    else: raise KeyError(key)
    _write_kbd(mod, code)
def media(name):
    name = (name or "").upper()
    if name not in _CONSUMER: raise KeyError(name)
    code = _CONSUMER[name]
    with open(HID_CONSUMER, 'rb+') as fd:
        fd.write(bytes([code & 0xFF, (code >> 8) & 0xFF])); fd.write(bytes(2))
def ir_send(name):
    name = (name or "").strip()
    if not name or "/" in name or ".." in name: raise KeyError(name)
    env = dict(os.environ)
    r = subprocess.run([sys.executable, IR_TOOL, "send", name],
                       capture_output=True, text=True, timeout=15, env=env)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip() or "ir send failed")

# --- RTSP -> HLS live preview (ffmpeg remux, no transcode) ---
_ffmpeg = None
def stream_start(url):
    global _ffmpeg
    url = (url or "").strip()
    if not re.match(r'^rtsps?://', url, re.I):
        raise ValueError("only rtsp:// URLs can be relayed")
    stream_stop()
    os.makedirs(STREAM_DIR, exist_ok=True)
    for f in glob.glob(os.path.join(STREAM_DIR, "*")):
        try: os.remove(f)
        except OSError: pass
    cmd = [FFMPEG, "-nostdin", "-loglevel", "error", "-fflags", "nobuffer"]
    if RTSP_TRANSPORT and RTSP_TRANSPORT.lower() != "auto":
        cmd += ["-rtsp_transport", RTSP_TRANSPORT]
    cmd += ["-i", url, "-an", "-c:v", "copy",
            "-f", "hls", "-hls_time", "1", "-hls_list_size", "3",
            "-hls_flags", "delete_segments+append_list+omit_endlist",
            "-hls_segment_filename", os.path.join(STREAM_DIR, "seg_%05d.ts"),
            os.path.join(STREAM_DIR, "live.m3u8")]
    try:
        _ffmpeg = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        raise RuntimeError("ffmpeg is not installed")
    return "/stream/live.m3u8"

def stream_stop():
    global _ffmpeg
    if _ffmpeg and _ffmpeg.poll() is None:
        try:
            _ffmpeg.terminate(); _ffmpeg.wait(timeout=3)
        except Exception:
            try: _ffmpeg.kill()
            except Exception: pass
    _ffmpeg = None

def webrtc_start(url, host):
    """Register an RTSP source with go2rtc and return an embeddable WebRTC player URL."""
    name = GO2RTC_STREAM
    url = (url or "").strip()
    if url:
        if not re.match(r'^rtsps?://', url, re.I):
            raise ValueError("only rtsp:// URLs can be relayed")
        name = "preview"
        qs = urllib.parse.urlencode({"name": name, "src": url})
        api = GO2RTC_API.rstrip("/") + "/api/streams?" + qs
        last = None
        for method in ("PUT", "POST"):
            try:
                urllib.request.urlopen(urllib.request.Request(api, method=method), timeout=5).read()
                last = None; break
            except Exception as e:
                last = e
        if last is not None:
            raise RuntimeError("go2rtc not reachable: %s" % last)
    if GO2RTC_PUBLIC:
        base = GO2RTC_PUBLIC.rstrip("/")
    else:
        h = (host or "").split(":")[0] or "127.0.0.1"
        base = "http://%s:%s" % (h, GO2RTC_PORT)
    return "%s/webrtc.html?src=%s" % (base, name)

class Handler(BaseHTTPRequestHandler):
    def _auth(self, q):
        if not API_KEY: return True
        return (self.headers.get('X-API-Key') or q.get('token',[''])[0]) == API_KEY
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Headers','Content-Type,X-API-Key')
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code); self._cors()
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def _html(self):
        try:
            with open(REMOTE_HTML,'rb') as f: body = f.read()
        except FileNotFoundError:
            body = b'<h1>remote.html not found</h1>'
        self.send_response(200); self._cors()
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def _serve_stream(self, path):
        name = path[len('/stream/'):]
        if not re.match(r'^[A-Za-z0-9_.\-]+\.(m3u8|ts)$', name):
            return self._send(404, {'error': 'not found'})
        try:
            with open(os.path.join(STREAM_DIR, name), 'rb') as f: body = f.read()
        except FileNotFoundError:
            return self._send(404, {'error': 'not found'})
        ctype = 'application/vnd.apple.mpegurl' if name.endswith('.m3u8') else 'video/mp2t'
        self.send_response(200); self._cors()
        self.send_header('Content-Type', ctype)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def _parse(self):
        u = urlparse(self.path); return u.path, parse_qs(u.query)
    def _json(self):
        n = int(self.headers.get('Content-Length',0) or 0)
        if not n: return {}
        raw = self.rfile.read(n)
        try: return json.loads(raw)
        except Exception: return {'text': raw.decode('utf-8','ignore')}
    def do_OPTIONS(self):
        self.send_response(204); self._cors()
        self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS')
        self.send_header('Content-Length','0'); self.end_headers()
    def do_GET(self):  self._handle(False)
    def do_POST(self): self._handle(True)
    def _handle(self, post):
        path, q = self._parse()
        if path in ('/', '/remote', '/index.html'): return self._html()
        if path.startswith('/stream/') and path not in ('/stream/start', '/stream/stop'):
            return self._serve_stream(path)
        if not self._auth(q): return self._send(401, {'error':'unauthorized'})
        d = self._json() if post else {}
        def gv(k):
            if post and k in d: return d[k]
            return q.get(k, [''])[0]
        m = d.get('mods') or d.get('mod') or q.get('mod')
        if m and not isinstance(m, list): m = [m]
        try:
            if path == '/type':           return self._send(200, {'typed': type_text(gv('text'))})
            if path in ('/key','/press'): press(gv('key'), m); return self._send(200, {'pressed': gv('key')})
            if path == '/media':          media(gv('key')); return self._send(200, {'media': gv('key')})
            if path == '/ir':             ir_send(gv('cmd')); return self._send(200, {'ir': gv('cmd')})
            if path == '/stream/start':   return self._send(200, {'hls': stream_start(gv('url'))})
            if path == '/stream/stop':    stream_stop(); return self._send(200, {'stopped': True})
            if path == '/webrtc/start':   return self._send(200, {'embed': webrtc_start(gv('url'), self.headers.get('Host',''))})
        except KeyError as e:          return self._send(400, {'error':'unknown key: %s' % e})
        except ValueError as e:        return self._send(400, {'error':'%s' % e})
        except RuntimeError as e:      return self._send(502, {'error':'%s' % e})
        except FileNotFoundError as e: return self._send(503, {'error':'device missing: %s' % e})
        return self._send(200, {'status':'ok','endpoints':['/','/type','/key','/press','/media','/ir','/stream/start','/stream/stop','/webrtc/start']})
    def log_message(self, *a): pass

def wait_for(path, timeout=30):
    dl = time.time() + timeout
    while not os.path.exists(path) and time.time() < dl: time.sleep(0.5)

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    wait_for(HID_KBD)
    print("pi-remote HID bridge + remote + IR on :%d" % port, flush=True)
    ThreadingHTTPServer(('0.0.0.0', port), Handler).serve_forever()
