from qmap_permalink.qmap_maplibre import open_maplibre_from_permalink

permalink = 'http://example.com/qgis-map?lat=35.91359129966556&lon=139.59319360933935&zoom=16.71&typename=%E6%A9%8B%E8%84%9A%E6%97%97%E6%8F%9A%E3%81%92'

path = open_maplibre_from_permalink(permalink)
print('HTML path:', path)
