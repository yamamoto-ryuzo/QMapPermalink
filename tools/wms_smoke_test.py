"""Simple WMS smoke test helper for geo_webview

Usage examples:
  python tools/wms_smoke_test.py --host localhost --port 8089 --outdir .\tmp

Requires: requests (pip install requests)

The script performs:
- GET /wms?SERVICE=WMS&REQUEST=GetCapabilities
- GET /wms?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&CRS=EPSG:4326&BBOX=35.5,139.5,35.9,139.9&WIDTH=400&HEIGHT=300&FORMAT=image/png
  (basic example — adjust BBOX/CRS to your project)

It saves the GetMap image to disk and prints basic validation results.
"""
from __future__ import annotations
import argparse
import os
import sys

try:
    import requests
except Exception:
    print("ERROR: missing dependency 'requests'. Install with: python -m pip install requests")
    sys.exit(2)


def fetch_get_capabilities(base_url: str) -> tuple[int, str]:
    url = f"{base_url}/wms"
    params = {"SERVICE": "WMS", "REQUEST": "GetCapabilities"}
    r = requests.get(url, params=params, timeout=10)
    return r.status_code, r.text[:2000]


def fetch_get_map(base_url: str, out_path: str, params: dict) -> int:
    url = f"{base_url}/wms"
    r = requests.get(url, params=params, timeout=30)
    if r.status_code == 200:
        # save as binary
        with open(out_path, "wb") as fh:
            fh.write(r.content)
    return r.status_code


def main():
    p = argparse.ArgumentParser(description="WMS smoke test for geo_webview")
    p.add_argument("--host", default="localhost", help="server host")
    p.add_argument("--port", default=8089, type=int, help="server port")
    p.add_argument("--outdir", default=".", help="output directory for test image")
    p.add_argument("--bbox", default="35.5,139.5,35.9,139.9", help="BBOX (miny,minx,maxy,maxx or minx,miny,maxx,maxy depending on CRS) — default is a small area around Tokyo (lat/lon)")
    args = p.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    print(f"Testing WMS endpoints at {base_url}")

    print("\n[1] GetCapabilities")
    code, snippet = fetch_get_capabilities(base_url)
    print(f"Status: {code}")
    if code == 200 and ("WMS_Capabilities" in snippet or "Service" in snippet):
        print("GetCapabilities looks OK (basic check)")
    else:
        print("GetCapabilities may be invalid or unreachable — preview:")
        print(snippet)

    print("\n[2] GetMap (sample)")
    # Use WMS 1.3.0 + CRS=EPSG:4326 example (axis order for 4326 is lat,lon in 1.3.0)
    params = {
        "SERVICE": "WMS",
        "REQUEST": "GetMap",
        "VERSION": "1.3.0",
        "CRS": "EPSG:4326",
        # axis-order for EPSG:4326 in WMS 1.3.0 is (lat,lon), but the server handles swapping. Use a small bbox.
        "BBOX": args.bbox,
        "WIDTH": "400",
        "HEIGHT": "300",
        "FORMAT": "image/png",
        "ANGLE": "0"
    }

    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)
    out_path = os.path.join(outdir, "wms_getmap_test.png")

    code = fetch_get_map(base_url, out_path, params)
    print(f"Status: {code}")
    if code == 200 and os.path.exists(out_path):
        print(f"Saved GetMap output to: {out_path}")
        print("You can open it with your image viewer to inspect the rendered map.")
    else:
        print("GetMap failed. HTTP status:", code)
        print("Response headers (if any) may indicate error details. Check QGIS Message Log for plugin traces.")


if __name__ == '__main__':
    main()
