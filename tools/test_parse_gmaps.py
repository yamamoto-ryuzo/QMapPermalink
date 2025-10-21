#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone test for Google Maps @... parser used by QMapPermalink.
"""
import re
import urllib.parse


def parse_google_maps_at_url(url):
    parsed = urllib.parse.urlparse(url)
    path = parsed.path or ''

    m = re.search(r'@([-0-9.]+),([-0-9.]+)(?:,([^/\s]+))?', path)
    if not m:
        m = re.search(r'@([-0-9.]+),([-0-9.]+)(?:,([^/\s]+))?', url)
    if not m:
        return None

    lat = float(m.group(1))
    lon = float(m.group(2))
    rest = m.group(3) if m.lastindex and m.lastindex >= 3 else None

    zoom = None
    scale = None
    map_width_m = None

    if rest:
        m2 = re.match(r'^([0-9.]+)(m|z)?', rest)
        if m2:
            val = float(m2.group(1))
            suf = m2.group(2)
            if suf == 'z':
                zoom = float(val)
            elif suf == 'm':
                try:
                    map_width_m = float(val)
                except Exception:
                    map_width_m = None

    result = {'lat': lat, 'lon': lon, 'zoom': zoom, 'scale': scale}
    if map_width_m is not None:
        result['map_width_m'] = map_width_m
    return result


if __name__ == '__main__':
    urls = [
        'https://www.google.co.jp/maps/@35.6722008,139.6943022,10883m/data=!3m1!1e3?entry=ttu&g_ep=EgoyMDI1MTAxNC4wIKXMDSo',
        'https://www.google.co.jp/maps/@35.6723234,139.6939071,499m/data=!3m1!1e3?entry=ttu&g_ep=EgoyMDI1MTAxNC4wIKXMDSoASAFQAw%3D%3D',
        'https://www.google.co.jp/maps/@35.6723234,139.6939071,4990m/data=!3m1!1e3?entry=ttu&g_ep=EgoyMDI1MTAxNC4wIKXMDSoASAFQAw%3D%3D',
        'https://www.google.co.jp/maps/@35.6778996,139.6960404,883m/data=!3m1!1e3?entry=ttu&g_ep=EgoyMDI1MTAxNC4wIKXMDSoASAFQAw%25',
    'https://www.google.co.jp/maps/@35.8075405,139.5292591,1246m/data=!3m1!1e3?entry=ttu&g_ep=EgoyMDI1MTAxNC4wIKXMDSoASAFQAw%3D%3D',
        'https://www.google.co.jp/maps/@35.9118462,139.5876715,220m,15z',
    ]

    for u in urls:
        r = parse_google_maps_at_url(u)
        print('URL:', u)
        print('  parsed:', r)
        print()
