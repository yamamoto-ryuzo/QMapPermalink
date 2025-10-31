import json, requests
from qmap_permalink.qmap_maplibre import sld_to_mapbox_style

typename = '橋脚旗揚げ'
_wfs_typename = requests.utils.requote_uri(typename)
_wfs_source_id = 'wfs_test'

sld_url = f"http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetStyles&TYPENAME={_wfs_typename}"
resp = requests.get(sld_url, timeout=5)
if resp.status_code == 200:
    sld_xml = resp.text
    mapbox_layers = sld_to_mapbox_style(sld_xml, _wfs_source_id)
    style_dict = {
        "version": 8,
        "name": typename,
        "glyphs": "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        "sources": {
            "qmap": {"type":"raster","tiles":["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],"tileSize":256},
            _wfs_source_id: {"type":"geojson","data": f"http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetFeature&TYPENAMES={_wfs_typename}&OUTPUTFORMAT=application/json&MAXFEATURES=1000"}
        },
        "layers": [ {"id": "qmap", "type": "raster", "source": "qmap"} ] + mapbox_layers
    }
    print(json.dumps(style_dict, ensure_ascii=False, indent=2))
else:
    print('Failed to fetch SLD', resp.status_code)
