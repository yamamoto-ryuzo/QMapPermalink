"""Simple test harness for Google Maps @-format parser in the plugin.

Run from repo root with: python tools/parse_gmaps.py
"""
import sys
sys.path.insert(0, '.')
from qmap_permalink.qmap_permalink import QMapPermalink

class DummyIface:
    def mapCanvas(self):
        return None

p = QMapPermalink(DummyIface())

samples = [
    'https://www.google.co.jp/maps/@35.9118462,139.5876715,220m/data=!3m1!1e3',
    'https://www.google.com/maps/@35.9118462,139.5876715,16z',
    'https://maps.google.com/?q=35.9118462,139.5876715',
    'https://www.google.com/maps/place/35.9118462,139.5876715'
]

for s in samples:
    parsed = p._parse_google_maps_at_url(s)
    print(s)
    print('  ->', parsed)
