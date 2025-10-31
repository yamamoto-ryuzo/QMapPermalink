from qmap_permalink.qmap_maplibre import open_maplibre_from_permalink

permalink = 'http://localhost:8089/qgis-map?x=-21673.330850&y=-9560.153850&scale=3738.5&crs=EPSG:6677&rotation=95.00'
typename = '橋脚旗揚げ'

path = open_maplibre_from_permalink(permalink, wfs_typename=typename)
print('HTML path:', path)
