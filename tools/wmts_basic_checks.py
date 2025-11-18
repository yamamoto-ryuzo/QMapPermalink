#!/usr/bin/env python3
"""Basic checks for WMTS capabilities (well-formedness and common compatibility issues)."""
import sys
import xml.etree.ElementTree as ET

XML_PATH = 'wmts_capabilities.xml'

def find_ns(tag):
    # return namespace and localname
    if tag[0] == '{':
        uri, local = tag[1:].split('}', 1)
        return uri, local
    return None, tag

try:
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
except Exception as e:
    print('ERROR: failed to parse XML:', e)
    sys.exit(2)

print('OK: parsed XML')

# find Contents element
contents = None
for child in root:
    uri, local = find_ns(child.tag)
    if local == 'Contents':
        contents = child
        break

if contents is None:
    print('WARN: <Contents> element not found')
    sys.exit(1)

# find Layer elements
layers = [c for c in contents if find_ns(c.tag)[1] == 'Layer']
print(f'Found {len(layers)} <Layer> entries under <Contents>')

# check ResourceURL templates and token order
import re
bad_templates = []
ok_templates = []
for lyr in layers:
    for elem in lyr:
        if find_ns(elem.tag)[1] == 'ResourceURL' or elem.tag.endswith('ResourceURL'):
            template = elem.attrib.get('template')
            if not template:
                bad_templates.append(('missing', ET.tostring(elem, encoding='unicode')))
                continue
            # look for TileMatrix, TileRow, TileCol tokens
            has_tm = '{TileMatrix}' in template
            has_tr = '{TileRow}' in template
            has_tc = '{TileCol}' in template
            order_ok = None
            if has_tm and has_tr and has_tc:
                # determine order
                idx_tm = template.find('{TileMatrix}')
                idx_tr = template.find('{TileRow}')
                idx_tc = template.find('{TileCol}')
                order = [idx_tm, idx_tr, idx_tc]
                order_ok = order == sorted(order)
            else:
                order_ok = False
            if not order_ok:
                bad_templates.append((template, 'tokens missing or wrong order'))
            else:
                ok_templates.append(template)

print(f'Good ResourceURL templates: {len(ok_templates)}')
print(f'Bad ResourceURL templates: {len(bad_templates)}')
for t in bad_templates[:5]:
    print(' -', t)

# check for new-style template presence
new_style_present = False
for lyr in layers:
    for elem in lyr:
        if find_ns(elem.tag)[1] == 'ResourceURL' or elem.tag.endswith('ResourceURL'):
            template = elem.attrib.get('template','')
            if '{Style}' in template and '{TileMatrixSet}' in template and '{TileRow}' in template and '{TileCol}' in template and '{Format}' in template:
                new_style_present = True

print('New-style {Style}/{TileMatrixSet}/{TileMatrix}/{TileRow}/{TileCol}.{Format} present:', new_style_present)

sys.exit(0)
