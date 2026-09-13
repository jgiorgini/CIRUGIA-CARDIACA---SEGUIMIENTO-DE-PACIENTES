import json
import os
import sqlite3
import threading
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path

VERSION = os.environ.get('RCV_VERSION', 'RCV-V1.0-PILOT-001')
ROOT = Path(__file__).resolve().parent
STATIC = ROOT / 'static'
DATA = ROOT / 'data'
DB = DATA / 'rcv.db'
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', '8767'))
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
USING_POSTGRES = bool(DATABASE_URL)

DATA.mkdir(exist_ok=True)

if USING_POSTGRES:
    import psycopg
    from psycopg.types.json import Jsonb


def default_state():
    return {
        'version': VERSION,
        'currentUser': {'name': 'Usuario piloto', 'role': 'Administrador'},
        'patients': [],
        'settings': {
            'volumeMeansFinalVolume': True,
            'defaultDiluent': 'SF',
            'drugDefaultsSource': 'droguitas.xlsx filas 1-30'
        },
        'drugConfig': []
    }


def init_db():
    if USING_POSTGRES:
        with psycopg.connect(DATABASE_URL) as c:
            c.execute('''
                CREATE TABLE IF NOT EXISTS app_state (
                    id SMALLINT PRIMARY KEY CHECK (id = 1),
                    payload JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            ''')
    else:
        with sqlite3.connect(DB) as c:
            c.execute('''
                CREATE TABLE IF NOT EXISTS app_state (
                    id INTEGER PRIMARY KEY CHECK(id=1),
                    payload TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')


def load_state():
    if USING_POSTGRES:
        with psycopg.connect(DATABASE_URL) as c:
            row = c.execute('SELECT payload FROM app_state WHERE id=1').fetchone()
        if not row:
            return default_state()
        payload = row[0]
        return payload if isinstance(payload, dict) else json.loads(payload)
    with sqlite3.connect(DB) as c:
        row = c.execute('SELECT payload FROM app_state WHERE id=1').fetchone()
    return json.loads(row[0]) if row else default_state()


def save_state(payload):
    if not isinstance(payload, dict):
        raise ValueError('payload inválido')
    payload['version'] = VERSION
    if USING_POSTGRES:
        with psycopg.connect(DATABASE_URL) as c:
            c.execute('''
                INSERT INTO app_state(id,payload,updated_at)
                VALUES (1,%s,NOW())
                ON CONFLICT(id) DO UPDATE
                SET payload=EXCLUDED.payload, updated_at=NOW()
            ''', (Jsonb(payload),))
        return
    text = json.dumps(payload, ensure_ascii=False)
    with sqlite3.connect(DB) as c:
        c.execute('''
            INSERT INTO app_state(id,payload,updated_at)
            VALUES(1,?,CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE
            SET payload=excluded.payload, updated_at=CURRENT_TIMESTAMP
        ''', (text,))


def reset_state():
    if USING_POSTGRES:
        with psycopg.connect(DATABASE_URL) as c:
            c.execute('DELETE FROM app_state WHERE id=1')
        return
    with sqlite3.connect(DB) as c:
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
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
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
        if p == '/api/health':
            return self._json(200, {
                'ok': True,
                'version': VERSION,
                'storage': 'postgresql' if USING_POSTGRES else 'sqlite'
            })
        if p == '/api/state':
            return self._json(200, load_state())
        if p == '/api/backup':
            raw = json.dumps(load_state(), ensure_ascii=False, indent=2).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="{VERSION}-backup.json"')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
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
            reset_state()
            return self._json(200, {'ok':True})
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
        if os.environ.get('RCV_HTTP_LOG', '0') == '1':
            super().log_message(fmt, *args)


if __name__ == '__main__':
    init_db()
    os.chdir(STATIC)
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)

    local_url = f'http://127.0.0.1:{PORT}'
    if not os.environ.get('RENDER') and os.environ.get('OPEN_BROWSER', '1') == '1':
        threading.Timer(0.7, lambda: webbrowser.open(local_url)).start()

    print('=' * 64)
    print(VERSION)
    print(f'URL local: {local_url}')
    print(f'Almacenamiento: {"PostgreSQL" if USING_POSTGRES else str(DB)}')
    print('=' * 64)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
