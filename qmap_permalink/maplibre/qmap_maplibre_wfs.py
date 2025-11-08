"""WFS helper utilities for QMapPermalink MapLibre HTML generation.

This module extracts and normalizes WFS-related parameters used by the
MapLibre HTML generator. It uses QGIS API directly to convert layer styles
to MapLibre GL JS format.
"""

# Public API exported by this module
__all__ = [
    'prepare_wfs_for_maplibre',
    'qgis_layer_to_maplibre_style',
]

from typing import Dict, Any, List


def prepare_wfs_for_maplibre(permalink_text: str, wfs_typename: str = None) -> Dict[str, Any]:
    """Prepare and validate WFS-related variables for MapLibre HTML.

    This function extracts a typename from the provided permalink (unless
    `wfs_typename` is explicitly provided), url-encodes it for WFS queries,
    and — when running inside QGIS — attempts to normalize it to a canonical
    QGIS layer id. The returned dict contains the values expected by the
    MapLibre HTML template generator.

    Parameters
    ----------
    permalink_text : str
        The permalink/URL that may include query parameters such as
        `typename`/`typenames`.
    wfs_typename : Optional[str]
        Optional explicit typename to use instead of extracting from the
        permalink.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing keys used by the MapLibre generator.

    Raises
    ------
    ValueError
        When no typename can be determined or when QGIS-specific validation
        fails (running inside QGIS).
    """
    from urllib.parse import quote as _quote, urlparse as _urlparse, parse_qs as _parse_qs
    import json as _jsonmod

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
        # No typename provided — return a benign response so callers can still
        # generate a MapLibre HTML without WFS layers. Use the local WMTS
        # style endpoint so base map tiles are always available.
        local_style = "/maplibre-style"
        return {
            'final_typename': None,
            'wfs_typename': '',
            'wfs_query_url': '',
            'wfs_source_id': '',
            'wfs_layer_id': '',
            'wfs_label_id': '',
            'wfs_layer_title': '',
            'wfs_label_title': '',
            'wfs_source_id_js': _jsonmod.dumps(''),
            'wfs_layer_id_js': _jsonmod.dumps(''),
            'wfs_label_id_js': _jsonmod.dumps(''),
            'wfs_layer_title_js': _jsonmod.dumps(''),
            'wfs_label_title_js': _jsonmod.dumps(''),
            'style_url': local_style,
            'mapbox_layers': [],
            'style_json': None,
            'wfs_layers_js': '',
        }

    _wfs_typename = _quote(_final_typename)
    _wfs_query_url = f"/wfs?SERVICE=WFS&REQUEST=GetFeature&TYPENAMES={_wfs_typename}&OUTPUTFORMAT=application/json&MAXFEATURES=1000"

    # Try to normalize to canonical QGIS layer id when QGIS is available
    from qgis.core import QgsProject
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

    # Use complete URL for MapLibre style endpoint
    # MapLibre GL JS requires either a complete URL or an inline style object
    # Using URL maintains separation of concerns and allows for caching
    style_url = f"http://localhost:8089/maplibre-style?typename={_wfs_typename}"

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


