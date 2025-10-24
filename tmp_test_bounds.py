from qmap_permalink import qmap_maplibre as g

# bbox example in EPSG:3857 roughly covering central Tokyo area
permalink = 'http://localhost:8089/qgis-map?x_min=15550000&y_min=4256000&x_max=15551000&y_max=4257000&crs=EPSG:3857'
print('Input permalink:', permalink)
path = g.open_maplibre_from_permalink(permalink)
print('Returned path:', path)
try:
    with open(path, 'r', encoding='utf-8') as fh:
        data = fh.read()
        idx = data.find('map.fitBounds')
        if idx != -1:
            print(data[idx:idx+200])
        else:
            print('fitBounds not found in generated HTML')
except Exception as e:
    print('Could not read generated HTML:', e)
