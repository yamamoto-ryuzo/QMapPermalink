import zipfile, os
p='c:/github/QMapPermalink/dist'
if not os.path.isdir(p):
    print('dist folder not found:',p)
else:
    zips=[os.path.join(p,f) for f in os.listdir(p) if f.lower().endswith('.zip')]
    if not zips:
        print('no zip files in',p)
    for zf in sorted(zips):
        st=os.path.getsize(zf)
        print('\nZIP:',zf)
        print('Size:',st,'bytes')
        try:
            z=zipfile.ZipFile(zf)
            candidates=['qmap_permalink/metadata.txt','metadata.txt']
            found=False
            for c in candidates:
                if c in z.namelist():
                    data=z.read(c).decode('utf-8',errors='replace')
                    print('Found',c)
                    has_camel = any(k in data for k in ['qgisMinimumVersion','qgisMaximumVersion','requiredQtVersion','hasProcessingProvider'])
                    has_lower = any(k in data for k in ['qgisminimumversion','qgismaximumversion','requiredqtversion','hasprocessingprovider'])
                    print('Contains camelCase keys:',has_camel)
                    print('Contains lowercase keys:',has_lower)
                    print('--- metadata excerpt ---')
                    print('\n'.join(data.splitlines()[:30]))
                    found=True
                    break
            if not found:
                print('metadata.txt not found inside zip')
        except Exception as e:
            print('Error reading zip:',e)