def qgis_layer_to_maplibre_style(layer_id: str, source_id: str = None) -> List[Dict[str, Any]]:
    """Convert QGIS layer style to MapLibre GL JS style layers using QGIS API directly.
    
    Parameters
    ----------
    layer_id : str
        QGIS layer ID
    source_id : str, optional
        MapLibre source ID to reference. If None, uses layer_id.
        
    Returns
    -------
    List[Dict[str, Any]]
        List of MapLibre layer definitions
    """
    try:
        from qgis.core import (
            QgsProject, QgsWkbTypes,
            QgsSimpleMarkerSymbolLayer, QgsSimpleLineSymbolLayer, QgsSimpleFillSymbolLayer,
            QgsSingleSymbolRenderer, QgsCategorizedSymbolRenderer, QgsGraduatedSymbolRenderer
        )
    except ImportError:
        return []
    
    if source_id is None:
        source_id = layer_id
    
    project = QgsProject.instance()
    layer = project.mapLayer(layer_id)
    
    if not layer or not hasattr(layer, 'renderer'):
        return []
    
    renderer = layer.renderer()
    geometry_type = layer.geometryType()
    layers = []
    
    # Get renderer type
    if isinstance(renderer, QgsSingleSymbolRenderer):
        # Single symbol - one layer
        symbol = renderer.symbol()
        maplibre_layer = _convert_symbol_to_maplibre(symbol, source_id, geometry_type, len(layers))
        if maplibre_layer:
            layers.extend(maplibre_layer)
            
    elif isinstance(renderer, QgsCategorizedSymbolRenderer):
        # Categorized - multiple layers with filters
        for category in renderer.categories():
            symbol = category.symbol()
            value = category.value()
            field = renderer.classAttribute()
            
            maplibre_layer = _convert_symbol_to_maplibre(symbol, source_id, geometry_type, len(layers))
            if maplibre_layer:
                # Add filter for this category
                for layer_def in maplibre_layer:
                    # Try to convert value to number if possible
                    try:
                        numeric_value = float(value)
                        if numeric_value == int(numeric_value):
                            numeric_value = int(numeric_value)
                        layer_def['filter'] = ['==', ['get', field], numeric_value]
                    except (ValueError, TypeError):
                        layer_def['filter'] = ['==', ['get', field], str(value)]
                layers.extend(maplibre_layer)
                
    elif isinstance(renderer, QgsGraduatedSymbolRenderer):
        # Graduated - multiple layers with range filters
        for range_item in renderer.ranges():
            symbol = range_item.symbol()
            lower = range_item.lowerValue()
            upper = range_item.upperValue()
            field = renderer.classAttribute()
            
            maplibre_layer = _convert_symbol_to_maplibre(symbol, source_id, geometry_type, len(layers))
            if maplibre_layer:
                # Add range filter
                for layer_def in maplibre_layer:
                    try:
                        lower_val = float(lower)
                        upper_val = float(upper)
                        layer_def['filter'] = ['all', ['>=', ['get', field], lower_val], ['<', ['get', field], upper_val]]
                    except (ValueError, TypeError):
                        pass
                layers.extend(maplibre_layer)
    
    return layers


