"""Basic WFS checks for QMapPermalink

- Fetch GetCapabilities
- Parse FeatureTypeList and print count/names
- For first FeatureType, fetch DescribeFeatureType and GetFeature (COUNT/ MAXFEATURES=1)

Usage:
    python tools\wfs_basic_checks.py --url "http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetCapabilities"
"""
import argparse
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import sys

DEFAULT = 'http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetCapabilities'

def fetch(url):
    print(f'Fetching: {url}')
    req = urllib.request.Request(url, headers={'User-Agent':'wfs-basic-check/1.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = r.read()
        ct = r.headers.get('Content-Type')
    return data, ct


def parse_capabilities(xmlbytes):
    try:
        root = ET.fromstring(xmlbytes)
    except Exception as e:
        print('ERROR: Failed to parse GetCapabilities XML:', e)
        return None
    # Find FeatureType elements (WFS 2.0 namespace)
    ns = {'wfs':'http://www.opengis.net/wfs/2.0'}
    ftypes = root.findall('.//{http://www.opengis.net/wfs/2.0}FeatureType')
    if not ftypes:
        # try generic local-name search
        ftypes = [el for el in root.findall('.//*') if el.tag.endswith('FeatureType')]
    names = []
    for ft in ftypes:
        name_el = ft.find('{http://www.opengis.net/wfs/2.0}Name')
        if name_el is None:
            # fallback: any child ending with Name
            for c in ft:
                if c.tag.endswith('Name'):
                    name_el = c; break
        names.append(name_el.text if name_el is not None else '(unknown)')
    return names


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--url', '-u', default=DEFAULT)
    args = p.parse_args()

    try:
        data, ct = fetch(args.url)
    except Exception as e:
        print('ERROR: could not fetch GetCapabilities:', e)
        sys.exit(2)

    print('Content-Type:', ct)
    names = parse_capabilities(data)
    if names is None:
        print('No FeatureTypeList found in GetCapabilities')
        sys.exit(3)

    print(f'Found {len(names)} FeatureType entries')
    for i, n in enumerate(names[:20], start=1):
        print(f'  {i}: {n}')

    if not names:
        print('No published layers (WFSLayers not set?)')
        sys.exit(0)

    first = names[0]
    # DescribeFeatureType
    q = urllib.parse.urlencode({'SERVICE':'WFS','REQUEST':'DescribeFeatureType','TYPENAME':first})
    base = args.url.split('?')[0]
    desc_url = base + '?' + q
    try:
        ddata, dct = fetch(desc_url)
        print('DescribeFeatureType OK, Content-Type:', dct)
        print(ddata.decode('utf-8')[:1000])
    except Exception as e:
        print('ERROR: DescribeFeatureType failed:', e)

    # GetFeature (MAXFEATURES=1)
    q = urllib.parse.urlencode({'SERVICE':'WFS','REQUEST':'GetFeature','TYPENAME':first,'COUNT':'1','OUTPUTFORMAT':'application/json'})
    gf_url = base + '?' + q
    try:
        gdata, gct = fetch(gf_url)
        print('GetFeature OK, Content-Type:', gct)
        # print beginning of payload
        try:
            txt = gdata.decode('utf-8')
            print(txt[:2000])
        except Exception:
            print('Binary response (not UTF-8) or decode error')
    except Exception as e:
        print('ERROR: GetFeature failed:', e)

if __name__ == '__main__':
    main()
