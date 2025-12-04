# -*- coding: utf-8 -*-
"""Simple SLD renderer helpers

This module provides a lightweight conversion of QGIS renderers (categorized,
graduated, rule-based, single-symbol) into a basic SLD 1.1.0 string. It is
intended as a pragmatic, best-effort exporter for use by WFS GetStyles.

The output focuses on simple symbol properties (fill/stroke color, stroke
width, size, opacity). Complex symbol layers, external graphics or vendor
options are intentionally not fully supported here.
"""

from typing import Optional

from qgis.core import (
    QgsCategorizedSymbolRenderer, QgsGraduatedSymbolRenderer, QgsRuleBasedRenderer,
    QgsSingleSymbolRenderer
)


def _sld_header(layer_name: str) -> str:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<StyledLayerDescriptor version="1.1.0" xmlns="http://www.opengis.net/sld" '
        f'xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        f'xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd">\n'
        f'  <NamedLayer>\n'
        f'    <Name>{layer_name}</Name>\n'
        f'    <UserStyle>\n'
        f'      <FeatureTypeStyle>\n'
    )


def _sld_footer() -> str:
    return (
        f'      </FeatureTypeStyle>\n'
        f'    </UserStyle>\n'
        f'  </NamedLayer>\n'
        f'</StyledLayerDescriptor>'
    )


def _escape_xml(s: Optional[str]) -> str:
    if s is None:
        return ''
    return (str(s)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))


