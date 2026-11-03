"""Loopback-only static server. No uploads, filesystem writes or external libraries."""
import argparse
import webbrowser
import json
from urllib.request import urlopen
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import socket

class ViewerServer(ThreadingHTTPServer):
    allow_reuse_address=False

    def server_bind(self):
        if hasattr(socket,'SO_EXCLUSIVEADDRUSE'):
            self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        super().server_bind()

class ViewerHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        path=Path(self.translate_path(self.path))
        if not path.is_file():
            return super().send_head()
        if self.headers.get('If-Modified-Since') and not self.headers.get('If-None-Match'):
            try:
                since=parsedate_to_datetime(self.headers['If-Modified-Since'])
                if since.tzinfo is None:since=since.replace(tzinfo=timezone.utc)
                modified=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).replace(microsecond=0)
                if modified<=since:
                    self.send_response(304);self.send_header('Vary','Accept-Encoding');self.send_header('Cache-Control','no-cache');self.end_headers();return None
            except (ValueError,TypeError,OverflowError):
                pass
        accepted={}
        for item in self.headers.get('Accept-Encoding','').split(','):
            parts=item.strip().split(';');quality=1.0
            for parameter in parts[1:]:
                if parameter.strip().startswith('q='):
                    try:quality=float(parameter.strip()[2:])
                    except ValueError:quality=0
            accepted[parts[0].strip().lower()]=quality
        sidecar=path.with_name(path.name+'.gz')
        compressed=(accepted.get('gzip',accepted.get('*',0))>0 and sidecar.is_file()
                    and sidecar.stat().st_mtime_ns>=path.stat().st_mtime_ns
                    and sidecar.stat().st_size<path.stat().st_size)
        source=sidecar if compressed else path
        try:stream=source.open('rb')
        except OSError:
            self.send_error(404,'File not found');return None
        self.send_response(200)
        self.send_header('Content-Type',self.guess_type(str(path)))
        self.send_header('Content-Length',str(source.stat().st_size))
        self.send_header('Last-Modified',self.date_time_string(path.stat().st_mtime))
        self.send_header('Vary','Accept-Encoding')
        # 每次向本机服务校验（304 很便宜），避免更新后浏览器继续用旧脚本/样式。
        self.send_header('Cache-Control','no-cache')
        if compressed:self.send_header('Content-Encoding','gzip')
        self.end_headers();return stream

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8780)
    ap.add_argument('--directory', type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument('--open', action='store_true', help='Open the viewer after the server is bound')
    args = ap.parse_args()
    handler = partial(ViewerHandler, directory=str(args.directory.resolve()))
    url = f'http://127.0.0.1:{args.port}/'
    # Windows may allow two SO_REUSEADDR listeners; detect our existing viewer first.
    try:
        with urlopen(url + 'web/world.json', timeout=.5) as response:
            existing = json.load(response)
    except Exception:
        existing = None
    if existing and existing.get('name') == '谷中 · 此间':
        print(f'Already running: {url}', flush=True)
        if args.open:
            webbrowser.open(url)
        raise SystemExit(0)
    try:
        server = ViewerServer(('127.0.0.1', args.port), handler)
    except OSError:
        # Opening the launcher again reuses this viewer's existing local server.
        try:
            with urlopen(url + 'web/world.json', timeout=2) as response:
                existing = json.load(response)
            if existing.get('name') != '谷中 · 此间':
                raise ValueError('Port belongs to another service')
        except Exception:
            raise SystemExit(f'Port {args.port} is occupied. Try --port {args.port + 1}.')
        if args.open:
            webbrowser.open(url)
        raise SystemExit(0)
    print(f'Open {url}', flush=True)
    if args.open:
        webbrowser.open(url)
    server.serve_forever()
