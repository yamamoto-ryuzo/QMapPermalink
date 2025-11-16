#!/usr/bin/env python3
"""Validate a WMTS GetCapabilities document against the WMTS 1.0.0 XSD.

Usage:
  python tools/validate_wmts_capabilities.py [--url URL]

Default URL: http://localhost:8089/wmts?SERVICE=WMTS&REQUEST=GetCapabilities

Behavior:
- Try to use lxml (recommended). If available, download the WMTS XSD and validate.
- If lxml not available, print an `xmllint` command you can run in PowerShell / shell.
"""

from __future__ import print_function
import argparse
import sys
import urllib.request
import tempfile
import os

DEFAULT_URL = 'http://localhost:8089/wmts?SERVICE=WMTS&REQUEST=GetCapabilities'
WMTS_XSD_URL = 'http://schemas.opengis.net/wmts/1.0/wmtsGetCapabilities_response.xsd'


def download_to_temp(url, prefix='wmts_', suffix=''):
    try:
        resp = urllib.request.urlopen(url)
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None
    data = resp.read()
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    with os.fdopen(fd, 'wb') as fh:
        fh.write(data)
    return path


def validate_with_lxml(capabilities_path):
    try:
        from lxml import etree as ET
    except Exception as e:
        print('lxml not available:', e)
        return False, 'lxml not installed'

    print('Downloading WMTS XSD...')
    xsd_path = download_to_temp(WMTS_XSD_URL, prefix='wmts_xsd_', suffix='.xsd')
    if not xsd_path:
        return False, f'Failed to download {WMTS_XSD_URL}'

    try:
        xsd_doc = ET.parse(xsd_path)
        schema = ET.XMLSchema(xsd_doc)
    except Exception as e:
        return False, f'Failed to parse XSD: {e}'

    try:
        doc = ET.parse(capabilities_path)
    except Exception as e:
        return False, f'Failed to parse capabilities XML: {e}'

    valid = schema.validate(doc)
    if valid:
        return True, 'Document is valid against WMTS XSD'
    else:
        log = schema.error_log
        return False, str(log)


def main():
    p = argparse.ArgumentParser(description='Validate WMTS GetCapabilities against WMTS 1.0.0 XSD')
    p.add_argument('--url', '-u', default=DEFAULT_URL, help='GetCapabilities URL')
    args = p.parse_args()

    url = args.url
    print(f'Fetching GetCapabilities from: {url}')
    cap_path = download_to_temp(url, prefix='wmts_cap_', suffix='.xml')
    if not cap_path:
        print('Failed to download capabilities document')
        sys.exit(2)

    print('Saved capabilities to:', cap_path)

    ok, msg = validate_with_lxml(cap_path)
    if ok:
        print('\nVALID: ', msg)
        sys.exit(0)
    else:
        print('\nLXML validation not available or failed:', msg)
        print('\nIf you have xmllint installed, you can validate manually with:')
        print(f'  xmllint --noout --schema {WMTS_XSD_URL} {cap_path}')
        print('\nOr use a web-based XML validator that accepts external schema imports.')
        sys.exit(1)


if __name__ == "__main__":
    main()
