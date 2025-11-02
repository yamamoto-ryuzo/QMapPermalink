"""WFS helper utilities for QMapPermalink MapLibre HTML generation.

This module extracts and normalizes WFS-related parameters used by the
MapLibre HTML generator. It mirrors the validation/normalization logic
previously embedded in `qmap_maplibre.py` so callers can simply call
`prepare_wfs_for_maplibre(permalink_text, wfs_typename)` to receive the
ready-to-use values.
"""

from typing import Dict, Any


def prepare_wfs_for_maplibre(permalink_text: str, wfs_typename: str = None) -> Dict[str, Any]:
    """Prepare and validate WFS-related variables for MapLibre HTML.

    Returns a dict with keys matching the variables used by the MapLibre
    HTML generator (for example: 'final_typename', 'wfs_typename',
    'wfs_query_url', 'wfs_source_id', 'wfs_layer_id', 'wfs_label_id',
    'wfs_layer_title', 'wfs_label_title', 'style_url', 'wfs_layers_js').

    Raises ValueError when typename is not provided or when running inside
    QGIS and the provided typename cannot be normalized to a canonical
    layer id.
    """
    from urllib.parse import quote as _quote, urlparse as _urlparse, parse_qs as _parse_qs

    _final_typename = None
    if wfs_typename and str(wfs_typename).strip():
        _final_typename = str(wfs_typename)
    else:
        try:
            _p = _urlparse(permalink_text)
            _qs = _parse_qs(_p.query)
            for k in ('typename', 'typenames', 'TYPENAME', 'TYPENAMES', 'layer', 'layers', 'type', 'typeName'):
                if k in _qs and _qs[k]:
                    _final_typename = _qs[k][0]
                    break
        except Exception:
            _final_typename = None

    if not _final_typename:
        raise ValueError("WFS typename not provided: specify 'wfs_typename' argument or include a typename in the permalink query parameters")

    _wfs_typename = _quote(_final_typename)
    _wfs_query_url = f"/wfs?SERVICE=WFS&REQUEST=GetFeature&TYPENAMES={_wfs_typename}&OUTPUTFORMAT=application/json&MAXFEATURES=1000"

    # Try to normalize to canonical QGIS layer id when QGIS is available
    try:
        from qgis.core import QgsProject  # type: ignore
        from urllib.parse import unquote_plus

        try:
            decoded_try = unquote_plus(_final_typename)
        except Exception:
            decoded_try = _final_typename

        found = None
        layers_map = QgsProject.instance().mapLayers()

        if _final_typename in layers_map:
            found = _final_typename
        elif decoded_try in layers_map:
            found = decoded_try

        if not found:
            for lid, layer in layers_map.items():
                try:
                    if str(lid).lstrip('_') == _final_typename or str(lid).lstrip('_') == decoded_try:
                        found = lid
                        break
                    if hasattr(layer, 'name') and (layer.name() == _final_typename or layer.name() == decoded_try):
                        found = lid
                        break
                except Exception:
                    continue

        if not found:
            try:
                available = list(layers_map.keys())
            except Exception:
                available = []
            raise ValueError(f"WFS typename must be a canonical QGIS layer id (layer.id()). Provided: '{_final_typename}'. Available typenames: {available}")

        _final_typename = found
        _wfs_typename = _quote(_final_typename)
        _wfs_query_url = f"/wfs?SERVICE=WFS&REQUEST=GetFeature&TYPENAMES={_wfs_typename}&OUTPUTFORMAT=application/json&MAXFEATURES=1000"
    except Exception as e:
        # propagate ValueError validation failures; otherwise continue (non-QGIS runtime)
        try:
            if isinstance(e, ValueError):
                raise
        except Exception:
            pass

    import json as _jsonmod

    _wfs_source_id = _final_typename
    _wfs_layer_id = f"{_wfs_source_id}_layer"
    _wfs_label_id = f"{_wfs_source_id}_label"
    _wfs_layer_title = f"WFS: {_final_typename}"
    _wfs_label_title = f"WFS: {_final_typename} (labels)"

    _wfs_source_id_js = _jsonmod.dumps(_wfs_source_id)
    _wfs_layer_id_js = _jsonmod.dumps(_wfs_layer_id)
    _wfs_label_id_js = _jsonmod.dumps(_wfs_label_id)
    _wfs_layer_title_js = _jsonmod.dumps(_wfs_layer_title)
    _wfs_label_title_js = _jsonmod.dumps(_wfs_label_title)

    style_url = f"/maplibre-style?typename={_wfs_typename}"

    mapbox_layers = []
    style_json = None
    wfs_layers_js = ""

    return {
        'final_typename': _final_typename,
        'wfs_typename': _wfs_typename,
        'wfs_query_url': _wfs_query_url,
        'wfs_source_id': _wfs_source_id,
        'wfs_layer_id': _wfs_layer_id,
        'wfs_label_id': _wfs_label_id,
        'wfs_layer_title': _wfs_layer_title,
        'wfs_label_title': _wfs_label_title,
        'wfs_source_id_js': _wfs_source_id_js,
        'wfs_layer_id_js': _wfs_layer_id_js,
        'wfs_label_id_js': _wfs_label_id_js,
        'wfs_layer_title_js': _wfs_layer_title_js,
        'wfs_label_title_js': _wfs_label_title_js,
        'style_url': style_url,
        'mapbox_layers': mapbox_layers,
        'style_json': style_json,
        'wfs_layers_js': wfs_layers_js,
    }
