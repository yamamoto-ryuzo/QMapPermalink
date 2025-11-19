#!/usr/bin/env python3
"""WMS STYLES smoke test

Usage:
  python tools/wms_styles_test.py --host http://localhost:8089/wms --layers layerA,layerB --styles styleA,

This script issues a WMS GetMap with LAYERS and STYLES and saves the returned PNG.
"""
from __future__ import annotations

import argparse
import os
import sys
from urllib.parse import urlencode

try:
    import requests
except Exception as e:
    print("requests is required. Install via: python -m pip install requests", file=sys.stderr)
    raise


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='http://localhost:8089/wms', help='WMS endpoint base URL (default: http://localhost:8089/wms)')
    p.add_argument('--layers', default='', help='Comma-separated LAYERS parameter')
    p.add_argument('--styles', default='', help='Comma-separated STYLES parameter')
    p.add_argument('--bbox', default='-180,-90,180,90', help='BBOX (default: world in EPSG:4326)')
    p.add_argument('--crs', default='EPSG:4326', help='CRS/SRS (default: EPSG:4326)')
    p.add_argument('--width', type=int, default=800, help='Output width')
    p.add_argument('--height', type=int, default=600, help='Output height')
    p.add_argument('--out', default=os.path.join('tmp', 'getmap_styles_test.png'), help='Output file path')
    args = p.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    params = {
        'SERVICE': 'WMS',
        'REQUEST': 'GetMap',
        'VERSION': '1.3.0',
        'CRS': args.crs,
        'BBOX': args.bbox,
        'WIDTH': str(args.width),
        'HEIGHT': str(args.height),
        'FORMAT': 'image/png',
    }
    if args.layers:
        params['LAYERS'] = args.layers
    if args.styles is not None:
        # STYLES may be empty string to indicate default styles for each layer
        params['STYLES'] = args.styles

    url = args.host
    qs = urlencode(params)
    full = url + ('?' if '?' not in url else '&') + qs

    print(f"Requesting: {full}")

    try:
        resp = requests.get(full, timeout=30)
    except Exception as e:
        print(f"HTTP request failed: {e}")
        sys.exit(2)

    print(f"HTTP {resp.status_code} {resp.reason}")

    if resp.status_code == 200:
        # Try to detect binary image
        content_type = resp.headers.get('Content-Type', '')
        print(f"Content-Type: {content_type}")
        try:
            with open(args.out, 'wb') as f:
                f.write(resp.content)
            print(f"Saved output to: {args.out}")
            sys.exit(0)
        except Exception as e:
            print(f"Failed to write output: {e}")
            sys.exit(3)
    else:
        # Print a snippet of the body for debugging
        body = resp.text[:1000]
        print("Response body (truncated):")
        print(body)
        sys.exit(1)


if __name__ == '__main__':
    main()
