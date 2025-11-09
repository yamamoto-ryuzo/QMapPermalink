import sys
import types
import urllib.parse

# Ensure project root is importable
sys.path.insert(0, r"c:\github\QMapPermalink")

# Create a fake qgis.core module to satisfy imports
qgis_core = types.SimpleNamespace()

class DummyQgsMessageLog:
    @staticmethod
    def logMessage(msg, tag=None, level=None):
        print(f"QGSLOG:{tag}:{level}:{msg}")

class DummyQgis:
    Critical = 3

qgis_core.QgsMessageLog = DummyQgsMessageLog
qgis_core.Qgis = DummyQgis

fake_qgis = types.ModuleType('qgis')
fake_qgis.core = qgis_core
sys.modules['qgis'] = fake_qgis
sys.modules['qgis.core'] = qgis_core

# Now import the module under test
from qmap_permalink.qmap_wmts_service import QMapPermalinkWMTSService
from qmap_permalink import http_server

# Fake connection that captures sendall
class FakeConn:
    def __init__(self):
        self.data = b''
    def sendall(self, b):
        # print small marker to stdout for testing
        print('---SENDALL START---')
        try:
            print(b.decode('utf-8', errors='ignore'))
        except Exception:
            print(repr(b[:200]))
        print('---SENDALL END---')
    def close(self):
        print('conn closed')

# Fake server_manager
class FakeServerManager:
    def __init__(self):
        self.http_server = None
        self.server_port = 12345
    def _handle_wms_get_map_with_bbox(self, conn, bbox, srs, w, h, rotation=0.0):
        print(f"render called: bbox={bbox} srs={srs} size={w}x{h} rot={rotation}")
        # simulate returning a PNG by using http_server.send_binary_response
        png = b'PNGDATA'
        http_server.send_binary_response(conn, 200, 'OK', png, 'image/png')

sm = FakeServerManager()
service = QMapPermalinkWMTSService(sm)
conn = FakeConn()

print('\n=== Test: GetCapabilities via SERVICE=WMTS ===')
parsed = urllib.parse.urlparse('http://localhost/wmts')
params = {'SERVICE': ['WMTS']}
service.handle_wmts_request(conn, parsed, params, host='localhost:12345')

print('\n=== Test: Tile path without TMS ===')
parsed = urllib.parse.urlparse('http://localhost/wmts/3/2/1.png')
params = {}
service.handle_wmts_request(conn, parsed, params, host='localhost:12345')

print('\n=== Test: Tile path with TMS (tms=1) ===')
parsed = urllib.parse.urlparse('http://localhost/wmts/3/2/1.png')
params = {'tms': ['1']}
service.handle_wmts_request(conn, parsed, params, host='localhost:12345')

print('\n=== Test: KVP GetTile with TMS ===')
parsed = urllib.parse.urlparse('http://localhost/wmts')
params = {'REQUEST': ['GetTile'], 'TILEMATRIX': ['3'], 'TILECOL': ['2'], 'TILEROW': ['1'], 'tms': ['1']}
service.handle_wmts_request(conn, parsed, params, host='localhost:12345')
