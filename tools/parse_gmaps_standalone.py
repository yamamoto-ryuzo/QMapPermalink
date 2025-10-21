"""Standalone parser test that imports only the parsing function by copying logic.

Run: python tools/parse_gmaps_standalone.py
"""
import urllib.parse
import re
import math

# We'll copy the helper functions from the plugin but keep them independent

def _zoom_to_earth_distance(zoom_level):
    if zoom_level is None:
        return 5000
    try:
        z = float(zoom_level)
        zoom_distances = {
            0: 20000000, 1: 10000000, 2: 5000000, 3: 2000000, 4: 1000000,
            5: 500000, 6: 200000, 7: 100000, 8: 50000, 9: 20000,
            10: 10000, 11: 5000, 12: 2000, 13: 1000, 14: 500,
            15: 200, 16: 100, 17: 50, 18: 20, 19: 10, 20: 5
        }
        rounded_zoom = max(0, min(20, round(z)))
        return zoom_distances.get(rounded_zoom, 5000)
    except Exception:
        return 5000


def _estimate_scale_from_zoom(zoom_level):
    if zoom_level is None:
        return 20000.0
    try:
        z = float(zoom_level)
        scale_table = {
            0: 400_000_000.0, 1: 200_000_000.0, 2: 100_000_000.0, 3: 60_000_000.0, 4: 30_000_000.0,
            5: 15_000_000.0, 6: 8_000_000.0, 7: 4_000_000.0, 8: 2_000_000.0, 9: 1_000_000.0,
            10: 600_000.0, 11: 300_000.0, 12: 150_000.0, 13: 75_000.0, 14: 40_000.0,
            15: 20_000.0, 16: 10_000.0, 17: 5_000.0, 18: 2_500.0, 19: 1_250.0,
            20: 600.0, 21: 300.0, 22: 150.0, 23: 75.0,
        }
        for zoom in range(24, 31):
            scale_table[zoom] = scale_table[23] / (2 ** (zoom - 23))
        z = max(0.0, min(30.0, z))
        if z == int(z) and int(z) in scale_table:
            return scale_table[int(z)]
        z_floor = int(math.floor(z))
        z_ceil = int(math.ceil(z))
        if z_floor < 0:
            z_floor = 0
        if z_ceil > 30:
            z_ceil = 30
        if z_floor not in scale_table:
            z_floor = max([k for k in scale_table.keys() if k <= z_floor], default=0)
        if z_ceil not in scale_table:
            z_ceil = min([k for k in scale_table.keys() if k >= z_ceil], default=30)
        if z_floor == z_ceil:
            return scale_table.get(z_floor, 20000.0)
        s1, s2 = scale_table[z_floor], scale_table[z_ceil]
        log_s1, log_s2 = math.log(s1), math.log(s2)
        t = (z - z_floor) / (z_ceil - z_floor) if z_ceil != z_floor else 0.0
        interpolated_log_scale = log_s1 + t * (log_s2 - log_s1)
        return math.exp(interpolated_log_scale)
    except Exception:
        return 20000.0


def _parse_google_maps_at_url(url):
    try:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path or ''
        m = re.search(r'@([-0-9.]+),([-0-9.]+),([^/]+)', path)
        if not m:
            m = re.search(r'@([-0-9.]+),([-0-9.]+),([^/\s]+)', url)
        if not m:
            return None
        lat = float(m.group(1))
        lon = float(m.group(2))
        rest = m.group(3)
        zoom = None
        scale = None
        m2 = re.match(r'^([0-9.]+)(m|z)?', rest)
        if m2:
            val = float(m2.group(1))
            suf = m2.group(2)
            if suf == 'z':
                zoom = float(val)
                scale = _estimate_scale_from_zoom(zoom)
            elif suf == 'm':
                best_z = None
                best_diff = float('inf')
                for zt in [i / 10.0 for i in range(0, 301)]:
                    d = _zoom_to_earth_distance(zt)
                    diff = abs(d - val)
                    if diff < best_diff:
                        best_diff = diff
                        best_z = zt
                zoom = best_z
                scale = _estimate_scale_from_zoom(zoom)
        return {'lat': lat, 'lon': lon, 'zoom': zoom, 'scale': scale}
    except Exception:
        return None


if __name__ == '__main__':
    samples = [
        'https://www.google.co.jp/maps/@35.9118462,139.5876715,220m/data=!3m1!1e3',
        'https://www.google.com/maps/@35.9118462,139.5876715,16z',
        'https://maps.google.com/?q=35.9118462,139.5876715',
        'https://www.google.com/maps/place/35.9118462,139.5876715'
    ]
    for s in samples:
        print(s)
        print(' ->', _parse_google_maps_at_url(s))