def _extract_symbol_properties(symbol, geom_type: str):
    """Extract color, stroke, width, size, opacity from symbol or symbol layer.
    
    Returns: (color, stroke_color, stroke_width, stroke_opacity, size, opacity, has_brush, 
              pen_join_style, pen_cap_style, pen_style, point_shape)
    """
    color = None
    stroke_color = None
    stroke_width = None
    stroke_opacity = None
    size = None
    opacity = None
    has_brush = True
    pen_join_style = None
    pen_cap_style = None
    pen_style = None
    point_shape = None

    # First, try to extract properties from symbol layer (most reliable)
    try:
        if hasattr(symbol, 'symbolLayer') and callable(symbol.symbolLayer):
            sl = symbol.symbolLayer(0)
            if sl is not None:
                # Fill color
                if hasattr(sl, 'color') and callable(sl.color):
                    try:
                        color = sl.color()
                    except Exception:
                        pass
                
                # Stroke color
                if hasattr(sl, 'strokeColor') and callable(sl.strokeColor):
                    try:
                        stroke_color = sl.strokeColor()
                    except Exception:
                        pass
                
                # Stroke width
                if hasattr(sl, 'strokeWidth') and callable(sl.strokeWidth):
                    try:
                        stroke_width = sl.strokeWidth()
                    except Exception:
                        pass
                
                # Stroke opacity (from stroke color alpha)
                if stroke_color is not None and hasattr(stroke_color, 'alpha') and callable(stroke_color.alpha):
                    try:
                        stroke_opacity = stroke_color.alpha() / 255.0
                    except Exception:
                        pass
                
                # Size (for points)
                if hasattr(sl, 'size') and callable(sl.size):
                    try:
                        size = sl.size()
                    except Exception:
                        pass
                
                # Opacity from fill color alpha
                if color is not None and hasattr(color, 'alpha') and callable(color.alpha):
                    try:
                        opacity = color.alpha() / 255.0
                    except Exception:
                        pass
                
                # Pen join style (miter, round, bevel)
                if hasattr(sl, 'penJoinStyle') and callable(sl.penJoinStyle):
                    try:
                        pen_join_style = sl.penJoinStyle()
                        try:
                            from qgis.core import QgsMessageLog, Qgis
                            QgsMessageLog.logMessage(f'🔧 Extracted penJoinStyle: {pen_join_style} (type: {type(pen_join_style).__name__})', 'QMapPermalink', Qgis.Info)
                        except Exception:
                            pass
                    except Exception:
                        pass
                
                # Pen cap style (flat, round, square)
                if hasattr(sl, 'penCapStyle') and callable(sl.penCapStyle):
                    try:
                        pen_cap_style = sl.penCapStyle()
                        try:
                            from qgis.core import QgsMessageLog, Qgis
                            QgsMessageLog.logMessage(f'🔧 Extracted penCapStyle: {pen_cap_style}', 'QMapPermalink', Qgis.Info)
                        except Exception:
                            pass
                    except Exception:
                        pass
                
                # Pen style (solid, dash, dot, etc.)
                if hasattr(sl, 'penStyle') and callable(sl.penStyle):
                    try:
                        pen_style = sl.penStyle()
                        try:
                            from qgis.core import QgsMessageLog, Qgis
                            QgsMessageLog.logMessage(f'🔧 Extracted penStyle: {pen_style}', 'QMapPermalink', Qgis.Info)
                        except Exception:
                            pass
                    except Exception:
                        pass
                
                # Point shape (for markers)
                if geom_type == 'Point':
                    if hasattr(sl, 'shape') and callable(sl.shape):
                        try:
                            point_shape = sl.shape()
                        except Exception:
                            pass
                    # Also try name() for well-known names
                    if point_shape is None and hasattr(sl, 'name') and callable(sl.name):
                        try:
                            point_shape = sl.name()
                        except Exception:
                            pass
                
                # Brush style (for polygons - NoBrush detection)
                if geom_type == 'Polygon':
                    if hasattr(sl, 'brushStyle') and callable(sl.brushStyle):
                        try:
                            from qgis.PyQt.QtCore import Qt
                            brush_style = sl.brushStyle()
                            if brush_style == Qt.NoBrush:
                                has_brush = False
                                color = None
                        except Exception:
                            pass
                # If some properties are still missing, try additional symbol layers
                try:
                    if (hasattr(symbol, 'symbolLayerCount') and callable(symbol.symbolLayerCount)):
                        cnt = symbol.symbolLayerCount()
                        for idx in range(1, int(cnt or 0)):
                            try:
                                slx = symbol.symbolLayer(idx)
                            except Exception:
                                slx = None
                            if slx is None:
                                continue
                            # Fill color fallback
                            if color is None and hasattr(slx, 'color') and callable(slx.color):
                                try:
                                    c2 = slx.color()
                                    if c2 is not None:
                                        color = c2
                                except Exception:
                                    pass
                            # Stroke color/width fallback
                            if stroke_color is None and hasattr(slx, 'strokeColor') and callable(slx.strokeColor):
                                try:
                                    stroke_color = slx.strokeColor()
                                except Exception:
                                    pass
                            if stroke_width is None and hasattr(slx, 'strokeWidth') and callable(slx.strokeWidth):
                                try:
                                    stroke_width = slx.strokeWidth()
                                except Exception:
                                    pass
                            # Pen styles fallback
                            if pen_join_style is None and hasattr(slx, 'penJoinStyle') and callable(slx.penJoinStyle):
                                try:
                                    pen_join_style = slx.penJoinStyle()
                                except Exception:
                                    pass
                            if pen_cap_style is None and hasattr(slx, 'penCapStyle') and callable(slx.penCapStyle):
                                try:
                                    pen_cap_style = slx.penCapStyle()
                                except Exception:
                                    pass
                            if pen_style is None and hasattr(slx, 'penStyle') and callable(slx.penStyle):
                                try:
                                    pen_style = slx.penStyle()
                                except Exception:
                                    pass
                            # Size fallback for points
                            if size is None and hasattr(slx, 'size') and callable(slx.size):
                                try:
                                    size = slx.size()
                                except Exception:
                                    pass
                            # Brush style check on any layer
                            if geom_type == 'Polygon' and hasattr(slx, 'brushStyle') and callable(slx.brushStyle):
                                try:
                                    from qgis.PyQt.QtCore import Qt
                                    if slx.brushStyle() == Qt.NoBrush:
                                        has_brush = False
                                except Exception:
                                    pass
                except Exception:
                    pass
    except Exception as e:
        try:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(f"⚠️ sld_renderer: symbolLayer extraction failed: {e}", "QMapPermalink", Qgis.Warning)
        except Exception:
            pass

    # Fallback: try methods directly on symbol
    if color is None:
        try:
            color = symbol.color()
        except Exception:
            pass
    
    if stroke_color is None:
        try:
            stroke_color = symbol.strokeColor()
        except Exception:
            try:
                stroke_color = symbol.color()
            except Exception:
                pass
    
    if stroke_width is None:
        try:
            stroke_width = symbol.strokeWidth()
        except Exception:
            try:
                stroke_width = symbol.width()
            except Exception:
                pass
    
    if size is None:
        try:
            size = symbol.size()
        except Exception:
            pass
    
    if opacity is None:
        try:
            opacity = symbol.opacity()
        except Exception:
            pass
    
    # Final check: color alpha = 0 means no fill
    if has_brush and color is not None:
        try:
            if hasattr(color, 'alpha') and callable(color.alpha) and color.alpha() == 0:
                has_brush = False
                color = None
        except Exception:
            pass
    
    return color, stroke_color, stroke_width, stroke_opacity, size, opacity, has_brush, pen_join_style, pen_cap_style, pen_style, point_shape


