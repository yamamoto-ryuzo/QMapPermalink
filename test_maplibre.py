#!/usr/bin/env python3
"""
Test script to open MapLibre with SLD styling
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from qmap_permalink.qmap_maplibre import open_maplibre_from_permalink

# Mock SLD XML for testing
sld_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.1.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>test_layer</Name>
    <UserStyle>
      <Title>Test Style</Title>
      <FeatureTypeStyle>
        <Rule>
          <PointSymbolizer>
            <Graphic>
              <Mark>
                <WellKnownName>circle</WellKnownName>
                <Fill>
                  <CssParameter name="fill">#FF0000</CssParameter>
                  <CssParameter name="fill-opacity">0.8</CssParameter>
                </Fill>
                <Stroke>
                  <CssParameter name="stroke">#000000</CssParameter>
                  <CssParameter name="stroke-width">1</CssParameter>
                </Stroke>
              </Mark>
              <Size>10</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>'''

# Test SLD conversion
from qmap_permalink.qmap_maplibre import sld_to_mapbox_style

layers = sld_to_mapbox_style(sld_xml, "test_source")
print(f"Converted layers: {len(layers)}")
for layer in layers:
    print(f"Layer: {layer}")

# Test opening MapLibre
if __name__ == "__main__":
    try:
        # Permalink text with coordinates and typename
        permalink_text = "http://example.com/qgis-map?lat=35.6895&lon=139.6917&zoom=10&typename=test_layer"
        wfs_typename = "test_layer"

        # Open MapLibre with SLD
        path = open_maplibre_from_permalink(permalink_text, wfs_typename)
        print(f"MapLibre opened at: {path}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()