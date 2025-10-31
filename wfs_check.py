#!/usr/bin/env python3
import requests, xml.etree.ElementTree as ET, json, sys

BASE = 'http://localhost:8089'

try:
    print('Fetching WFS GetCapabilities...')
    r = requests.get(BASE + '/wfs?SERVICE=WFS&REQUEST=GetCapabilities', timeout=5)
    r.raise_for_status()
    xml = r.text
    root = ET.fromstring(xml)
    # find FeatureType/Name
    names = []
    for ft in root.findall('.//{http://www.opengis.net/wfs/2.0}FeatureType'):
        nm = ft.find('{http://www.opengis.net/wfs/2.0}Name')
        if nm is not None and nm.text:
            names.append(nm.text)
    # fallback: try no-namespace tags
    if not names:
        for ft in root.findall('.//FeatureType'):
            nm = ft.find('Name')
            if nm is not None and nm.text:
                names.append(nm.text)

    if not names:
        print('No FeatureType names found in GetCapabilities')
        sys.exit(2)

    typename = names[0]
    print('Using typename:', typename)

    gf_url = f"{BASE}/wfs?SERVICE=WFS&REQUEST=GetFeature&TYPENAMES={requests.utils.requote_uri(typename)}&OUTPUTFORMAT=application/json&MAXFEATURES=10"
    print('Fetching GetFeature:', gf_url)
    r2 = requests.get(gf_url, timeout=10)
    r2.raise_for_status()
    data = r2.json()

    feats = data.get('features', [])
    print('Number of features returned:', len(feats))
    if not feats:
        print('No features to inspect')
        sys.exit(0)

    count_with_style = 0
    for i, f in enumerate(feats[:10]):
        props = f.get('properties') or {}
        has = '_qgis_style' in props
        print(f'Feature[{i}] properties keys:', list(props.keys())[:20])
        print(f'Feature[{i}] has _qgis_style:', has)
        if has:
            count_with_style += 1
            print('  _qgis_style:', json.dumps(props.get('_qgis_style'), ensure_ascii=False))
    print(f'Features with _qgis_style: {count_with_style}/{len(feats)}')

    # exit 0 success
    sys.exit(0)
except Exception as e:
    print('Error while checking WFS:', e)
    import traceback
    traceback.print_exc()
    sys.exit(3)
