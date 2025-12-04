# -*- coding: utf-8 -*-
"""
Lightweight WMTS-like service for geo_webview.

This module provides a small class that handles /wmts requests and
delegates actual rendering to the server manager's existing WMS
GetMap-with-BBOX pipeline. The class is intentionally small to avoid
duplicate rendering code and to prevent circular imports: it expects
to receive the server manager instance at construction time.
"""
import re
import os
import tempfile
import hashlib
import json
import concurrent.futures
import threading


class GeoWebViewWMTSService:
    """Simple WMTS-like handler that maps XYZ tiles to a WMS GetMap BBOX.

    The service does not implement a full WMTS server — just a minimal
    GetCapabilities response and XYZ tile URL pattern /wmts/{z}/{x}/{y}.png
    which it translates into an EPSG:3857 BBOX and calls the server
    manager's _handle_wms_get_map_with_bbox method.
    """

    def __init__(self, server_manager):
        self.server_manager = server_manager
        # Configurable defaults (CPU-derived defaults; environment variables not used for render worker counts)
        # Prefer a computed default based on CPU count; enforce a sensible minimum for parallelism.
        try:
            cpu_count = os.cpu_count()
        except Exception:
            cpu_count = None
        if not cpu_count:
            cpu_count = 8
        # max_render_workers: cpu_count - 1, but at least 6
        try:
            self.max_render_workers = max(6, max(1, int(cpu_count) - 1))
        except Exception:
            self.max_render_workers = 6
        self.max_io_workers = int(os.environ.get('QMAP_MAX_IO_WORKERS', 20))
        self.request_timeout_s = int(os.environ.get('QMAP_REQUEST_TIMEOUT_S', 10))
        self.retry_count = int(os.environ.get('QMAP_RETRY_COUNT', 2))
        # tile size (default 256)
        self.tile_size = int(os.environ.get('QMAP_TILE_SIZE', 256))
        # cache directory for WMTS tiles
        self.cache_dir = os.path.join(os.path.dirname(__file__), os.environ.get('QMAP_CACHE_DIR', '.cache'), 'wmts')
        # Maximum allowed zoom to avoid absurd requests (sane default)
        self._max_zoom = 30
        # small cache to avoid noisy repeated identity writes
        self._last_identity_hash = None
        # track style manager objects we've connected to so we don't double-connect
        # store the actual objects (not their id) to keep a strong reference
        # and avoid the signal object being garbage-collected.
        self._watched_style_managers = set()
        # guard to avoid re-entrant identity writes when reacting to signals
        self._writing_identity = False
        # Thread pool for parallel tile pre-generation (prewarm)
        # max_workers: use detected CPU count, fallback to 8 when unknown
        try:
            cpu_count = os.cpu_count()
        except Exception:
            cpu_count = None
        if not cpu_count:
            cpu_count = 8

        # Determine prewarm worker count.
        # Use CPU-derived value: cpu_count() - 1, but enforce a sensible lower bound
        # to ensure prewarm has reasonable parallelism on small CPU counts.
        # Final policy: prewarm_workers = max(6, cpu_count() - 1)
        try:
            cpu_count = os.cpu_count()
        except Exception:
            cpu_count = None
        if not cpu_count:
            cpu_count = 8

        try:
            prewarm_workers = max(6, max(1, int(cpu_count) - 1))
        except Exception:
            prewarm_workers = 6

        # Thread pool for prewarm tasks
        self._prewarm_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=prewarm_workers,
            thread_name_prefix='WMTS-Prewarm'
        )

        # Log the configured prewarm worker count at startup for diagnostics
        try:
            from qgis.core import QgsMessageLog, Qgis
            max_rw = str(self.max_render_workers) if getattr(self, 'max_render_workers', None) is not None else 'None'
            cpu_val = str(cpu_count) if cpu_count is not None else 'unknown'
            QgsMessageLog.logMessage(
                f"WMTS Prewarm workers: {prewarm_workers} (computed: cpu_count()-1, enforced min=6; max_render_workers={max_rw}, cpu_count={cpu_val})",
                'QMapPermalink', Qgis.Info
            )
        except Exception:
            # best-effort logging; ignore if QGIS logging not available
            pass
        self._prewarm_futures = []
        self._prewarm_lock = threading.Lock()
        self._is_prewarming = False

    def _on_style_changed(self, *args, **kwargs):
        """Signal handler called when a layer's current style changes.

        Clears the short-circuit cache and triggers ensure_identity to
        rewrite the identity meta so WMTS cache keys update.
        """
        try:
            # clear last cached hash so next ensure_identity will write
            self._last_identity_hash = None
            # style change detected; background identity recompute will run.
            # Avoid recursion: set a guard while we call ensure_identity
            if not getattr(self, '_writing_identity', False):
                try:
                    self._writing_identity = True
                    # best-effort: attempt to compute and write identity now
                    try:
                        identity_short, identity_raw = self._get_identity_info()
                        self.ensure_identity(identity_short, identity_raw)
                    except Exception:
                        # swallow; this is a best-effort background reaction
                        pass
                finally:
                    self._writing_identity = False
        except Exception:
            pass

    def _ensure_watch_style_managers(self):
        """Scan current project layers and connect to their style manager
        currentStyleChanged signal (if available) so we get notified when
        the user switches styles.

        This is safe to call multiple times; connections are tracked.
        """
        try:
            from qgis.core import QgsProject
            proj = QgsProject.instance()
            if not proj:
                return
            layers = proj.mapLayers().values()
        except Exception:
            # fallback: try server_manager canvas layers
            try:
                canvas = getattr(self.server_manager, 'map_canvas', None) or getattr(self.server_manager, 'canvas', None)
                layers = canvas.layers() if canvas and hasattr(canvas, 'layers') else []
            except Exception:
                layers = []

        for lyr in list(layers):
            try:
                sm_attr = getattr(lyr, 'styleManager', None)
                sm = None
                if callable(sm_attr):
                    try:
                        sm = sm_attr()
                    except Exception:
                        sm = None
                else:
                    sm = sm_attr
                if not sm:
                    continue
                # track by object to keep a reference (prevent GC) and
                # avoid duplicate connects
                if sm in self._watched_style_managers:
                    continue
                # connect to currentStyleChanged if available
                sig = getattr(sm, 'currentStyleChanged', None)
                if sig and hasattr(sig, 'connect'):
                    try:
                        sig.connect(self._on_style_changed)
                        # keep sm itself in the set to hold a reference
                        self._watched_style_managers.add(sm)
                    except Exception:
                        # ignore failures to connect
                        pass
            except Exception:
                continue

    def _extract_style_id(self, layer_obj):
        """Attempt to extract a stable style identifier from a QGIS layer object.

        The function tries several common APIs across QGIS versions and layer
        types and returns a string (or empty string if nothing found).
        """
        # Only use the style manager's explicit currentStyleId if available.
        # Per request, no fallbacks: if currentStyleId is not present, return ''
        try:
            if layer_obj is None:
                return ''
            sm_attr = getattr(layer_obj, 'styleManager', None)
            sm = None
            if callable(sm_attr):
                try:
                    sm = sm_attr()
                except Exception:
                    sm = None
            else:
                sm = sm_attr
            if sm is None:
                return ''
            # Use a single, reliable attribute to avoid complexity: prefer
            # `currentStyle` (observed in many QGIS versions). If absent or
            # empty, return empty string. Do not attempt multiple fallbacks.
            try:
                val = getattr(sm, 'currentStyle', None)
                if val is None:
                    return ''
                if callable(val):
                    try:
                        v = val()
                    except Exception:
                        v = None
                else:
                    v = val
                return str(v) if v else ''
            except Exception:
                return ''
        except Exception:
            return ''

    def _tile_xyz_to_bbox(self, z, x, y):
        """Convert XYZ tile coordinates to WebMercator bbox string.

        Returns: string "minx,miny,maxx,maxy"
        """
        origin = 20037508.342789244
        tiles = 2 ** z
        tile_size = (origin * 2) / tiles
        minx = -origin + x * tile_size
        maxx = -origin + (x + 1) * tile_size
        maxy = origin - y * tile_size
        miny = origin - (y + 1) * tile_size
        return f"{minx},{miny},{maxx},{maxy}"

    def _validate_tile_coords(self, z, x, y):
        """Validate XYZ tile coordinates.

        Returns (True, '') on success, or (False, error_message) on failure.
        """
        try:
            z = int(z)
            x = int(x)
            y = int(y)
        except Exception:
            return False, 'Invalid tile coordinates (not integers)'
        if z < 0 or z > int(self._max_zoom):
            return False, f'Zoom level {z} out of allowed range 0..{self._max_zoom}'
        max_index = (2 ** z) - 1
        if x < 0 or x > max_index or y < 0 or y > max_index:
            return False, f'Tile coordinates out of range for z={z} (0..{max_index})'
        return True, ''

    def get_identity_diagnostics(self):
        """Return a dict with diagnostic info about layer-tree and canvas layers.

        This helper is intended for interactive debugging from the QGIS
        Python console. It does not modify cache or files.
        """
        diag = {
            'canvas_present': False,
            'layer_tree_root_present': False,
            'lnode_count': None,
            'sample_layernode_ids': None,
            'constructed_layers_info_count': None,
            'constructed_layers_info_sample': None,
            'canvas_layers_count': None,
            'canvas_sample_ids': None,
            'server_manager_theme_attrs': None,
        }
        try:
            canvas = getattr(self.server_manager, 'map_canvas', None) or getattr(self.server_manager, 'canvas', None)
            if (not canvas) and hasattr(self.server_manager, 'iface'):
                try:
                    canvas = self.server_manager.iface.mapCanvas()
                except Exception:
                    canvas = None
            diag['canvas_present'] = bool(canvas)

            try:
                from qgis.core import QgsProject
                root = QgsProject.instance().layerTreeRoot()
            except Exception:
                root = None
            diag['layer_tree_root_present'] = bool(root)

            # layer-tree nodes
            try:
                lnodes = []
                if root is not None:
                    try:
                        lnodes = root.findLayers()
                    except Exception:
                        try:
                            for ch in root.children():
                                if hasattr(ch, 'layerId'):
                                    lnodes.append(ch)
                        except Exception:
                            lnodes = []
                try:
                    diag['lnode_count'] = len(lnodes)
                except Exception:
                    diag['lnode_count'] = sum(1 for _ in lnodes) if hasattr(lnodes, '__iter__') else None
                sample = []
                for n in (lnodes[:10] if hasattr(lnodes, '__getitem__') else list(lnodes)[:10]):
                    try:
                        lid = None
                        try:
                            lid = n.layerId()
                        except Exception:
                            lid = getattr(n, 'layerId', None)
                            if callable(lid):
                                try:
                                    lid = lid()
                                except Exception:
                                    lid = None
                        sample.append(lid)
                    except Exception:
                        sample.append(None)
                diag['sample_layernode_ids'] = sample
            except Exception:
                pass

            # attempt to build layers_info via layer-tree path (but don't stop on failure)
            try:
                layers_info = []
                if root is not None and diag.get('lnode_count'):
                    from qgis.core import QgsProject as _QProj
                    for idx, lnode in enumerate(lnodes):
                        try:
                            lid = None
                            try:
                                lid = lnode.layerId()
                            except Exception:
                                lid = getattr(lnode, 'layerId', None)
                            if not lid:
                                continue
                            layer_obj = _QProj.instance().mapLayer(lid)
                            if not layer_obj:
                                continue

                            # source: call if callable, else stringify safely
                            try:
                                src_attr = getattr(layer_obj, 'source', None)
                                if callable(src_attr):
                                    try:
                                        src_val = src_attr()
                                    except Exception:
                                        try:
                                            src_val = str(src_attr)
                                        except Exception:
                                            src_val = ''
                                else:
                                    src_val = str(src_attr) if src_attr is not None else ''
                            except Exception:
                                src_val = ''

                            # style id extraction (use centralized helper)
                            style_id = self._extract_style_id(layer_obj)

                            # visibility
                            try:
                                vis = bool(lnode.isVisible()) if hasattr(lnode, 'isVisible') else False
                            except Exception:
                                vis = False

                            info = {
                                'order': idx,
                                'id': layer_obj.id(),
                                'source': src_val or '',
                                'style_id': style_id,
                                'visible': bool(vis),
                            }
                            layers_info.append(info)
                        except Exception:
                            continue
                diag['constructed_layers_info_count'] = len(layers_info)
                diag['constructed_layers_info_sample'] = layers_info[:5]
            except Exception:
                pass

            # canvas.layers() info
            try:
                if canvas and hasattr(canvas, 'layers'):
                    layer_objs = canvas.layers()
                    try:
                        diag['canvas_layers_count'] = len(layer_objs)
                    except Exception:
                        diag['canvas_layers_count'] = sum(1 for _ in layer_objs) if hasattr(layer_objs, '__iter__') else None
                    sample = []
                    for li in (layer_objs[:10] if hasattr(layer_objs, '__getitem__') else list(layer_objs)[:10]):
                        try:
                            lid = None
                            try:
                                lid = li.id()
                            except Exception:
                                lid = getattr(li, 'source', None) or getattr(li, 'name', None) or str(li)
                            sample.append(lid)
                        except Exception:
                            sample.append(None)
                    diag['canvas_sample_ids'] = sample
            except Exception:
                pass

            # server_manager theme attrs
            try:
                avail = {attr: (getattr(self.server_manager, attr, None) is not None) for attr in ('current_theme', 'active_theme', 'theme', 'selected_theme')}
                diag['server_manager_theme_attrs'] = avail
            except Exception:
                diag['server_manager_theme_attrs'] = None

        except Exception:
            pass
        # intentionally quiet: return diagnostics without logging
        return diag

    def handle_wmts_request(self, conn, parsed_url, params, host=None):
        """Handle an incoming /wmts request.

        Args:
            conn: socket connection
            parsed_url: result of urllib.parse.urlparse(target)
            params: dict from urllib.parse.parse_qs
            host: Host header value (optional)
        """
        try:
            # Ensure local tile vars exist so early returns (e.g. GetCapabilities)
            # don't trigger UnboundLocalError when `z` is assigned later in
            # the function scope.
            z = x = y = None

            # Accept WMTS GetCapabilities via REQUEST=GetCapabilities or SERVICE=WMTS (without other REQUEST)
            req = params.get('REQUEST', [params.get('request', [''])[0]])[0] if params else ''
            svc = params.get('SERVICE', [params.get('service', [''])[0]])[0] if params else ''
            
            # Handle GetCapabilities explicitly
            # Treat either explicit REQUEST=GetCapabilities or SERVICE=WMTS (with no REQUEST)
            if (req and str(req).upper() == 'GETCAPABILITIES') or (not req and svc and str(svc).upper() == 'WMTS'):
                try:
                    server_port = self.server_manager.http_server.getsockname()[1] if self.server_manager.http_server else self.server_manager.server_port
                except Exception:
                    server_port = self.server_manager.server_port
                if not host:
                    host = f'localhost:{server_port}'

    
                # Provide both a simple template URL and a WMTS ResourceURL entry to help clients
                # Include the current identity short so clients can detect when the
                # visible layers / styles have changed. The GetCapabilities handler
                # runs in the server context and can compute the identity via
                # _get_identity_info(). Use str.format with doubled braces so the
                # template placeholders remain literal in the XML.
                try:
                    identity_short, identity_raw = self._get_identity_info()
                except Exception:
                    identity_short = None

                # Append identity as a simple cache-busting query parameter when
                # available. Clients that parse the GetCapabilities can read the
                # template including ?v=<identity_short> to know the current hash.
                vqs = (f"?v={identity_short}" if identity_short else "")

                # Prefer explicit host passed to handler. If not provided, fall
                # back to server manager detection; default to localhost:8089.
                if not host:
                    try:
                        server_port = self.server_manager.http_server.getsockname()[1] if self.server_manager.http_server else self.server_manager.server_port
                    except Exception:
                        server_port = getattr(self.server_manager, 'server_port', 8089)
                    host = f'localhost:{server_port or 8089}'

                # New ResourceURL template: {Style}/{TileMatrixSet}/{TileMatrix}/{TileRow}/{TileCol}.{Format}
                # Use literal braces in the template so clients can substitute tokens.
                tile_url = ("http://{host}/wmts/{{Style}}/{{TileMatrixSet}}/{{TileMatrix}}/{{TileRow}}/{{TileCol}}.{{Format}}" + vqs).format(host=host)
                tile_url_template = ("http://{host}/wmts/{{Style}}/{{TileMatrixSet}}/{{TileMatrix}}/{{TileRow}}/{{TileCol}}.{{Format}}" + vqs).format(host=host)
                # Also advertise a dedicated XYZ endpoint for clients that prefer
                # a canonical /xyz/{z}/{x}/{y}.png path. This endpoint is handled
                # by the same WMTS tile logic below (the tile regex accepts both
                # /wmts and /xyz prefixes).
                xyz_tile_url = ("http://{host}/xyz/{{z}}/{{x}}/{{y}}.png" + vqs).format(host=host)
                # Escape characters that must be XML-escaped when included
                # inside attribute values (notably '&' in querystrings).
                try:
                    from xml.sax import saxutils
                    tile_url_template_esc = saxutils.escape(tile_url_template, {'"': '&quot;'})
                    service_metadata_href = f"http://{host}/wmts?SERVICE=WMTS&REQUEST=GetCapabilities"
                    service_metadata_href_esc = saxutils.escape(service_metadata_href, {'"': '&quot;'})
                    # escape the xyz template as well
                    xyz_tile_url_template_esc = saxutils.escape(xyz_tile_url, {'"': '&quot;'})
                    # Also provide a classic matrix/row/col ordered template for broader client compatibility
                    matrix_order_template = (f"http://{host}/wmts/{{TileMatrix}}/{{TileRow}}/{{TileCol}}.png" + vqs)
                    matrix_order_template_esc = saxutils.escape(matrix_order_template, {'"': '&quot;'})
                except Exception:
                    # fallback: naive replace for ampersand
                    tile_url_template_esc = tile_url_template.replace('&', '&amp;')
                    service_metadata_href_esc = (f"http://{host}/wmts?SERVICE=WMTS&REQUEST=GetCapabilities").replace('&', '&amp;')
                    xyz_tile_url_template_esc = xyz_tile_url.replace('&', '&amp;')
                    matrix_order_template_esc = matrix_order_template.replace('&', '&amp;')

                # Build TileMatrix entries for each zoom level (0.._max_zoom)
                origin = 20037508.342789244
                full_width = origin * 2
                tile_size = 256
                initial_resolution = full_width / tile_size
                tile_matrices_entries = []
                tile_matrix_limits_entries = []
                for zlevel in range(0, self._max_zoom + 1):
                    matrix_width = 2 ** zlevel
                    matrix_height = matrix_width
                    resolution = initial_resolution / (2 ** zlevel)
                    # scaleDenominator = resolution / 0.00028 (pixel size 0.28 mm)
                    scale_denominator = resolution / 0.00028
                    tile_matrices_entries.append(
                        f"      <TileMatrix>\n"
                        f"        <Identifier>{zlevel}</Identifier>\n"
                        f"        <ScaleDenominator>{scale_denominator:.6f}</ScaleDenominator>\n"
                        f"        <TopLeftCorner>{-origin} {origin}</TopLeftCorner>\n"
                        f"        <TileWidth>{tile_size}</TileWidth>\n"
                        f"        <TileHeight>{tile_size}</TileHeight>\n"
                        f"        <MatrixWidth>{matrix_width}</MatrixWidth>\n"
                        f"        <MatrixHeight>{matrix_height}</MatrixHeight>\n"
                        f"      </TileMatrix>"
                    )
                    # TileMatrixLimits for this zoom level (0..matrix_width-1, 0..matrix_height-1)
                    tile_matrix_limits_entries.append(
                        f"        <TileMatrixLimits>\n"
                        f"          <TileMatrix>\n"
                        f"            <ows:Identifier>{zlevel}</ows:Identifier>\n"
                        f"          </TileMatrix>\n"
                        f"          <MinTileRow>0</MinTileRow>\n"
                        f"          <MaxTileRow>{matrix_height - 1}</MaxTileRow>\n"
                        f"          <MinTileCol>0</MinTileCol>\n"
                        f"          <MaxTileCol>{matrix_width - 1}</MaxTileCol>\n"
                        f"        </TileMatrixLimits>"
                    )

                tile_matrices_xml = "\n".join(tile_matrices_entries)
                tile_matrix_limits_xml = "\n".join(tile_matrix_limits_entries)

                # Build per-layer Contents entries: enumerate project/canvas layers
                layers_xml = ''
                try:
                    from qgis.core import QgsProject
                    proj = QgsProject.instance()
                    layer_objs = []
                    if proj:
                        try:
                            lnodes = proj.layerTreeRoot().findLayers()
                            for ln in lnodes:
                                try:
                                    lid = ln.layerId() if hasattr(ln, 'layerId') else None
                                except Exception:
                                    lid = None
                                if not lid:
                                    continue
                                lyr = proj.mapLayer(lid)
                                if lyr:
                                    layer_objs.append(lyr)
                        except Exception:
                            layer_objs = list(proj.mapLayers().values())
                    if not layer_objs:
                        canvas = getattr(self.server_manager, 'map_canvas', None) or getattr(self.server_manager, 'canvas', None)
                        if canvas and hasattr(canvas, 'layers'):
                            try:
                                layer_objs = canvas.layers()
                            except Exception:
                                layer_objs = []
                except Exception:
                    layer_objs = []

                def _layer_entry(layer_obj):
                    try:
                        lid = getattr(layer_obj, 'id', None)
                        if callable(lid):
                            lid = lid()
                        else:
                            lid = str(lid)
                    except Exception:
                        lid = 'layer'
                    try:
                        lname = getattr(layer_obj, 'name', None)
                        if callable(lname):
                            lname = lname()
                        lname = str(lname) if lname else lid
                    except Exception:
                        lname = lid
                    entry = (
                        f"        <Layer>\n"
                        f"            <ows:Title>{lname}</ows:Title>\n"
                        f"            <ows:Identifier>{lid}</ows:Identifier>\n"
                        f"            <ows:WGS84BoundingBox>\n"
                        f"                <ows:LowerCorner>-180 -85.0511287798066</ows:LowerCorner>\n"
                        f"                <ows:UpperCorner>180 85.0511287798066</ows:UpperCorner>\n"
                        f"            </ows:WGS84BoundingBox>\n"
                        f"            <Style isDefault=\"true\">\n"
                        f"                <ows:Identifier>default</ows:Identifier>\n"
                        f"            </Style>\n"
                        f"            <Format>image/png</Format>\n"
                        f"            <Format>image/jpeg</Format>\n"
                        f"            <TileMatrixSetLink>\n"
                        f"                <TileMatrixSet>EPSG:3857</TileMatrixSet>\n"
                        f"                <TileMatrixSetLimits>\n{tile_matrix_limits_xml}\n"
                        f"                </TileMatrixSetLimits>\n"
                        f"            </TileMatrixSetLink>\n"
                        f"            <ResourceURL resourceType=\"tile\" format=\"image/png\" width=\"256\" height=\"256\" template=\"{tile_url_template_esc}\"/>\n"
                        f"            <ResourceURL resourceType=\"tile\" format=\"image/png\" width=\"256\" height=\"256\" template=\"{matrix_order_template_esc}\"/>\n"
                        f"            <!-- Also provide a simple XYZ endpoint for convenience: /xyz/{{z}}/{{x}}/{{y}}.png -->\n"
                        f"            <ResourceURL resourceType=\"tile\" format=\"image/png\" width=\"256\" height=\"256\" template=\"{xyz_tile_url_template_esc}\"/>\n"
                        f"        </Layer>"
                    )
                    return entry

                if layer_objs:
                    try:
                        for lyr in layer_objs:
                            try:
                                layers_xml += _layer_entry(lyr) + '\n'
                            except Exception:
                                continue
                    except Exception:
                        layers_xml = ''
                else:
                    layers_xml = (
                        "        <Layer>\n"
                        "            <ows:Title>QMap</ows:Title>\n"
                        "            <ows:Identifier>qgis_map</ows:Identifier>\n"
                        "            <ows:WGS84BoundingBox>\n"
                        "                <ows:LowerCorner>-180 -85.0511287798066</ows:LowerCorner>\n"
                        "                <ows:UpperCorner>180 85.0511287798066</ows:UpperCorner>\n"
                        "            </ows:WGS84BoundingBox>\n"
                        "            <Style isDefault=\"true\">\n"
                        "                <ows:Identifier>default</ows:Identifier>\n"
                        "            </Style>\n"
                        "            <Format>image/png</Format>\n"
                        "            <Format>image/jpeg</Format>\n"
                        "            <TileMatrixSetLink>\n"
                        "                <TileMatrixSet>EPSG:3857</TileMatrixSet>\n"
                        f"                <TileMatrixSetLimits>\n{tile_matrix_limits_xml}\n"
                        "                </TileMatrixSetLimits>\n"
                        "            </TileMatrixSetLink>\n"
                        f"            <ResourceURL resourceType=\"tile\" format=\"image/png\" width=\"256\" height=\"256\" template=\"{tile_url_template_esc}\"/>\n"
                        f"            <ResourceURL resourceType=\"tile\" format=\"image/png\" width=\"256\" height=\"256\" template=\"{matrix_order_template_esc}\"/>\n"
                        f"            <ResourceURL resourceType=\"tile\" format=\"image/png\" width=\"256\" height=\"256\" template=\"{xyz_tile_url_template_esc}\"/>\n"
                        "        </Layer>\n"
                    )

                # Build a more standards-oriented GetCapabilities response.
                xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Capabilities
    xmlns="http://www.opengis.net/wmts/1.0"
    xmlns:ows="http://www.opengis.net/ows/1.1"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.opengis.net/wmts/1.0 http://schemas.opengis.net/wmts/1.0/wmtsGetCapabilities_response.xsd http://www.opengis.net/ows/1.1 http://schemas.opengis.net/ows/1.1.0/owsAll.xsd"
    version="1.0.0">
    <ows:ServiceIdentification>
        <ows:Title>QMap</ows:Title>
        <ows:Abstract>Lightweight WMTS-like service generated by QMapPermalink</ows:Abstract>
        <ows:Keywords>
            <ows:Keyword>WMTS</ows:Keyword>
            <ows:Keyword>QMapPermalink</ows:Keyword>
        </ows:Keywords>
        <ows:ServiceType>OGC WMTS</ows:ServiceType>
        <ows:ServiceTypeVersion>1.0.0</ows:ServiceTypeVersion>
    </ows:ServiceIdentification>
    <ows:ServiceProvider>
        <ows:ProviderName>QMapPermalink</ows:ProviderName>
        <ows:ProviderSite xlink:href="https://github.com/yamamoto-ryuzo/QMapPermalink"/>
    </ows:ServiceProvider>
    <ows:OperationsMetadata>
        <ows:Operation name="GetCapabilities">
            <ows:DCP>
                <ows:HTTP>
                    <ows:Get xlink:href="http://{host}/wmts"/>
                </ows:HTTP>
            </ows:DCP>
            <ows:Parameter name="SERVICE"><ows:Value>WMTS</ows:Value></ows:Parameter>
            <ows:Parameter name="REQUEST"><ows:Value>GetCapabilities</ows:Value></ows:Parameter>
            <ows:Parameter name="VERSION"><ows:Value>1.0.0</ows:Value></ows:Parameter>
        </ows:Operation>
        <ows:Operation name="GetTile">
            <ows:DCP>
                <ows:HTTP>
                    <ows:Get xlink:href="http://{host}/wmts"/>
                </ows:HTTP>
            </ows:DCP>
            <ows:Parameter name="SERVICE"><ows:Value>WMTS</ows:Value></ows:Parameter>
            <ows:Parameter name="REQUEST"><ows:Value>GetTile</ows:Value></ows:Parameter>
            <ows:Parameter name="VERSION"><ows:Value>1.0.0</ows:Value></ows:Parameter>
            <ows:Parameter name="LAYER"><ows:Value>qgis_map</ows:Value></ows:Parameter>
            <ows:Parameter name="TILEMATRIXSET"><ows:Value>EPSG:3857</ows:Value></ows:Parameter>
            <ows:Parameter name="FORMAT"><ows:Value>image/png</ows:Value><ows:Value>image/jpeg</ows:Value></ows:Parameter>
        </ows:Operation>
    </ows:OperationsMetadata>
    <Contents>
{layers_xml}
        <TileMatrixSet>
            <ows:Identifier>EPSG:3857</ows:Identifier>
            <ows:SupportedCRS>urn:ogc:def:crs:EPSG::3857</ows:SupportedCRS>
{tile_matrices_xml}
        </TileMatrixSet>
    </Contents>
    <ServiceMetadataURL xlink:href="{service_metadata_href_esc}"/>