def _convert_symbol_to_maplibre(symbol, source_id: str, geometry_type, base_index: int) -> List[Dict[str, Any]]:
    """Convert QgsSymbol to MapLibre layer definition(s).
    
    Parameters
    ----------
    symbol : QgsSymbol
        QGIS symbol to convert
    source_id : str
        MapLibre source ID
    geometry_type : QgsWkbTypes.GeometryType
        Geometry type (Point, Line, Polygon)
    base_index : int
        Base index for layer ID generation
        
    Returns
    -------
    List[Dict[str, Any]]
        List of MapLibre layer definitions (may be multiple for polygon with outline)
    """
    try:
        from qgis.core import (
            QgsWkbTypes,
            QgsSimpleMarkerSymbolLayer, QgsSimpleLineSymbolLayer, QgsSimpleFillSymbolLayer
        )
    except ImportError:
        return []
    
    if not symbol:
        return []
    
    layers = []
    
    # Get the first symbol layer (main style)
    if symbol.symbolLayerCount() > 0:
        symbol_layer = symbol.symbolLayer(0)
        
        if geometry_type == QgsWkbTypes.PointGeometry:
            # Point geometry - create circle layer
            paint = {}
            layout = {}
            
            if isinstance(symbol_layer, QgsSimpleMarkerSymbolLayer):
                # Fill color
                color = symbol_layer.color()
                if color.isValid():
                    paint['circle-color'] = color.name()
                    paint['circle-opacity'] = color.alphaF()
                
                # Stroke
                stroke_color = symbol_layer.strokeColor()
                if stroke_color.isValid():
                    paint['circle-stroke-color'] = stroke_color.name()
                    paint['circle-stroke-opacity'] = stroke_color.alphaF()
                    paint['circle-stroke-width'] = symbol_layer.strokeWidth()
                
                # Size
                paint['circle-radius'] = symbol_layer.size() / 2
            
            layers.append({
                'id': f"{source_id}_circle_{base_index}",
                'type': 'circle',
                'source': source_id,
                'paint': paint,
                'layout': layout
            })
            
        elif geometry_type == QgsWkbTypes.LineGeometry:
            # Line geometry
            paint = {}
            layout = {}
            
            if isinstance(symbol_layer, QgsSimpleLineSymbolLayer):
                # Color
                color = symbol_layer.color()
                if color.isValid():
                    paint['line-color'] = color.name()
                    paint['line-opacity'] = color.alphaF()
                
                # Width
                paint['line-width'] = symbol_layer.width()
                
                # Join and cap styles
                pen_join_style = symbol_layer.penJoinStyle()
                if pen_join_style == 0x40:  # Qt.MiterJoin
                    layout['line-join'] = 'miter'
                elif pen_join_style == 0x80:  # Qt.BevelJoin
                    layout['line-join'] = 'bevel'
                elif pen_join_style == 0x100:  # Qt.RoundJoin
                    layout['line-join'] = 'round'
                
                pen_cap_style = symbol_layer.penCapStyle()
                if pen_cap_style == 0x00:  # Qt.FlatCap
                    layout['line-cap'] = 'butt'
                elif pen_cap_style == 0x10:  # Qt.SquareCap
                    layout['line-cap'] = 'square'
                elif pen_cap_style == 0x20:  # Qt.RoundCap
                    layout['line-cap'] = 'round'
            
            layers.append({
                'id': f"{source_id}_line_{base_index}",
                'type': 'line',
                'source': source_id,
                'paint': paint,
                'layout': layout
            })
            
        elif geometry_type == QgsWkbTypes.PolygonGeometry:
            # Polygon geometry - may have fill and/or outline
            
            if isinstance(symbol_layer, QgsSimpleFillSymbolLayer):
                # Fill
                fill_color = symbol_layer.color()
                has_fill = fill_color.isValid() and fill_color.alpha() > 0
                
                if has_fill:
                    paint = {
                        'fill-color': fill_color.name(),
                        'fill-opacity': fill_color.alphaF()
                    }
                    layers.append({
                        'id': f"{source_id}_fill_{base_index}",
                        'type': 'fill',
                        'source': source_id,
                        'paint': paint,
                        'layout': {}
                    })
                
                # Outline
                stroke_color = symbol_layer.strokeColor()
                if stroke_color.isValid() and stroke_color.alpha() > 0:
                    paint = {
                        'line-color': stroke_color.name(),
                        'line-opacity': stroke_color.alphaF(),
                        'line-width': symbol_layer.strokeWidth()
                    }
                    
                    layout = {}
                    pen_join_style = symbol_layer.penJoinStyle()
                    if pen_join_style == 0x40:  # Qt.MiterJoin
                        layout['line-join'] = 'miter'
                    elif pen_join_style == 0x80:  # Qt.BevelJoin
                        layout['line-join'] = 'bevel'
                    elif pen_join_style == 0x100:  # Qt.RoundJoin
                        layout['line-join'] = 'round'
                    
                    layers.append({
                        'id': f"{source_id}_line_{base_index + (1 if has_fill else 0)}",
                        'type': 'line',
                        'source': source_id,
                        'paint': paint,
                        'layout': layout
                    })
    
    return layers


