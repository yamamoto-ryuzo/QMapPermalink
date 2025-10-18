"""Simple CORS proxy that forwards requests to backend WMS and adds CORS headers.
Usage: python scripts/cors_proxy.py [listen_port] [backend_url]
Default: listen_port=8088 backend_url=http://127.0.0.1:8089
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, urlunparse
import urllib.request
import sys

LISTEN_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8088
BACKEND = sys.argv[2] if len(sys.argv) > 2 else 'http://127.0.0.1:8089'

class ProxyHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        # construct backend URL
        target = BACKEND + self.path
        try:
            with urllib.request.urlopen(target) as resp:
                status = resp.getcode()
                data = resp.read()
                self.send_response(status)
                # copy a few headers
                ctype = resp.headers.get('Content-Type')
                if ctype:
                    self.send_header('Content-Type', ctype)
                clen = resp.headers.get('Content-Length')
                if clen:
                    self.send_header('Content-Length', clen)
                # add CORS headers
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            # forward error status and body
            try:
                body = e.read()
            except Exception:
                body = b''
            self.send_response(e.code)
            self.send_header('Content-Type', e.headers.get('Content-Type','text/plain'))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

if __name__ == '__main__':
    print(f"Starting CORS proxy on http://127.0.0.1:{LISTEN_PORT}/ -> {BACKEND}")
    server = HTTPServer(('127.0.0.1', LISTEN_PORT), ProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Stopping')
        server.server_close()
