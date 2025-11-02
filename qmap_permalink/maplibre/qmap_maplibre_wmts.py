"""WMTS helper utilities for QMapPermalink MapLibre HTML generation.

This module contains a small, dependency-light helper to select the appropriate
WMTS tile template and to provide the default WMTS layers JavaScript snippet
that is injected into the MapLibre HTML template.

The functions intentionally avoid importing heavy QGIS modules at import time
and instead attempt lightweight existence checks so the module can be used
both inside and outside QGIS (e.g. in unit tests).
"""


def choose_tile_template():
    """Return a tile URL template string.

    Prefers a local WMTS endpoint when QGIS is available, otherwise falls
    back to a public OSM tile template.
    """
    try:
        # existence check for QGIS runtime
        from qgis.core import QgsApplication  # type: ignore
        return "/wmts/{z}/{x}/{y}.png"
    except Exception:
        return "https://tile.openstreetmap.org/{z}/{x}/{y}.png"


def default_wmts_layers_js():
    """Return a JS snippet (string) that defines the initial wmtsLayers array.

    The returned string is intended to be inserted verbatim into the HTML
    template used by the MapLibre viewer.
    """
    return "const wmtsLayers = [\n    { id: 'qmap', title: 'QGIS Map (WMTS)' }\n];"