def _build_stroke_params(stroke_color, stroke_width, stroke_opacity, pen_join_style, pen_cap_style, pen_style):
    """Build stroke CssParameter elements including advanced styling.
    
    Returns: formatted string with CssParameter elements
    """
    sc = _escape_xml(stroke_color or '#000000')
    sw = stroke_width if stroke_width is not None else 1
    so = stroke_opacity if (stroke_opacity is not None) else 1.0
    
    stroke_params = f'    <CssParameter name="stroke">{sc}</CssParameter>\n'
    stroke_params += f'    <CssParameter name="stroke-width">{sw}</CssParameter>\n'
    if so < 1.0:
        stroke_params += f'    <CssParameter name="stroke-opacity">{so}</CssParameter>\n'
    
    # Add line join style (using integer values for compatibility)
    if pen_join_style is not None:
        try:
            # Qt.MiterJoin=0, Qt.BevelJoin=64, Qt.RoundJoin=128
            join_val = int(pen_join_style)
            if join_val == 64:  # BevelJoin
                stroke_params += f'    <CssParameter name="stroke-linejoin">bevel</CssParameter>\n'
            elif join_val == 128:  # RoundJoin
                stroke_params += f'    <CssParameter name="stroke-linejoin">round</CssParameter>\n'
            elif join_val == 0:  # MiterJoin
                stroke_params += f'    <CssParameter name="stroke-linejoin">mitre</CssParameter>\n'
        except Exception:
            pass
    
    # Add line cap style (using integer values for compatibility)
    if pen_cap_style is not None:
        try:
            # Qt.FlatCap=0, Qt.SquareCap=16, Qt.RoundCap=32
            cap_val = int(pen_cap_style)
            if cap_val == 0:  # FlatCap
                stroke_params += f'    <CssParameter name="stroke-linecap">butt</CssParameter>\n'
            elif cap_val == 16:  # SquareCap
                stroke_params += f'    <CssParameter name="stroke-linecap">square</CssParameter>\n'
            elif cap_val == 32:  # RoundCap
                stroke_params += f'    <CssParameter name="stroke-linecap">round</CssParameter>\n'
        except Exception:
            pass
    
    # Add dash pattern (using integer values for compatibility)
    if pen_style is not None:
        try:
            # Qt.SolidLine=1, Qt.DashLine=2, Qt.DotLine=3, Qt.DashDotLine=4, Qt.DashDotDotLine=5
            style_val = int(pen_style)
            if style_val == 2:  # DashLine
                stroke_params += f'    <CssParameter name="stroke-dasharray">5 2</CssParameter>\n'
            elif style_val == 3:  # DotLine
                stroke_params += f'    <CssParameter name="stroke-dasharray">1 2</CssParameter>\n'
            elif style_val == 4:  # DashDotLine
                stroke_params += f'    <CssParameter name="stroke-dasharray">5 2 1 2</CssParameter>\n'
            elif style_val == 5:  # DashDotDotLine
                stroke_params += f'    <CssParameter name="stroke-dasharray">5 2 1 2 1 2</CssParameter>\n'
        except Exception:
            pass
    
    return stroke_params


