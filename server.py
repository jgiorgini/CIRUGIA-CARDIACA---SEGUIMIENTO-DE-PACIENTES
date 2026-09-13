import json, os, sqlite3, threading, webbrowser, socket
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path

VERSION = 'RCV-V1.0-LOCAL-004'
ROOT = Path(__file__).resolve().parent
STATIC = ROOT / 'static'
DATA = ROOT / 'data'
DB = DATA / 'rcv.db'
HOST = '0.0.0.0'
PORT = 8767

DATA.mkdir(exist_ok=True)

def conn():
    c = sqlite3.connect(DB)
    c.execute('CREATE TABLE IF NOT EXISTS app_state (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    return c

def default_state():
    return {
        'version': VERSION,
        'currentUser': {'name': 'Usuario local', 'role': 'Administrador'},
        'patients': [],
        'settings': {
            'volumeMeansFinalVolume': True,
            'defaultDiluent': 'SF',
            'drugDefaultsSource': 'droguitas.xlsx filas 1-30'
        },
        'drugConfig': []
    }

def load_state():
    with conn() as c:
        row = c.execute('SELECT payload FROM app_state WHERE id=1').fetchone()
    return json.loads(row[0]) if row else default_state()

def save_state(payload):
    if not isinstance(payload, dict):
        raise ValueError('payload inválido')
    payload['version'] = VERSION
    text = json.dumps(payload, ensure_ascii=False)
    with conn() as c:
        c.execute('INSERT INTO app_state(id,payload,updated_at) VALUES(1,?,CURRENT_TIMESTAMP) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, updated_at=CURRENT_TIMESTAMP', (text,))

def reset_state():
    with conn() as c:
        c.execute('DELETE FROM app_state WHERE id=1')

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urlparse(path).path
        if parsed.startswith('/api/'):
            return str(STATIC / '__api__')
        if parsed == '/':
            return str(STATIC / 'index.html')
        return str(STATIC / parsed.lstrip('/'))

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def _json(self, code, obj):
        raw = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        p = urlparse(self.path).path
        if p == '/api/state':
            return self._json(200, load_state())
        if p == '/api/backup':
            raw = json.dumps(load_state(), ensure_ascii=False, indent=2).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="{VERSION}-backup.json"')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers(); self.wfile.write(raw); return
        return super().do_GET()

    def do_PUT(self):
        p = urlparse(self.path).path
        if p == '/api/state':
            try:
                n = int(self.headers.get('Content-Length','0'))
                body = self.rfile.read(n)
                payload = json.loads(body.decode('utf-8'))
                save_state(payload)
                return self._json(200, {'ok': True})
            except Exception as e:
                return self._json(400, {'ok': False, 'error': str(e)})
        return self._json(404, {'error':'not found'})

    def do_POST(self):
        p = urlparse(self.path).path
        if p == '/api/reset':
            reset_state(); return self._json(200, {'ok':True})
        if p == '/api/restore':
            try:
                n = int(self.headers.get('Content-Length','0'))
                payload = json.loads(self.rfile.read(n).decode('utf-8'))
                save_state(payload)
                return self._json(200, {'ok':True})
            except Exception as e:
                return self._json(400, {'ok':False,'error':str(e)})
        return self._json(404, {'error':'not found'})

    def log_message(self, fmt, *args):
        pass

if __name__ == '__main__':
    os.chdir(STATIC)
    try:
        httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as e:
        print('=' * 64)
        print(f'ERROR: no se pudo iniciar {VERSION} en el puerto {PORT}.')
        print(f'Detalle: {e}')
        print('Cierre otra instancia que use ese puerto y vuelva a intentar.')
        print('=' * 64)
        input('Presione Enter para salir...')
        raise SystemExit(1)

    local_url = f'http://127.0.0.1:{PORT}'
    lan_ip = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        lan_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    threading.Timer(0.7, lambda: webbrowser.open(local_url)).start()
    print('=' * 64)
    print(VERSION)
    print(f'PC:      {local_url}')
    if lan_ip:
        print(f'CELULAR: http://{lan_ip}:{PORT}')
    else:
        print('CELULAR: no se pudo detectar la IP local automaticamente.')
    print(f'Base local: {DB}')
    print('=' * 64)
    print('Cerrar esta ventana detiene ESTA version de RCV.')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
