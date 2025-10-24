"""Standalone MapLibre endpoint server

Run this script from the repository root (or from tools/) to start a
minimal HTTP server that serves an interactive MapLibre page at
http://localhost:8089/maplibre

The server accepts optional query parameters: lat, lon, zoom or a
"permalink" query string which will be parsed by the generator.
"""
import os
import sys
import socket
import threading
import urllib.parse

# Ensure package import works when run from tools/ or repo root
HERE = os.path.dirname(__file__)
REPO_ROOT = os.path.dirname(HERE)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from qmap_permalink import maplibre_endpoint
from qmap_permalink import http_server


HOST = '0.0.0.0'
PORT = 8089


def handle_client(conn, addr):
    with conn:
        request_bytes = http_server.read_http_request(conn)
        if not request_bytes:
            return
        try:
            request_text = request_bytes.decode('iso-8859-1', errors='replace')
            request_line = request_text.splitlines()[0]
        except Exception:
            http_server.send_http_response(conn, 400, 'Bad Request', 'Invalid HTTP request')
            return

        parts = request_line.split()
        if len(parts) < 3:
            http_server.send_http_response(conn, 400, 'Bad Request', 'Malformed HTTP request line')
            return

        method, target, _ = parts
        if method.upper() != 'GET':
            http_server.send_http_response(conn, 405, 'Method Not Allowed', 'Only GET supported')
            return

        parsed = urllib.parse.urlparse(target)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == '/maplibre':
            # Accept either explicit lat/lon/zoom or a permalink string
            lat = qs.get('lat', [None])[0]
            lon = qs.get('lon', [None])[0]
            zoom = qs.get('zoom', [None])[0]
            permalink = qs.get('permalink', [None])[0]
            try:
                if permalink:
                    html = maplibre_endpoint.generate_maplibre_html(permalink_text=permalink)
                else:
                    html = maplibre_endpoint.generate_maplibre_html(lat=lat, lon=lon, zoom=zoom)
                http_server.send_http_response(conn, 200, 'OK', html, 'text/html; charset=utf-8')
            except Exception as e:
                http_server.send_http_response(conn, 500, 'Internal Server Error', f'Error generating MapLibre page: {e}')
            return

        # not found
        http_server.send_http_response(conn, 404, 'Not Found', 'Available endpoints: /maplibre')


def run_server(host=HOST, port=PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(5)
    print(f"MapLibre server listening on http://{host}:{port}/maplibre")
    try:
        while True:
            conn, addr = sock.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print('\nShutting down server')
    finally:
        try:
            sock.close()
        except Exception:
            pass


if __name__ == '__main__':
    run_server()
