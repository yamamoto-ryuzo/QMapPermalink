from qmap_permalink import qmap_maplibre_generator as g

# Example with x/y/crs in query for EPSG:3857 (WebMercator center for Tokyo approx)
permalink = 'http://localhost:8089/qgis-map?x=15550418.0&y=4256678.0&crs=EPSG:3857&zoom=12'
print('Input permalink:', permalink)
path = g.open_maplibre_from_permalink(permalink)
print('Returned path:', path)
try:
	with open(path, 'r', encoding='utf-8') as fh:
		data = fh.read()
		# print a small excerpt around center/initialization for inspection
		idx = data.find('Initializing map at')
		if idx != -1:
			print(data[idx:idx+200])
		else:
			# fallback: print first 400 chars
			print(data[:400])
except Exception as e:
	print('Could not read generated HTML:', e)