def _symbol_to_symbolizer(symbol, geom_type: str) -> str:
    """Return a simple Symbolizer XML fragment for the given symbol.

    geom_type: 'Point', 'LineString', or 'Polygon'
    """
    try:
        # Extract all properties in one unified function
        color, stroke_color, stroke_width, stroke_opacity, size, opacity, has_brush, pen_join_style, pen_cap_style, pen_style, point_shape = _extract_symbol_properties(symbol, geom_type)

        # Debug: Log extracted properties
        try:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(
                f'📋 Symbol properties for {geom_type}: '
                f'stroke_color={stroke_color}, stroke_width={stroke_width}, '
                f'pen_join_style={pen_join_style}, pen_cap_style={pen_cap_style}, pen_style={pen_style}',
                'QMapPermalink', Qgis.Info
            )
        except Exception:
            pass

        # convert QColor-like to hex if possible
        def _color_name(c):
            try:
                if c is None:
                    return None
                if hasattr(c, 'name') and c.isValid():
                    return c.name()
                return str(c)
            except Exception:
                return None

        fill_color = _color_name(color)
        stroke_color = _color_name(stroke_color)

        if geom_type == 'Point':
            if size is None:
                size = 6
            fc = _escape_xml(fill_color or '#000000')
            sc = _escape_xml(stroke_color or '#000000')
            
            # Determine WellKnownName from point_shape
            well_known_name = 'circle'  # default
            if point_shape is not None:
                try:
                    from qgis.core import QgsSimpleMarkerSymbolLayerBase
                    shape_map = {
                        QgsSimpleMarkerSymbolLayerBase.Square: 'square',
                        QgsSimpleMarkerSymbolLayerBase.Diamond: 'square',  # rotated square
                        QgsSimpleMarkerSymbolLayerBase.Pentagon: 'circle',  # no direct equivalent
                        QgsSimpleMarkerSymbolLayerBase.Hexagon: 'circle',  # no direct equivalent
                        QgsSimpleMarkerSymbolLayerBase.Triangle: 'triangle',
                        QgsSimpleMarkerSymbolLayerBase.Star: 'star',
                        QgsSimpleMarkerSymbolLayerBase.Cross: 'cross',
                        QgsSimpleMarkerSymbolLayerBase.Cross2: 'x',
                        QgsSimpleMarkerSymbolLayerBase.Circle: 'circle',
                    }
                    if point_shape in shape_map:
                        well_known_name = shape_map[point_shape]
                except Exception:
                    pass
            
            return (
                f'<PointSymbolizer>\n'
                f'  <Graphic>\n'
                f'    <Mark>\n'
                f'      <WellKnownName>{well_known_name}</WellKnownName>\n'
                f'      <Fill><CssParameter name="fill">{fc}</CssParameter></Fill>\n'
                f'      <Stroke><CssParameter name="stroke">{sc}</CssParameter>\n'
                f'      <CssParameter name="stroke-width">1</CssParameter></Stroke>\n'
                f'    </Mark>\n'
                f'    <Size>{size}</Size>\n'
                f'  </Graphic>\n'
                f'</PointSymbolizer>\n'
            )

        if geom_type == 'LineString':
            # Build stroke parameters using common function
            stroke_params = _build_stroke_params(
                stroke_color, stroke_width or 2, stroke_opacity,
                pen_join_style, pen_cap_style, pen_style
            )

            return (
                f'<LineSymbolizer>\n'
                f'  <Stroke>\n'
                f'{stroke_params}'
                f'  </Stroke>\n'
                f'</LineSymbolizer>\n'
            )

        # Polygon
        fo = opacity if (opacity is not None) else 1.0
        
        # Check if the fill should be included (ブラシなし detection)
        # has_brush was determined earlier by checking brushStyle and alpha
        has_fill = bool(has_brush) and (fill_color is not None) and (fo is None or float(fo) > 0)
        # Diagnostics: log decision inputs
        try:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(
                f"🧪 Polygon fill decision: fill_color={fill_color}, opacity={opacity}, has_brush={has_brush}, has_fill={has_fill}",
                "QMapPermalink", Qgis.Info
            )
        except Exception:
            pass
        # fill-opacityが0ならhas_fill=False
        if has_fill and opacity is not None:
            try:
                if float(opacity) == 0:
                    has_fill = False
            except Exception:
                pass

        # Build stroke parameters using common function (always build for both branches)
        stroke_params = _build_stroke_params(
            stroke_color, stroke_width or 1, stroke_opacity, 
            pen_join_style, pen_cap_style, pen_style
        )
        
        # Build PolygonSymbolizer with conditional Fill
        if has_fill:
            fc = _escape_xml(fill_color)
            return (
                f'<PolygonSymbolizer>\n'
                f'  <Fill>\n'
                f'    <CssParameter name="fill">{fc}</CssParameter>\n'
                f'    <CssParameter name="fill-opacity">{fo}</CssParameter>\n'
                f'  </Fill>\n'
                f'  <Stroke>\n'
                f'{stroke_params}'
                f'  </Stroke>\n'
                f'</PolygonSymbolizer>\n'
            )
        else:
            # ブラシなし: Fill要素を省略し、Strokeのみ
            # LineSymbolizerを返してポリゴンの枠線のみ描画
            return (
                f'<LineSymbolizer>\n'
                f'  <Stroke>\n'
                f'{stroke_params}'
                f'  </Stroke>\n'
                f'</LineSymbolizer>\n'
            )
    except Exception:
        return ''


