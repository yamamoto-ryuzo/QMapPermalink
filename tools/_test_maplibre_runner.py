import sys
import os
# ensure repository root is on sys.path so package imports work when running
# this script from the tools/ folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from qmap_permalink.qmap_maplibre import _parse_permalink, open_maplibre_from_permalink

permalink = "http://localhost:8089/qgis-map?x=139.596021&y=35.906887&scale=1598.9&crs=EPSG:4326&rotation=115.00"
print("permalink:", permalink)
print("_parse_permalink ->", _parse_permalink(permalink))
path = None
try:
    path = open_maplibre_from_permalink(permalink)
    print("open_maplibre_from_permalink returned:", path)
except Exception as e:
    print("open_maplibre_from_permalink raised:", repr(e))
    sys.exit(2)
