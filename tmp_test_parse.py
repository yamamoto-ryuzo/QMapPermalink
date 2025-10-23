from qmap_permalink import qmap_maplibre_generator as g
cases=[
 'https://example.com/?lat=35.6895&lon=139.6917&zoom=12',
 '35.6895,139.6917,12',
 '@35.6895,139.6917,12z'
]
for c in cases:
    print(c, '->', g._parse_permalink(c))