def _rule_xml(name: str, filter_xml: Optional[str], symbolizer_xml: str) -> str:
    nm = _escape_xml(name or '')
    filt = f'{filter_xml}\n' if filter_xml else ''
    return (
        f'        <Rule>\n'
        f'          <Name>{nm}</Name>\n'
        f'{filt}'
        f'{symbolizer_xml}'
        f'        </Rule>\n'
    )


def _filter_equal(field: str, value) -> str:
    return (
        f'          <ogc:Filter>\n'
        f'            <ogc:PropertyIsEqualTo>\n'
        f'              <ogc:PropertyName>{_escape_xml(field)}</ogc:PropertyName>\n'
        f'              <ogc:Literal>{_escape_xml(value)}</ogc:Literal>\n'
        f'            </ogc:PropertyIsEqualTo>\n'
        f'          </ogc:Filter>'
    )


def _filter_range(field: str, lower, upper) -> str:
    # Use And of >= lower and < upper (upper may be None meaning >= lower)
    if upper is None:
        return (
            f'          <ogc:Filter>\n'
            f'            <ogc:PropertyIsGreaterThanOrEqualTo>\n'
            f'              <ogc:PropertyName>{_escape_xml(field)}</ogc:PropertyName>\n'
            f'              <ogc:Literal>{_escape_xml(lower)}</ogc:Literal>\n'
            f'            </ogc:PropertyIsGreaterThanOrEqualTo>\n'
            f'          </ogc:Filter>'
        )
    return (
        f'          <ogc:Filter>\n'
        f'            <ogc:And>\n'
        f'              <ogc:PropertyIsGreaterThanOrEqualTo>\n'
        f'                <ogc:PropertyName>{_escape_xml(field)}</ogc:PropertyName>\n'
        f'                <ogc:Literal>{_escape_xml(lower)}</ogc:Literal>\n'
        f'              </ogc:PropertyIsGreaterThanOrEqualTo>\n'
        f'              <ogc:PropertyIsLessThan>\n'
        f'                <ogc:PropertyName>{_escape_xml(field)}</ogc:PropertyName>\n'
        f'                <ogc:Literal>{_escape_xml(upper)}</ogc:Literal>\n'
        f'              </ogc:PropertyIsLessThan>\n'
        f'            </ogc:And>\n'
        f'          </ogc:Filter>'
    )


