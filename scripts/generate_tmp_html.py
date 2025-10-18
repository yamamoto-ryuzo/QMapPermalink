import os
import sys
# ensure project root is on sys.path so imports like `qmap_permalink` work when running this script
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from qmap_permalink.qmap_webmap_generator import QMapWebMapGenerator

try:
    g = QMapWebMapGenerator()
    nav = {'x': -21550.369052, 'y': -10063.519083, 'scale': 502.6, 'rotation': 0}
    html = g.generate_wms_based_html_page(nav, server_port=8089)
    out = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tmp_qmap_test.html'))
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(html)
    print('WROTE', out, 'len', len(html))
except Exception as e:
    import traceback
    traceback.print_exc()
    print('ERROR:', e)
