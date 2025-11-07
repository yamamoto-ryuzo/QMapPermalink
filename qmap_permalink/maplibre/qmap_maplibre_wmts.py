"""WMTS helper utilities for QMapPermalink MapLibre HTML generation.

This module contains a small, dependency-light helper to select the appropriate
WMTS tile template and to provide the default WMTS layers JavaScript snippet
that is injected into the MapLibre HTML template.

The functions intentionally avoid importing heavy QGIS modules at import time
and instead attempt lightweight existence checks so the module can be used
both inside and outside QGIS (e.g. in unit tests).
"""

# Public API exported by this module
__all__ = [
    'choose_tile_template',
    'default_wmts_layers_js',
]


def choose_tile_template() -> str:
    """Return a tile URL template string.

    Prefers a local WMTS endpoint when QGIS is available, otherwise falls
    back to a public OSM tile template.

    Returns
    -------
    str
        Tile URL template suitable for MapLibre tile sources.
    """
    try:
        # existence check for QGIS runtime
        from qgis.core import QgsApplication  # type: ignore
        # MapLibre requires complete URLs for tile sources
        # Try to get the actual server port from the plugin
        try:
            from ..qmap_permalink_server_manager import QMapPermalinkServerManager
            # Attempt to find a running server instance
            port = 8089  # default fallback
            # In practice, the server manager is instantiated with the plugin
            # and we don't have easy access here. We use the default port.
        except Exception:
            port = 8089
        return f"http://localhost:{port}/wmts/{{z}}/{{x}}/{{y}}.png"
    except Exception:
        return "https://tile.openstreetmap.org/{z}/{x}/{y}.png"


def default_wmts_layers_js() -> str:
    """Return a JS snippet (string) that defines the initial wmtsLayers array.

    The returned string is intended to be inserted verbatim into the HTML
    template used by the MapLibre viewer.
    """
    return "const wmtsLayers = [\n    { id: 'qmap', title: 'QGIS Map (WMTS)' }\n];"
