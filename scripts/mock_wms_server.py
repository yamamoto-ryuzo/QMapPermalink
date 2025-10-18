"""Simple mock WMS server to respond to /wms requests for local testing.
Serves a tiny 256x256 PNG and returns CORS headers.
Run with: python scripts\mock_wms_server.py
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

PORT = 8089

# A minimal 16x16 PNG (checker) bytes to avoid external deps
SAMPLE_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\x00\x00\x19tEXtSoftware\x00mock_wms\x00http://example.com\x92\xe6\x9b\x9a\x00\x00\x00\x0cIDATx\x9cc`\x18\x05\xa3\x60\x14\x8c\x81\x81\x81\x01\x00\x04\x00\x01\xe2\x02\xa5\x00\x00\x00\x00IEND\xaeB`\x82'
)


class MockWMSHandler(BaseHTTPRequestHandler):
    def _set_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != '/wms':
            self.send_response(404)
            self._set_cors()
            self.end_headers()
            return
        data = SAMPLE_PNG
        self.send_response(200)
        self._set_cors()
        self.send_header('Content-type', 'image/png')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), MockWMSHandler)
    print(f"Mock WMS server listening on http://127.0.0.1:{PORT}/wms")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Stopping')
        server.server_close()
