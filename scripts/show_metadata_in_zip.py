import zipfile
p='c:/github/QMapPermalink/dist/qmap_permalink_1.1.8.zip'
with zipfile.ZipFile(p) as z:
    data=z.read('qmap_permalink/metadata.txt').decode('utf-8')
    print(data)
    print('\ncontains qgisMinimumVersion?', 'qgisMinimumVersion' in data)
