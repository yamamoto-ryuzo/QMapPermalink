# geo_webview — Turn QGIS into a lightweight OGC server

[日本語版はこちら / Japanese: `README_JP.md`](README_JP.md)

> Part of the `geo_suite` project — a lightweight QGIS plugin that exposes a QGIS project as WMS/WMTS/WFS services for client apps and quick sharing.

Table of contents
- [geo\_webview — Turn QGIS into a lightweight OGC server](#geo_webview--turn-qgis-into-a-lightweight-ogc-server)
  - [Overview](#overview)
  - [Integration with geo\_suite](#integration-with-geo_suite)
  - [System requirements](#system-requirements)
  - [Main features](#main-features)
    - [OGC services (WMS / WMTS / WFS)](#ogc-services-wms--wmts--wfs)
      - [WMS](#wms)
      - [WMTS](#wmts)
      - [WFS 2.0](#wfs-20)
    - [Performance optimizations](#performance-optimizations)
    - [Network features (v3.5.0)](#network-features-v350)
  - [Client integrations](#client-integrations)
    - [OpenLayers](#openlayers)
    - [MapLibre GL](#maplibre-gl)
    - [Google Maps / Google Earth](#google-maps--google-earth)
  - [Permalinks](#permalinks)
  - [Quick start](#quick-start)
    - [1) Install](#1-install)
    - [2) Basic usage](#2-basic-usage)
    - [3) Example OGC requests](#3-example-ogc-requests)
  - [Common use cases](#common-use-cases)
    - [Field data collection](#field-data-collection)
    - [Internal map portal](#internal-map-portal)
    - [Emergency map server](#emergency-map-server)
    - [Distributable project package](#distributable-project-package)
  - [WFS details](#wfs-details)
  - [MapLibre integration](#maplibre-integration)
    - [Style conversion](#style-conversion)
  - [Office integration](#office-integration)
    - [Excel](#excel)
    - [PowerPoint](#powerpoint)
  - [Development \& customization](#development--customization)
  - [Security notes](#security-notes)
  - [Roadmap \& changelog](#roadmap--changelog)
  - [License](#license)
  - [Disclaimer](#disclaimer)

## Overview

`geo_webview` instantly converts QGIS into an OGC-compliant map server. No complex server setup is required: open a QGIS project and the plugin provides WMS, WMTS and WFS services.

Use cases include:
- Sharing internal map data on a LAN
- Delivering data to mobile field apps
- Quickly standing up an emergency map server
- Packaging a QGIS project as a distributable map service

![Panel screenshot](images/image01.png)

## Integration with geo_suite

`geo_webview` is developed as part of the `geo_suite` project.

How they work together:
- `geo_webview`: run QGIS as an OGC server (this plugin)
- `geo_suite`: client applications for viewing and editing
- Scenario: QGIS + `geo_webview` serve data; `geo_suite` clients consume it

## System requirements
- QGIS 3.x (Qt5/Qt6 compatible)
- Windows / macOS / Linux
- Python 3.7+
- Network: local network or localhost

## Main features

### OGC services (WMS / WMTS / WFS)

#### WMS
- Serve a QGIS project as WMS
- Support for `GetCapabilities`, `GetMap`, `GetFeatureInfo`
- SLD / custom style support
- High-resolution image output (clamped by default, e.g. 4096 px)

#### WMTS
- Tile-based fast map delivery
- XYZ tile interface
- Cache support (planned / optional)

#### WFS 2.0
- Serve vector data as GeoJSON/GML
- `GetCapabilities`, `GetFeature`, `DescribeFeatureType` supported
- `GetStyles` (SLD) support
- High-performance caching: subsequent requests are much faster

### Performance optimizations

WFS response cache (v3.4.0):

```
First request: 200ms → 70ms (3x faster)
Subsequent requests: 200ms → <5ms (≈40x faster)
1000 features: 1.5s → 500ms
10000 features: 15s → 5s
```

### Network features (v3.5.0)

- External access diagnostics and firewall detection
- Automatic port configuration (Windows firewall rules helper)
- Flexible port range (supports 80–65535)
- Dynamic hostname resolution for external clients

## Client integrations

### OpenLayers

Use `/qgis-map` to render an interactive OpenLayers view that integrates with the plugin's WMS/WMTS endpoints.

![OpenLayers view](images/openlayers.png)

### MapLibre GL

- MapLibre-style viewer with automatic style conversion from QGIS renderers
- Theme and bookmark support (v3.6.0)

![MapLibre view](images/maplibre2.png)

### Google Maps / Google Earth

- Coordinate conversion utilities
- Import links shared from external services into QGIS

## Permalinks

- Generate URLs that encode the current view (coordinates, zoom/scale, layer state)
- Embed links in Office documents (Excel / PowerPoint)
- Export high-resolution PNGs for slide decks

## Quick start

### 1) Install

Place plugin in your QGIS plugins folder, or install via the QGIS plugin manager.

Windows example path:

```
%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\geo_webview
```

### 2) Basic usage

1. Open a QGIS project (.qgs/.qgz)
2. Select `Web > geo_webview` from the menu
3. The panel appears and an HTTP server starts automatically
4. Open the provided URL (e.g. `http://localhost:8089`)

### 3) Example OGC requests

WMS:

```
# GetCapabilities
http://localhost:8089/wms?SERVICE=WMS&REQUEST=GetCapabilities

# GetMap (example)
http://localhost:8089/wms?SERVICE=WMS&REQUEST=GetMap&LAYERS=mylayer&WIDTH=800&HEIGHT=600&BBOX=...
```

WMTS / XYZ:

```
# XYZ tile
http://localhost:8089/wmts/{z}/{x}/{y}.png

# GetCapabilities
http://localhost:8089/wmts?SERVICE=WMTS&REQUEST=GetCapabilities
```

WFS:

```
# GetCapabilities
http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetCapabilities

# GetFeature (GeoJSON)
http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetFeature&TYPENAME=mylayer&OUTPUTFORMAT=application/json
```

## Common use cases

### Field data collection

Serve QGIS data to mobile field teams via `geo_suite`.

### Internal map portal

Share project views on your LAN: `http://192.168.1.100:8089/qgis-map`

### Emergency map server

Quickly publish an existing QGIS project as a temporary server for disaster response.

### Distributable project package

Bundle QGIS Portable + `geo_webview` + data on a USB drive for easy distribution.

## WFS details

Supported operations:

| Operation | Description | Output |
|---|---:|---|
| GetCapabilities | Service & layer listing | XML |
| GetFeature | Retrieve features | GeoJSON / GML |
| DescribeFeatureType | Feature schema | XML |
| GetStyles | Style (SLD) | XML |

Parameters (examples):

```
SERVICE=WFS
REQUEST=GetFeature
VERSION=2.0.0
TYPENAME=layer_name
OUTPUTFORMAT=application/json
MAXFEATURES=100
BBOX=minx,miny,maxx,maxy
SRSNAME=EPSG:4326
```

Example usage (curl):

```
curl "http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetCapabilities"
curl "http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetFeature&TYPENAME=roads&OUTPUTFORMAT=application/json"
curl "http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetFeature&TYPENAME=buildings&BBOX=130,30,140,40"
```

## MapLibre integration

### Style conversion

QGIS renderers are converted to MapLibre layers (circle/line/fill) and data-driven styles where applicable.

Endpoints:

```
# Base WMTS-only style
http://localhost:8089/maplibre-style

# Layer-specific style + GeoJSON
http://localhost:8089/maplibre-style?typename=layer_name

# MapLibre viewer
http://localhost:8089/maplibre
```

Customization example (client-side):

```javascript
map.setStyle('http://localhost:8089/maplibre-style?typename=roads');
```

## Office integration

### Excel

1. Generate a permalink in `geo_webview`
2. Insert hyperlink into an Excel cell
3. Click to jump the QGIS canvas to the location

### PowerPoint

1. Export a high-resolution PNG
2. Insert image into a slide
3. Attach a permalink to the image for interactive use during a presentation

## Development & customization

Repository layout (high level):

```
geo_webview/
├── plugin.py
├── panel.py
├── server_manager.py
├── wms_service.py
├── wmts_service.py
├── wfs_service.py
├── maplibre_generator.py
└── webmap_generator.py
```

Read the technical details in `SPEC.md`.

Development steps:

1. Review `SPEC.md`
2. Inspect key modules
3. Test changes in QGIS
4. Iterate: change → test → commit

Translation support: 10 languages (including English, Japanese, French, German, Spanish, Italian, Portuguese, Chinese, Russian, Hindi)

Update translations:

```bash
python update_translations.py
```

## Security notes

⚠️ Important: This plugin is designed primarily for internal LAN use.

- Avoid publishing sensitive data publicly.
- For public exposure, add authentication and access control.
- Configure firewalls appropriately and expose only minimal datasets.

## Roadmap & changelog

- ✅ WMS/WMTS/WFS basics implemented
- ✅ Caching for performance
- ✅ MapLibre style conversion
- ⏳ Tile cache (planned)
- ❌ Full vector tile server (use external services)

See `CHANGELOG.md` for details.

## License

GNU General Public License v3 (GPLv3)

See `LICENSE`.

## Disclaimer

This software was developed and tested on a personal machine. Use at your own risk; the author is not liable for damages resulting from use.

<p align="center">
  <a href="https://giphy.com/explore/free-gif" target="_blank">
    <img src="https://github.com/yamamoto-ryuzo/QGIS_portable_3x/raw/master/imgs/giphy.gif" width="500" title="avvio QGIS">
  </a>
</p>
