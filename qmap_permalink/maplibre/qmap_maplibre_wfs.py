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


def sld_to_mapbox_style(sld_xml, source_id="qgis"):
    """
    SLD XML を Mapbox Style の layers に変換。
    シンプルな PointSymbolizer, LineSymbolizer, PolygonSymbolizer をサポート。
    """
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(sld_xml)
        layers = []

        # SLD の名前空間を考慮
        ns = {'sld': 'http://www.opengis.net/sld', 'ogc': 'http://www.opengis.net/ogc'}

        # FeatureTypeStyle を探す
        feature_type_styles = root.findall('.//sld:FeatureTypeStyle', ns)
        if not feature_type_styles:
            feature_type_styles = root.findall('.//FeatureTypeStyle')  # 名前空間なしの場合

        for fts in feature_type_styles:
            rules = fts.findall('.//sld:Rule', ns) or fts.findall('.//Rule')
            for rule in rules:
                # Symbolizer を探す
                point_sym = rule.find('.//sld:PointSymbolizer', ns) or rule.find('.//PointSymbolizer')
                line_sym = rule.find('.//sld:LineSymbolizer', ns) or rule.find('.//LineSymbolizer')
                poly_sym = rule.find('.//sld:PolygonSymbolizer', ns) or rule.find('.//PolygonSymbolizer')

                paint = {}
                layout = {}
                layer_type = None

                if point_sym is not None:
                    layer_type = 'circle'
                    # Graphic > Mark > Fill/Stroke
                    mark = point_sym.find('.//sld:Mark', ns) or point_sym.find('.//Mark')
                    if mark:
                        fill = mark.find('.//sld:Fill', ns) or mark.find('.//Fill')
                        if fill:
                            # Extract fill color from SLD and use as concrete value
                            color = _extract_css_param(fill, 'fill')
                            if color:
                                paint['circle-color'] = color

                        stroke = mark.find('.//sld:Stroke', ns) or mark.find('.//Stroke')
                        if stroke:
                            # Extract stroke color from SLD and use as concrete value
                            stroke_color = _extract_css_param(stroke, 'stroke')
                            if stroke_color:
                                paint['circle-stroke-color'] = stroke_color
                            sw = _extract_css_param(stroke, 'stroke-width')
                            if sw:
                                try:
                                    paint['circle-stroke-width'] = float(sw)
                                except Exception:
                                    # ignore non-numeric
                                    pass

                    # Size: try to extract Size element or Graphic/Size if present
                    size_elem = point_sym.find('.//sld:Size', ns) or point_sym.find('.//Size')
                    if size_elem is not None and size_elem.text:
                        try:
                            paint['circle-radius'] = float(size_elem.text.strip())
                        except Exception:
                            pass

                elif line_sym is not None:
                    layer_type = 'line'
                    stroke = line_sym.find('.//sld:Stroke', ns) or line_sym.find('.//Stroke')
                    if stroke:
                        # Extract stroke color and width from SLD and use as concrete values
                        color = _extract_css_param(stroke, 'stroke')
                        if color:
                            paint['line-color'] = color
                        # stroke-width
                        width = _extract_css_param(stroke, 'stroke-width')
                        if width:
                            try:
                                paint['line-width'] = float(width)
                            except Exception:
                                pass
                        # opacity
                        opacity = _extract_css_param(stroke, 'stroke-opacity')
                        if opacity:
                            try:
                                paint['line-opacity'] = float(opacity)
                            except Exception:
                                pass

                elif poly_sym is not None:
                    layer_type = 'fill'
                    fill = poly_sym.find('.//sld:Fill', ns) or poly_sym.find('.//Fill')
                    if fill:
                        # Extract fill color and opacity
                        color = _extract_css_param(fill, 'fill')
                        if color:
                            paint['fill-color'] = color
                        fop = _extract_css_param(fill, 'fill-opacity')
                        if fop:
                            try:
                                paint['fill-opacity'] = float(fop)
                            except Exception:
                                pass

                    stroke = poly_sym.find('.//sld:Stroke', ns) or poly_sym.find('.//Stroke')
                    outline_color = None
                    outline_width = None
                    if stroke:
                        # Extract stroke color and width for outline
                        outline_color = _extract_css_param(stroke, 'stroke')
                        # try stroke-width
                        sw = _extract_css_param(stroke, 'stroke-width')
                        if sw:
                            try:
                                outline_width = float(sw)
                            except Exception:
                                outline_width = None

                    # If there is no effective fill (no color or fully transparent),
                    # prefer to omit the fill layer and only emit a line layer for the
                    # polygon outline when a stroke is present. This better matches the
                    # user's expectation for "ブラシなし" (brushless) polygon styles.
                    has_fill = False
                    try:
                        if 'fill-color' in paint:
                            # If explicit fill-opacity is zero, treat as no fill
                            fop_val = paint.get('fill-opacity')
                            if fop_val is None or (isinstance(fop_val, (int, float)) and float(fop_val) > 0):
                                has_fill = True
                    except Exception:
                        has_fill = False

                    # For polygons we may have either a fill, an outline (stroke), or both.
                    # If there is an effective fill (has_fill==True) create a fill layer.
                    # If there is a stroke/outline, always create a line layer for the outline.
                    try:
                        # create fill layer only when there is an effective fill
                        if has_fill and layer_type == 'fill':
                            base_index = len(layers)
                            layers.append({
                                'id': f"{source_id}_{layer_type}_{base_index}",
                                'type': layer_type,
                                'source': source_id,
                                'paint': paint,
                                'layout': layout
                            })
                        # create outline line layer when stroke present
                        if 'outline_color' in locals() and outline_color:
                            # use a deterministic index based on current layers length
                            line_index = len(layers)
                            # determine width with sensible fallback
                            if outline_width is not None:
                                line_width_val = outline_width
                            else:
                                line_width_val = 1
                            line_paint = {'line-color': outline_color, 'line-width': line_width_val, 'line-opacity': 1.0}
                            layers.append({
                                'id': f"{source_id}_line_{line_index}",
                                'type': 'line',
                                'source': source_id,
                                'paint': line_paint,
                                'layout': {}
                            })
                    except Exception:
                        # non-fatal: continue without outline/fill
                        pass

        return layers
    except Exception as e:
        # Importing _qgis_log would create circular dependency; simply emit a warning
        try:
            print(f"SLD to Mapbox Style conversion failed: {e}")
        except Exception:
            pass
        return []


def _extract_css_param(element, param_name):
    """
    SLD の CssParameter を抽出。
    """
    try:
        for css in element.findall('.//sld:CssParameter', {'sld': 'http://www.opengis.net/sld'}):
            if css.get('name') == param_name and css.text:
                return css.text.strip()
        # 名前空間なし
        for css in element.findall('.//CssParameter'):
            if css.get('name') == param_name and css.text:
                return css.text.strip()
    except Exception:
        pass
    return None
