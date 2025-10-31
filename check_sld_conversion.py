import requests
from qmap_permalink.qmap_maplibre import sld_to_mapbox_style

typename = '橋脚旗揚げ'
url = f"http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetStyles&TYPENAME={requests.utils.requote_uri(typename)}"
print('Fetching SLD from', url)
r = requests.get(url, timeout=5)
print('Status', r.status_code)
print(r.text[:400])

layers = sld_to_mapbox_style(r.text, source_id='test_source')
print('Converted layers:', len(layers))
for l in layers:
    print(l)