def sld_to_mapbox_style(sld_xml, source_id="qgis"):
    """
    SLD XML を Mapbox Style の layers に変換。
    PointSymbolizer, LineSymbolizer, PolygonSymbolizer をサポート。
    QGISのスタイル設定（色、線幅、透明度、線種、結合スタイル、キャップスタイル等）を
    可能な限りMapLibre GL JSに反映。
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
                # Ruleの名前を取得（カテゴリ分類やグラデーション分類用）
                rule_name_elem = rule.find('.//sld:Name', ns) or rule.find('.//Name')
                rule_name = rule_name_elem.text if (rule_name_elem is not None and rule_name_elem.text) else None
                
                # Filterの取得（カテゴリ分類・グラデーション分類用）
                filter_elem = rule.find('.//ogc:Filter', ns) or rule.find('.//Filter')
                mapbox_filter = None
                if filter_elem is not None:
                    # PropertyIsEqualTo（カテゴリ分類）
                    prop_eq = filter_elem.find('.//ogc:PropertyIsEqualTo', ns) or filter_elem.find('.//PropertyIsEqualTo')
                    if prop_eq is not None:
                        prop_name_elem = prop_eq.find('.//ogc:PropertyName', ns) or prop_eq.find('.//PropertyName')
                        literal_elem = prop_eq.find('.//ogc:Literal', ns) or prop_eq.find('.//Literal')
                        if prop_name_elem is not None and literal_elem is not None:
                            field = prop_name_elem.text.strip() if prop_name_elem.text else ''
                            value = literal_elem.text.strip() if literal_elem.text else ''
                            # Try to parse as number if possible
                            try:
                                value = float(value)
                                if value == int(value):
                                    value = int(value)
                            except Exception:
                                pass
                            mapbox_filter = ['==', ['get', field], value]
                    
                    # PropertyIsGreaterThanOrEqualTo & PropertyIsLessThan（グラデーション分類）
                    and_elem = filter_elem.find('.//ogc:And', ns) or filter_elem.find('.//And')
                    if and_elem is not None:
                        gte_elem = and_elem.find('.//ogc:PropertyIsGreaterThanOrEqualTo', ns) or and_elem.find('.//PropertyIsGreaterThanOrEqualTo')
                        lt_elem = and_elem.find('.//ogc:PropertyIsLessThan', ns) or and_elem.find('.//PropertyIsLessThan')
                        if gte_elem is not None and lt_elem is not None:
                            prop_gte = gte_elem.find('.//ogc:PropertyName', ns) or gte_elem.find('.//PropertyName')
                            lit_gte = gte_elem.find('.//ogc:Literal', ns) or gte_elem.find('.//Literal')
                            prop_lt = lt_elem.find('.//ogc:PropertyName', ns) or lt_elem.find('.//PropertyName')
                            lit_lt = lt_elem.find('.//ogc:Literal', ns) or lt_elem.find('.//Literal')
                            if all([prop_gte, lit_gte, prop_lt, lit_lt]):
                                field = prop_gte.text.strip() if prop_gte.text else ''
                                lower = lit_gte.text.strip() if lit_gte.text else ''
                                upper = lit_lt.text.strip() if lit_lt.text else ''
                                try:
                                    lower = float(lower)
                                    upper = float(upper)
                                except Exception:
                                    pass
                                # ['all', ['>=', ['get', field], lower], ['<', ['get', field], upper]]
                                mapbox_filter = ['all', ['>=', ['get', field], lower], ['<', ['get', field], upper]]
                        # PropertyIsGreaterThanOrEqualTo only (最後のクラス)
                        elif gte_elem is not None:
                            prop_gte = gte_elem.find('.//ogc:PropertyName', ns) or gte_elem.find('.//PropertyName')
                            lit_gte = gte_elem.find('.//ogc:Literal', ns) or gte_elem.find('.//Literal')
                            if prop_gte is not None and lit_gte is not None:
                                field = prop_gte.text.strip() if prop_gte.text else ''
                                lower = lit_gte.text.strip() if lit_gte.text else ''
                                try:
                                    lower = float(lower)
                                except Exception:
                                    pass
                                mapbox_filter = ['>=', ['get', field], lower]
                    # PropertyIsGreaterThanOrEqualTo only (without And)
                    elif filter_elem.find('.//ogc:PropertyIsGreaterThanOrEqualTo', ns) or filter_elem.find('.//PropertyIsGreaterThanOrEqualTo'):
                        gte_elem = filter_elem.find('.//ogc:PropertyIsGreaterThanOrEqualTo', ns) or filter_elem.find('.//PropertyIsGreaterThanOrEqualTo')
                        prop_gte = gte_elem.find('.//ogc:PropertyName', ns) or gte_elem.find('.//PropertyName')
                        lit_gte = gte_elem.find('.//ogc:Literal', ns) or gte_elem.find('.//Literal')
                        if prop_gte is not None and lit_gte is not None:
                            field = prop_gte.text.strip() if prop_gte.text else ''
                            lower = lit_gte.text.strip() if lit_gte.text else ''
                            try:
                                lower = float(lower)
                            except Exception:
                                pass
                            mapbox_filter = ['>=', ['get', field], lower]
                
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
                        # WellKnownName の取得（シンボル形状）
                        wkn_elem = mark.find('.//sld:WellKnownName', ns) or mark.find('.//WellKnownName')
                        well_known_name = wkn_elem.text.strip() if (wkn_elem is not None and wkn_elem.text) else 'circle'
                        
                        # MapLibre では circle のみサポート（square, star, triangle, cross, x は未対応）
                        # 将来的にはSymbolLayerでアイコン画像を使用可能
                        if well_known_name not in ['circle']:
                            # 非対応形状は circle にフォールバック
                            well_known_name = 'circle'
                        
                        fill = mark.find('.//sld:Fill', ns) or mark.find('.//Fill')
                        if fill:
                            # Extract fill color from SLD and use as concrete value
                            color = _extract_css_param(fill, 'fill')
                            if color:
                                paint['circle-color'] = color
                            # fill-opacity
                            fill_opacity = _extract_css_param(fill, 'fill-opacity')
                            if fill_opacity:
                                try:
                                    paint['circle-opacity'] = float(fill_opacity)
                                except Exception:
                                    pass

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
                            # stroke-opacity
                            stroke_opacity = _extract_css_param(stroke, 'stroke-opacity')
                            if stroke_opacity:
                                try:
                                    paint['circle-stroke-opacity'] = float(stroke_opacity)
                                except Exception:
                                    pass

                    # Size: try to extract Size element or Graphic/Size if present
                    size_elem = point_sym.find('.//sld:Size', ns) or point_sym.find('.//Size')
                    if size_elem is not None and size_elem.text:
                        try:
                            paint['circle-radius'] = float(size_elem.text.strip())
                        except Exception:
                            pass
                    
                    # ポイントレイヤーを追加
                    if layer_type == 'circle':
                        base_index = len(layers)
                        layers.append({
                            'id': f"{source_id}_{layer_type}_{base_index}",
                            'type': layer_type,
                            'source': source_id,
                            'paint': paint,
                            'layout': layout
                        })

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
                        # line join/cap
                        join = _extract_css_param(stroke, 'stroke-linejoin')
                        if join:
                            # Map SLD 'mitre' to MapLibre 'miter'
                            join_mbx = 'miter' if join.lower() == 'mitre' else join.lower()
                            layout['line-join'] = join_mbx
                        cap = _extract_css_param(stroke, 'stroke-linecap')
                        if cap:
                            layout['line-cap'] = cap.lower()
                        # dasharray
                        dash = _extract_css_param(stroke, 'stroke-dasharray')
                        if dash:
                            try:
                                parts = [float(x) for x in dash.replace(',', ' ').split() if x.strip()]
                                if parts:
                                    paint['line-dasharray'] = parts
                            except Exception:
                                pass
                        # LineSymbolizerのみの場合でも必ずlayersに追加
                        base_index = len(layers)
                        layers.append({
                            'id': f"{source_id}_{layer_type}_{base_index}",
                            'type': layer_type,
                            'source': source_id,
                            'paint': paint,
                            'layout': layout
                        })

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
                        # stroke-opacity
                        sop = _extract_css_param(stroke, 'stroke-opacity')
                        outline_opacity = None
                        if sop:
                            try:
                                outline_opacity = float(sop)
                            except Exception:
                                outline_opacity = None
                        # join/cap/dash for outline
                        outline_join = _extract_css_param(stroke, 'stroke-linejoin')
                        outline_cap = _extract_css_param(stroke, 'stroke-linecap')
                        outline_dash = _extract_css_param(stroke, 'stroke-dasharray')
                    
                    # If no stroke color extracted but stroke element exists, use default
                    if stroke is not None and not outline_color:
                        outline_color = '#000000'  # Default to black
                        outline_width = 1.0

                    # If there is no effective fill (no color or fully transparent),
                    # prefer to omit the fill layer and only emit a line layer for the
                    # polygon outline when a stroke is present. This better matches the
                    # user's expectation for "ブラシなし" (brushless) polygon styles.
                    has_fill = False
                    try:
                        if 'fill-color' in paint and paint['fill-color']:
                            # If explicit fill-opacity is zero, treat as no fill
                            fop_val = paint.get('fill-opacity')
                            if fop_val is None or (isinstance(fop_val, (int, float)) and float(fop_val) > 0):
                                has_fill = True
                        # If fill-color is missing or empty string, no fill
                        elif not paint.get('fill-color'):
                            has_fill = False
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
                            if outline_opacity is not None:
                                try:
                                    line_paint['line-opacity'] = float(outline_opacity)
                                except Exception:
                                    pass
                            # layout for outline
                            line_layout = {}
                            if outline_join:
                                line_layout['line-join'] = 'miter' if outline_join.lower() == 'mitre' else outline_join.lower()
                            if outline_cap:
                                line_layout['line-cap'] = outline_cap.lower()
                            if outline_dash:
                                try:
                                    parts = [float(x) for x in outline_dash.replace(',', ' ').split() if x.strip()]
                                    if parts:
                                        line_paint['line-dasharray'] = parts
                                except Exception:
                                    pass
                            layers.append({
                                'id': f"{source_id}_line_{line_index}",
                                'type': 'line',
                                'source': source_id,
                                'paint': line_paint,
                                'layout': line_layout
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
