#!/usr/bin/env python3
"""Validate the local wmts_capabilities.xml against WMTS XSD (lxml required).
"""
import sys
from urllib.request import urlopen
from lxml import etree

XSD_URL = 'http://schemas.opengis.net/wmts/1.0/wmtsGetCapabilities_response.xsd'
XML_PATH = 'wmts_capabilities.xml'

try:
    print('Downloading XSD...')
    xsd_data = urlopen(XSD_URL).read()
    xsd_doc = etree.XML(xsd_data)
    schema = etree.XMLSchema(xsd_doc)
except Exception as e:
    print('Failed to download or parse XSD:', e)
    sys.exit(2)

try:
    print('Parsing XML...')
    doc = etree.parse(XML_PATH)
except Exception as e:
    print('Failed to parse XML:', e)
    sys.exit(2)

print('Validating...')
valid = schema.validate(doc)
if valid:
    print('VALID: wmts_capabilities.xml validates against WMTS XSD')
    sys.exit(0)
else:
    print('INVALID: errors:')
    for err in schema.error_log:
        print(err)
    sys.exit(1)