</Capabilities>'''
                from . import http_server
                http_server.send_http_response(conn, 200, 'OK', xml, 'text/xml; charset=utf-8')
                return

            # KVP GetTile handling: support REQUEST=GetTile&LAYER=...&TILEMATRIXSET=...&TILEMATRIX=...&TILEROW=...&TILECOL=...&FORMAT=...
            if req and str(req).upper() == 'GETTILE':
                try:
                    # case-insensitive param access with fallbacks
                    def getp(k):
                        return params.get(k, params.get(k.lower(), ['']))[0] if params else ''

                    layer_param = getp('LAYER')
                    tms_param = getp('TILEMATRIXSET')
                    tm_param = getp('TILEMATRIX')
                    tr_param = getp('TILEROW')
                    tc_param = getp('TILECOL')
                    fmt_param = getp('FORMAT') or 'image/png'
                    style_param = getp('STYLE') or getp('Style') or ''

                    # Normalize format to short ext
                    fmt_low = fmt_param.split('/')[-1].lower()
                    if fmt_low in ('png', 'image/png'):
                        fmt_ext = 'png'
                    elif fmt_low in ('jpeg', 'jpg', 'image/jpeg'):
                        fmt_ext = 'jpg'
                    else:
                        # best-effort: use last token
                        fmt_ext = fmt_low.split()[-1]

                    # Parse tilematrix index: try int(tm_param) or last colon-separated part
                    try:
                        z = int(tm_param)
                    except Exception:
                        try:
                            z = int(str(tm_param).split(':')[-1])
                        except Exception:
                            raise ValueError('Invalid TILEMATRIX')

                    try:
                        x = int(tc_param)
                        y = int(tr_param)
                    except Exception:
                        raise ValueError('Invalid TILEROW/TILECOL')

                    ok, msg = self._validate_tile_coords(z, x, y)
                    if not ok:
                        from . import http_server
                        http_server.send_http_response(conn, 400, 'Bad Request', msg, 'text/plain; charset=utf-8')
                        return

                    # compute bbox and delegate to WMS path
                    bbox = self._tile_xyz_to_bbox(z, x, y)

                    if hasattr(self.server_manager, '_handle_wms_get_map_with_bbox'):
                        class _CaptureConn:
                            def __init__(self):
                                self._buf = bytearray()
                            def sendall(self, b):
                                if isinstance(b, (bytes, bytearray)):
                                    self._buf.extend(b)
                            def close(self):
                                pass

                        cap = _CaptureConn()
                        # pass style via later params if supported by server_manager (best-effort)
                        try:
                            self.server_manager._handle_wms_get_map_with_bbox(cap, bbox, 'EPSG:3857', int(self.tile_size), int(self.tile_size), rotation=0.0, layers_param=layer_param or None)
                        except TypeError:
                            # older signature without layers_param
                            self.server_manager._handle_wms_get_map_with_bbox(cap, bbox, 'EPSG:3857', int(self.tile_size), int(self.tile_size), rotation=0.0)

                        raw = bytes(cap._buf)
                        sep = b"\r\n\r\n"
                        if sep in raw:
                            hdr, body = raw.split(sep, 1)
                            hdr_text = hdr.decode('utf-8', errors='ignore')
                            content_type = 'application/octet-stream'
                            for line in hdr_text.splitlines():
                                if line.lower().startswith('content-type:'):
                                    content_type = line.split(':', 1)[1].strip()
                                    break
                            if content_type.startswith('image'):
                                try:
                                    # attempt to cache tile similarly to REST path
                                    cache_dir = self.cache_dir
                                    identity_short, identity_raw = self._get_identity_info()
                                    identity_hash, identity_dir = self.ensure_identity(identity_short, identity_raw)
                                    tile_dir = os.path.join(identity_dir, str(z), str(x))
                                    os.makedirs(tile_dir, exist_ok=True)
                                    cache_path = os.path.join(tile_dir, f"{y}.{fmt_ext}")
                                    tmpfd, tmppath = tempfile.mkstemp(dir=identity_dir, suffix='.tmp')
                                    with os.fdopen(tmpfd, 'wb') as tfh:
                                        tfh.write(body)
                                    os.replace(tmppath, cache_path)
                                except Exception:
                                    pass
                            try:
                                conn.sendall(raw)
                            except Exception:
                                pass
                            return
                        else:
                            try:
                                conn.sendall(raw)
                            except Exception:
                                pass
                            return
                    else:
                        from . import http_server
                        http_server.send_http_response(conn, 500, 'Internal Server Error', 'WMS rendering method not available', 'text/plain; charset=utf-8')
                        return
                except Exception as e:
                    from . import http_server
                    http_server.send_http_response(conn, 400, 'Bad Request', f'GetTile KVP failed: {e}', 'text/plain; charset=utf-8')
                    return

            # Tile request patterns:
            # - Legacy /wmts/{z}/{x}/{y}.png or /xyz/{z}/{x}/{y}.png (kept for backward compatibility)
            # - New style-based: /wmts/{Style}/{TileMatrixSet}/{TileMatrix}/{TileRow}/{TileCol}.{Format}
            m_style = re.match(r'^/wmts/([^/]+)/([^/]+)/(\d+)/(\d+)/(\d+)\.(png|jpg|jpeg)$', parsed_url.path, flags=re.IGNORECASE)
            if m_style:
                # style, tileset, z, row, col
                style = m_style.group(1)
                tileset = m_style.group(2)
                z = int(m_style.group(3))
                row = int(m_style.group(4))
                col = int(m_style.group(5))
                fmt = m_style.group(6).lower()
                # Normalize fmt
                if fmt == 'jpeg':
                    fmt = 'jpg'
                x = col
                y = row
                # Accept any TileMatrixSet but prefer EPSG:3857 semantics
                # downstream expects EPSG:3857; we do not enforce here but
                # users should request EPSG:3857 TileMatrixSet for correct bbox mapping.
            else:
                # Legacy pattern: /wmts/{z}/{x}/{y}.png or /xyz/{z}/{x}/{y}.png
                m = re.match(r'^/(?:wmts|xyz)/(\d+)/(\d+)/(\d+)\.(png|jpg|jpeg)$', parsed_url.path, flags=re.IGNORECASE)
                if m:
                    z = int(m.group(1))
                    x = int(m.group(2))
                    y = int(m.group(3))
                    fmt = m.group(4).lower()
                    if fmt == 'jpeg':
                        fmt = 'jpg'
                else:
                    m = None
            if (m_style or m):

                # Detect TMS (bottom-left origin) flag in params (tms=1 or tms=true)
                tms_flag = False
                try:
                    tms_val = params.get('tms', params.get('TMS', ['0']))[0] if params else '0'
                    tms_flag = str(tms_val).lower() in ('1', 'true', 'yes')
                except Exception:
                    tms_flag = False

                # If TMS requested, invert y before validation and bbox computation
                if tms_flag:
                    try:
                        y = (2 ** z - 1) - y
                    except Exception:
                        pass

                ok, msg = self._validate_tile_coords(z, x, y)
                if not ok:
                    from . import http_server
                    http_server.send_http_response(conn, 400, 'Bad Request', msg, 'text/plain; charset=utf-8')
                    return

                # compute WebMercator bbox for XYZ tile (origin top-left)
                bbox = self._tile_xyz_to_bbox(z, x, y)

                try:
                    # Try cache first
                    try:
                        cache_dir = self.cache_dir
                        os.makedirs(cache_dir, exist_ok=True)
                        # extension/format is already determined for both patterns
                        if not fmt:
                            fmt = 'png'

                        # Determine a stable identity for the current layer/theme
                        identity_short, identity_raw = self._get_identity_info()
                        cache_key = f"{identity_short}:{fmt}:{z}/{x}/{y}"

                        # Ensure identity folder/meta exists (centralized)
                        try:
                            identity_hash, identity_dir = self.ensure_identity(identity_short, identity_raw)
                        except Exception:
                            identity_hash = hashlib.sha1(identity_raw.encode('utf-8')).hexdigest()
                            identity_dir = os.path.join(cache_dir, identity_hash)
                            try:
                                os.makedirs(identity_dir, exist_ok=True)
                            except Exception:
                                pass

                            cache_dir = self.cache_dir
                            os.makedirs(cache_dir, exist_ok=True)
                        # tile path: nested by z/x/y for easier inspection
                        tile_dir = os.path.join(identity_dir, str(z), str(x))
                        try:
                            os.makedirs(tile_dir, exist_ok=True)
                        except Exception:
                            pass

                        cache_path = os.path.join(tile_dir, f"{y}.{fmt}")
                        if os.path.exists(cache_path):
                            with open(cache_path, 'rb') as fh:
                                data = fh.read()
                            from . import http_server
                            content_type = 'image/png' if fmt == 'png' else f'image/{fmt}'
                            http_server.send_binary_response(conn, 200, 'OK', data, content_type)
                            return
                    except Exception:
                        pass

                    # Delegate to server manager's WMS GetMap-with-BBOX pipeline (256x256)
                    if hasattr(self.server_manager, '_handle_wms_get_map_with_bbox'):
                        class _CaptureConn:
                            def __init__(self):
                                self._buf = bytearray()
                            def sendall(self, b):
                                if isinstance(b, (bytes, bytearray)):
                                    self._buf.extend(b)
                            def close(self):
                                pass
                        cap = _CaptureConn()
                        self.server_manager._handle_wms_get_map_with_bbox(cap, bbox, 'EPSG:3857', int(self.tile_size), int(self.tile_size), rotation=0.0)
                    try:
                        raw = bytes(cap._buf)
                        sep = b"\r\n\r\n"
                        if sep in raw:
                            hdr, body = raw.split(sep, 1)
                            hdr_text = hdr.decode('utf-8', errors='ignore')
                            content_type = 'application/octet-stream'
                            for line in hdr_text.splitlines():
                                if line.lower().startswith('content-type:'):
                                    content_type = line.split(':', 1)[1].strip()
                                    break
                            if content_type.startswith('image'):
                                try:
                                    tmpfd, tmppath = tempfile.mkstemp(dir=identity_dir, suffix='.tmp')
                                    with os.fdopen(tmpfd, 'wb') as tfh:
                                        tfh.write(body)
                                    os.replace(tmppath, cache_path)
                                    # write sidecar metadata for easier inspection
                                    meta_path = cache_path + '.meta.json'
                                    try:
                                        with open(meta_path, 'w', encoding='utf-8') as mf:
                                            json.dump({
                                                'cache_key': cache_key,
                                                'identity_short': identity_short,
                                                'identity_raw': identity_raw,
                                                'format': fmt,
                                                'z': z,
                                                'x': x,
                                                'y': y,
                                                'path': cache_path,
                                            }, mf, ensure_ascii=False, indent=2)
                                    except Exception:
                                        pass
                                except Exception:
                                    try:
                                        if os.path.exists(tmppath):
                                            os.remove(tmppath)
                                    except Exception:
                                        pass
                            # forward the captured bytes to original conn
                            try:
                                conn.sendall(raw)
                            except Exception:
                                pass
                            return
                        else:
                            # not an HTTP response: just forward raw buffer
                            try:
                                conn.sendall(raw)
                            except Exception:
                                pass
                            return
                    except Exception as e:
                        from . import http_server
                        http_server.send_http_response(conn, 500, 'Internal Server Error', f'WMTS tile failed: {e}')
                    else:
                        raise RuntimeError('WMS rendering method not available on server manager')
                except Exception as e:
                    from . import http_server
                    http_server.send_http_response(conn, 500, 'Internal Server Error', f'WMTS tile failed: {e}')
                return

        except Exception as e:
            try:
                from . import http_server
                http_server.send_http_response(conn, 500, 'Internal Server Error', f'WMTS processing failed: {e}')
            except Exception:
                pass

    def ensure_identity(self, identity_short=None, identity_raw=None):
        """Ensure the identity folder/meta exists for the given identity.

        If identity_short/raw are omitted, compute from current canvas. This
        method is idempotent and safe to call from signal handlers; it will
        create the identity folder under .cache/wmts and write
        identity.meta.json if missing.

        Returns: (identity_hash, identity_dir) or (None, None) on error.
        """
        try:
            # Ensure we are watching style managers for changes so identity
            # can be recomputed when the user switches styles.
            try:
                self._ensure_watch_style_managers()
            except Exception:
                pass
            if not identity_short or not identity_raw:
                try:
                    identity_short, identity_raw = self._get_identity_info()
                except Exception:
                    return None, None

            cache_dir = self.cache_dir
            try:
                os.makedirs(cache_dir, exist_ok=True)
            except Exception:
                pass

            identity_hash = hashlib.sha1(identity_raw.encode('utf-8')).hexdigest()
            identity_dir = os.path.join(cache_dir, identity_hash)
            try:
                os.makedirs(identity_dir, exist_ok=True)
            except Exception:
                pass

            # write or update identity meta (overwrite if identity_raw changed)
            try:
                meta_index_path = os.path.join(identity_dir, 'identity.meta.json')
                write_meta = True
                if os.path.exists(meta_index_path):
                    try:
                        with open(meta_index_path, 'r', encoding='utf-8') as mf:
                            existing = json.load(mf)
                        if existing and isinstance(existing, dict) and existing.get('identity_raw') == identity_raw:
                            write_meta = False
                    except Exception:
                        write_meta = True
                if write_meta:
                    meta_index = {
                        'identity_short': identity_short,
                        'identity_raw': identity_raw,
                    }
                    with open(meta_index_path, 'w', encoding='utf-8') as mf:
                        json.dump(meta_index, mf, ensure_ascii=False, indent=2)
            except Exception:
                pass

            # Start prewarm in background if not already running
            try:
                self._maybe_start_prewarm(identity_short, identity_hash, identity_dir)
            except Exception:
                pass
            
            return identity_hash, identity_dir
        except Exception:
            return None, None

    def _maybe_start_prewarm(self, identity_short, identity_hash, identity_dir):
        """バックグラウンドでタイルキャッシュを事前生成(プリウォーム)する。
        
        この関数は既にプリウォーム中の場合は何もしない。
        よく使われるズームレベル(10-16)の中心タイルを並列生成してキャッシュする。
        """
        with self._prewarm_lock:
            if self._is_prewarming:
                return
            self._is_prewarming = True
        
        try:
            # Get current canvas extent to determine which tiles to prewarm
            try:
                canvas = getattr(self.server_manager, 'map_canvas', None) or \
                         getattr(self.server_manager, 'canvas', None)
                if not canvas and hasattr(self.server_manager, 'iface'):
                    canvas = self.server_manager.iface.mapCanvas()
                
                if not canvas:
                    return
                
                # Get canvas center in EPSG:3857
                from qgis.core import QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsProject
                extent = canvas.extent()
                canvas_crs = canvas.mapSettings().destinationCrs()
                target_crs = QgsCoordinateReferenceSystem('EPSG:3857')
                
                if canvas_crs != target_crs:
                    transform = QgsCoordinateTransform(canvas_crs, target_crs, QgsProject.instance())
                    center = extent.center()
                    center_3857 = transform.transform(center)
                else:
                    center_3857 = extent.center()
                
                # Determine zoom levels to prewarm (z=10-18 for extended coverage)
                zoom_levels = range(10, 19)  # z=10,11,12,13,14,15,16,17,18
                
                # Calculate tile coordinates for center at each zoom level
                tasks = []
                origin = 20037508.342789244
                
                for z in zoom_levels:
                    tiles = 2 ** z
                    tile_size = (origin * 2) / tiles
                    
                    # Calculate center tile coordinates
                    x = int((center_3857.x() + origin) / tile_size)
                    y = int((origin - center_3857.y()) / tile_size)
                    
                    # Clamp to valid range
                    x = max(0, min(x, tiles - 1))
                    y = max(0, min(y, tiles - 1))
                    
                    # Add center tile and surrounding 24 tiles (5x5 grid)
                    for dx in [-2, -1, 0, 1, 2]:
                        for dy in [-2, -1, 0, 1, 2]:
                            tx = x + dx
                            ty = y + dy
                            if 0 <= tx < tiles and 0 <= ty < tiles:
                                tasks.append((z, tx, ty, identity_short, identity_hash, identity_dir))
                
                # Submit tasks to thread pool
                from qgis.core import QgsMessageLog, Qgis
                QgsMessageLog.logMessage(
                    f"🚀 WMTS Prewarm: {len(tasks)}タイルを並列生成開始",
                    "geo_webview", Qgis.Info
                )
                
                for task in tasks:
                    future = self._prewarm_executor.submit(self._prewarm_tile, *task)
                    self._prewarm_futures.append(future)
                
            except Exception as e:
                from qgis.core import QgsMessageLog, Qgis
                QgsMessageLog.logMessage(
                    f"⚠️ WMTS Prewarm setup failed: {e}",
                    "geo_webview", Qgis.Warning
                )
        finally:
            # Reset flag after a delay
            def reset_flag():
                import time
                time.sleep(2)
                with self._prewarm_lock:
                    self._is_prewarming = False
            
            t = threading.Thread(target=reset_flag, daemon=True)
            t.start()
    
    def _prewarm_tile(self, z, x, y, identity_short, identity_hash, identity_dir):
        """1つのタイルをプリウォーム(事前生成)する。
        
        この関数はスレッドプールから呼ばれ、タイルが既にキャッシュに
        存在する場合はスキップする。
        """
        try:
            # Check if tile already exists in cache
            tile_dir = os.path.join(identity_dir, str(z), str(x))
            cache_path = os.path.join(tile_dir, f"{y}.png")
            
            if os.path.exists(cache_path):
                return  # Already cached
            
            # Create directory
            os.makedirs(tile_dir, exist_ok=True)
            
            # Calculate bbox for this tile
            origin = 20037508.342789244
            tiles = 2 ** z
            tile_size = (origin * 2) / tiles
            minx = -origin + x * tile_size
            maxx = -origin + (x + 1) * tile_size
            maxy = origin - y * tile_size
            miny = origin - (y + 1) * tile_size
            bbox = f"{minx},{miny},{maxx},{maxy}"
            
            # Render tile (delegate to server_manager's WMS method)
            if hasattr(self.server_manager, '_handle_wms_get_map_with_bbox'):
                class _CaptureConn:
                    def __init__(self):
                        self._buf = bytearray()
                    def sendall(self, b):
                        if isinstance(b, (bytes, bytearray)):
                            self._buf.extend(b)
                    def close(self):
                        pass
                
                cap = _CaptureConn()
                self.server_manager._handle_wms_get_map_with_bbox(
                    cap, bbox, 'EPSG:3857', int(self.tile_size), int(self.tile_size), rotation=0.0
                )
                
                # Parse response and cache if successful
                raw = bytes(cap._buf)
                sep = b"\r\n\r\n"
                if sep in raw:
                    _, body = raw.split(sep, 1)
                    
                    # Write to cache atomically
                    tmpfd, tmppath = tempfile.mkstemp(dir=identity_dir, suffix='.tmp')
                    with os.fdopen(tmpfd, 'wb') as tfh:
                        tfh.write(body)
                    os.replace(tmppath, cache_path)
                    
        except Exception as e:
            # Prewarm failures are non-critical, just log quietly
            try:
                from qgis.core import QgsMessageLog, Qgis
                QgsMessageLog.logMessage(
                    f"Prewarm tile {z}/{x}/{y} failed: {e}",
                    "geo_webview", Qgis.Warning
                )
            except Exception:
                pass