def renderer_to_sld(layer, layer_name: Optional[str] = None) -> str:
    """Convert a layer.renderer() to an SLD string (best-effort).

    Returns a full SLD document string.
    """
    ln = layer_name or str(layer.id())
    renderer = layer.renderer()
    if renderer is None:
        # trivial default
        from qgis.core import QgsMessageLog, Qgis
        QgsMessageLog.logMessage(f"No renderer for layer {ln}, returning default SLD", "QMapPermalink", Qgis.Warning)
        return _sld_header(ln) + _rule_xml('default', None, _symbol_to_symbolizer(None, 'Polygon')) + _sld_footer()

    rules = []

    try:
        # Single symbol
        if isinstance(renderer, QgsSingleSymbolRenderer):
            sym = renderer.symbol()
            geom = getattr(sym, 'geometryType', None)
            # fallback: try to guess from layer geometry
            gtype = 'Polygon'
            try:
                if layer.geometryType() == 0:
                    gtype = 'Point'
                elif layer.geometryType() == 1:
                    gtype = 'LineString'
                else:
                    gtype = 'Polygon'
            except Exception:
                pass
            rules.append((_escape_xml('default'), None, _symbol_to_symbolizer(sym, gtype)))

        # Categorized
        elif isinstance(renderer, QgsCategorizedSymbolRenderer):
            field = ''
            try:
                field = renderer.classAttribute()
            except Exception:
                try:
                    field = renderer.attribute()
                except Exception:
                    field = ''
            try:
                cats = renderer.categories()
                for c in cats:
                    val = c.value()
                    label = c.label() or str(val)
                    sym = c.symbol()
                    # guess geom type from layer if possible
                    gtype = 'Polygon'
                    try:
                        if layer.geometryType() == 0:
                            gtype = 'Point'
                        elif layer.geometryType() == 1:
                            gtype = 'LineString'
                    except Exception:
                        pass
                    filt = _filter_equal(field, val) if field else None
                    rules.append((label, filt, _symbol_to_symbolizer(sym, gtype)))
            except Exception:
                pass

        # Graduated
        elif isinstance(renderer, QgsGraduatedSymbolRenderer):
            field = ''
            try:
                field = renderer.classAttribute()
            except Exception:
                try:
                    field = renderer.attribute()
                except Exception:
                    field = ''
            try:
                ranges = renderer.ranges()
                for r in ranges:
                    lab = r.label() or f"{r.lowerValue()} - {r.upperValue()}"
                    sym = r.symbol()
                    gtype = 'Polygon'
                    try:
                        if layer.geometryType() == 0:
                            gtype = 'Point'
                        elif layer.geometryType() == 1:
                            gtype = 'LineString'
                    except Exception:
                        pass
                    filt = None
                    if field:
                        # upper may be None
                        lower = r.lowerValue()
                        upper = r.upperValue()
                        filt = _filter_range(field, lower, upper)
                    rules.append((lab, filt, _symbol_to_symbolizer(sym, gtype)))
            except Exception:
                pass

        # Rule based
        elif isinstance(renderer, QgsRuleBasedRenderer):
            try:
                root = renderer.rootRule()
                def walk(rule):
                    res = []
                    # rule may have a symbol
                    try:
                        sym = rule.symbol()
                    except Exception:
                        sym = None
                    try:
                        label = rule.label() or ''
                    except Exception:
                        label = ''
                    try:
                        expr = rule.filterExpression() or ''
                    except Exception:
                        expr = ''
                    # convert expression into a naive ogc filter if simple 'field = value'
                    filt = None
                    if expr:
                        # naive parsing: look for = operator
                        m = expr.split('=')
                        if len(m) == 2:
                            field = m[0].strip().strip('"')
                            val = m[1].strip().strip('\'"')
                            filt = _filter_equal(field, val)
                    # guess geom type
                    gtype = 'Polygon'
                    try:
                        if layer.geometryType() == 0:
                            gtype = 'Point'
                        elif layer.geometryType() == 1:
                            gtype = 'LineString'
                    except Exception:
                        pass
                    if sym is not None:
                        res.append((label, filt, _symbol_to_symbolizer(sym, gtype)))
                    # children
                    try:
                        for child in rule.children():
                            res.extend(walk(child))
                    except Exception:
                        pass
                    return res

                for child in root.children():
                    rules.extend(walk(child))
            except Exception:
                pass

        # Fallback: try symbolForFeature via renderer if nothing produced
        if not rules:
            try:
                from qgis.core import QgsRenderContext, QgsExpressionContext, QgsExpressionContextUtils, QgsFeature
                ctx = QgsRenderContext()
                ctx.setExpressionContext(QgsExpressionContext())
                ctx.expressionContext().appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
                dummy = QgsFeature()
                ctx.expressionContext().setFeature(dummy)
                sym = renderer.symbolForFeature(dummy, ctx)
                gtype = 'Polygon'
                try:
                    if layer.geometryType() == 0:
                        gtype = 'Point'
                    elif layer.geometryType() == 1:
                        gtype = 'LineString'
                except Exception:
                    pass
                rules.append(('default', None, _symbol_to_symbolizer(sym, gtype)))
            except Exception:
                pass

    except Exception:
        # any error -> return empty default
        return _sld_header(ln) + _rule_xml('default', None, _symbol_to_symbolizer(None, 'Polygon')) + _sld_footer()

    # assemble SLD
    body = _sld_header(ln)
    for name, filt, symxml in rules:
        body += _rule_xml(name, filt, symxml)
    body += _sld_footer()
    return body
