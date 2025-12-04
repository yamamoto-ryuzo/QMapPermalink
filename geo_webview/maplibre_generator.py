def export_layer_geojson(layer, geojson_path="data.geojson"):
	"""
	QGISレイヤをGeoJSON形式でエクスポートする。
	geojson_path: 出力するGeoJSONファイルのパス
	"""
	try:
		from qgis.core import QgsVectorFileWriter, QgsCoordinateTransformContext
		# QGIS 3.x 以降推奨の書き出し方法
		options = QgsVectorFileWriter.SaveVectorOptions()
		options.driverName = "GeoJSON"
		options.fileEncoding = "UTF-8"
		# CRS変換なし（レイヤのCRSのまま出力）
		context = QgsCoordinateTransformContext()
		res, err = QgsVectorFileWriter.writeAsVectorFormatV2(layer, geojson_path, context, options)
		if res == QgsVectorFileWriter.NoError:
			_qgis_log(f"GeoJSON exported: {geojson_path}")
			return geojson_path
		else:
			raise RuntimeError(f"GeoJSONエクスポート失敗: {err}")
	except Exception as e:
		_qgis_log(f"GeoJSONエクスポート失敗: {e}", level="critical")
		return None
def export_mapbox_style_json(layer, geojson_url="data.geojson", style_path="style.json"):
	"""
	QGISレイヤからMapbox Style JSON (v8) を生成し、style.jsonとして保存する。
	単一レイヤ・単一シンボルのみ対応（複雑なスタイルは簡易化）。
	geojson_url: GeoJSONデータのURL（例: "data.geojson"）
	style_path: 出力するstyle.jsonのパス
	"""
	import json
	try:
		from qgis.core import QgsMarkerSymbol, QgsLineSymbol, QgsFillSymbol
		# レイヤのシンボル情報を取得
		renderer = layer.renderer()
		symbol = renderer.symbol() if renderer else None
		style = {}
		if symbol:
			# 幾何タイプ
			if isinstance(symbol, QgsMarkerSymbol):
				geom_type = 'circle'
			elif isinstance(symbol, QgsLineSymbol):
				geom_type = 'line'
			elif isinstance(symbol, QgsFillSymbol):
				geom_type = 'fill'
			else:
				geom_type = 'fill'
			# 色・線幅など
			props = {}
			try:
				sl = symbol.symbolLayer(0)
				props = sl.properties() if sl else {}
			except Exception:
				props = {}
			color = props.get('color') or props.get('stroke') or props.get('stroke_color') or props.get('fill') or props.get('fill_color') or None
			width = props.get('width') or props.get('stroke-width') or props.get('size') or None
			opacity = props.get('fill-opacity') or props.get('opacity') or None
			# Mapbox Styleのpaint/layoutにマッピング
			paint = {}
			layout = {}
			if geom_type == 'circle':
				if color:
					paint['circle-color'] = color
				if width:
					paint['circle-radius'] = float(width)
				if opacity:
					paint['circle-opacity'] = float(opacity)
			elif geom_type == 'line':
				if color:
					paint['line-color'] = color
				if width:
					paint['line-width'] = float(width)
				if opacity:
					paint['line-opacity'] = float(opacity)
			elif geom_type == 'fill':
				if color:
					paint['fill-color'] = color
				if opacity:
					paint['fill-opacity'] = float(opacity)
			# Mapbox Style JSON構造
			# ここでURLを常に8089ポートに固定
			style_json = {
				"version": 8,
				"name": layer.id(),
				"sources": {
					"qgis": {
						"type": "geojson",
						"data": "http://localhost:8089/data.geojson"
					}
				},
				"layers": [
					{
						"id": layer.id(),
						"type": geom_type,
						"source": "qgis",
						"paint": paint,
						"layout": layout
					}
				]
			}
			# style.jsonとして保存
			with open(style_path, "w", encoding="utf-8") as f:
				json.dump(style_json, f, ensure_ascii=False, indent=2)
			_qgis_log(f"Mapbox Style JSON exported: {style_path}")
			return style_json
		else:
			raise RuntimeError("レイヤのシンボル情報が取得できません")
	except Exception as e:
		_qgis_log(f"Mapbox Style JSONエクスポート失敗: {e}", level="critical")
		return None
"""MapLibre HTML generator for QMapPermalink

This module provides a small helper to create a temporary HTML file that
loads MapLibre GL JS and centers the map based on a permalink string when
possible. If the permalink cannot be parsed, this module will raise an
error — no fallback behavior (such as opening the input as a URL) is
performed.

Coordinate transformations:
- This module will attempt to use the QGIS Python API (PyQGIS) when
	available to convert coordinates from other CRSs to WGS84.
- If PyQGIS is not available, it will fall back only to a built-in
	inverse WebMercator (EPSG:3857) conversion. It does not use `pyproj`.
	If the source CRS is not convertible by these methods, a RuntimeError
	is raised.
"""
import os
import re
import tempfile
import webbrowser
from urllib.parse import urlparse, parse_qs
import traceback
import json
import json as _jsonmod
import xml.etree.ElementTree as ET
import requests
from .maplibre.qmap_maplibre_wmts import choose_tile_template, default_wmts_layers_js
from .maplibre.qmap_maplibre_wfs import sld_to_mapbox_style


def _qgis_log(message, level='info'):
	"""Log message to QGIS message log when available, otherwise print.

	level: 'info'|'warning'|'critical'|'debug'
	"""
	try:
		# QGIS logging API
		from qgis.core import QgsMessageLog, Qgis
		if level == 'info':
			QgsMessageLog.logMessage(str(message), 'QMapPermalink', Qgis.Info)
		elif level == 'warning':
			QgsMessageLog.logMessage(str(message), 'QMapPermalink', Qgis.Warning)
		elif level == 'critical':
			QgsMessageLog.logMessage(str(message), 'QMapPermalink', Qgis.Critical)
		else:
			QgsMessageLog.logMessage(str(message), 'QMapPermalink', Qgis.Info)
	except Exception:
		# fallback to stdout so non-QGIS contexts still see messages
		try:
			print(message)
		except Exception:
			# nothing we can do
			pass


def _parse_permalink(permalink_text):
	"""Try to extract lat, lon, zoom from a permalink URL or a simple
	formatted string. Returns (lat, lon, zoom) or None on failure.
	"""
	if not permalink_text:
		return None
	# Try common query parameters: lat, lon, zoom or center, z
	try:
		parsed = urlparse(permalink_text)
		qs = parse_qs(parsed.query)
		lat = None
		lon = None
		zoom = None
		# If query contains x/y and CRS indicates EPSG:4326, treat x=lon,y=lat
		if 'x' in qs and 'y' in qs:
			crs_q = qs.get('crs', [None])[0]
			if crs_q and ('4326' in str(crs_q)):
				try:
					lon = float(qs['x'][0])
					lat = float(qs['y'][0])
					# optional zoom param
					for key in ('zoom', 'z'):
						if key in qs:
							zoom = float(qs[key][0])
					# return early; keep zoom as None if not provided so callers can
					# decide whether to derive zoom from scale later
					return (lat, lon, zoom)
				except Exception:
					# fall through to other parsing strategies on error
					pass
		for key in ('lat', 'latitude'):
			if key in qs:
				lat = float(qs[key][0])
				break
		for key in ('lon', 'lng', 'longitude'):
			if key in qs:
				lon = float(qs[key][0])
				break
		for key in ('zoom', 'z'):
			if key in qs:
				zoom = float(qs[key][0])
				break
		# Some permalinks embed center as "lon,lat,zoom" or "lat,lon,zoom"
		if ('center' in qs or 'c' in qs) and (lat is None or lon is None):
			center = qs.get('center', qs.get('c'))[0]
			parts = re.split('[,; ]+', center)
			if len(parts) >= 2:
				# try both orders
				a = float(parts[0])
				b = float(parts[1])
				# heuristics: if abs(a)>90 then assume lon,lat
				if abs(a) > 90:
					lon, lat = a, b
				else:
					lat, lon = a, b
			if len(parts) >= 3 and zoom is None:
				zoom = float(parts[2])
		if lat is not None and lon is not None:
			# keep zoom as-is (may be None) so caller can apply scale->zoom logic
			return (lat, lon, zoom)
	except Exception:
		pass

	# Try to find patterns like @lat,lon,zoomz (e.g., some mapping services)
	m = re.search(r'@\s*([0-9.+-]+),\s*([0-9.+-]+),\s*([0-9.+-]+)z', permalink_text)
	if m:
		try:
			lat = float(m.group(1))
			lon = float(m.group(2))
			zoom = float(m.group(3))
			return (lat, lon, zoom)
		except Exception:
			pass

	# fallback: try any three floats in the query/path parts of the URL
	# Avoid scanning the netloc (host:port) which can contain a port number
	# that would confuse ordering heuristics.
	try:
		p = urlparse(permalink_text)
		search_source = ' '
		# include query and path (and fragment) but not netloc
		if p.query:
			search_source += p.query + ' '
		if p.path:
			search_source += p.path + ' '
		if p.fragment:
			search_source += p.fragment
		source_to_scan = search_source
	except Exception:
		source_to_scan = permalink_text

	floats = re.findall(r'[-+]?[0-9]*\.?[0-9]+', source_to_scan)
	if len(floats) >= 3:
		try:
			a, b, c = map(float, floats[:3])
			# guess order
			if abs(a) <= 90:
				return (a, b, c)
			else:
				return (b, a, c)
		except Exception:
			pass

	return None


def open_maplibre_from_permalink(permalink_text, wfs_typename: str = None):
	"""Generate a temporary HTML file with MapLibre and open it.

	If parsing of permalink_text fails, open the permalink_text directly in
	the default browser (it may be a full web page URL).
	"""

	# Log the received permalink as-is
	_qgis_log(f"Received permalink: {permalink_text!r}")

	parsed = _parse_permalink(permalink_text)
	if parsed is None:
		# Parsing failed — do not fallback or attempt to open the input as a URL.
		# Surface an explicit error so callers must handle invalid permalinks.
		raise ValueError(f"Cannot parse permalink: {permalink_text!r}")

	lat, lon, zoom = parsed
	_qgis_log(f"Parsed coordinates (from permalink): lat={lat}, lon={lon}, zoom={zoom}")

	# If the permalink contains a 'scale' parameter, prefer its converted zoom
	# value. We override any parsed zoom with the scale->zoom estimate when
	# possible; if scale parsing or estimator import fails we fall back to the
	# previously parsed zoom.
	try:
		from urllib.parse import urlparse as _urlparse, parse_qs as _parse_qs
		_p = _urlparse(permalink_text)
		_qs = _parse_qs(_p.query)
		if 'scale' in _qs:
			try:
				scale_val = float(_qs['scale'][0])
				# Import and use the pure-Python estimator (no QGIS dependency)
				try:
					from .scale_zoom import estimate_zoom_from_scale_maplibre
					zoom_est = estimate_zoom_from_scale_maplibre(scale_val)
					if zoom_est is not None:
						zoom = float(zoom_est)
						_qgis_log(f"scale param detected: {scale_val} -> estimated zoom={zoom}")
				except Exception:
					# best-effort: if import fails, leave zoom as parsed
					_qgis_log("scale->zoom estimator not available; using parsed zoom if any", 'debug')
			except Exception:
				# ignore float conversion errors
				_qgis_log("failed to parse scale parameter; using parsed zoom if any", 'debug')
	except Exception:
		# ignore any errors while attempting to read scale
		_qgis_log("error while reading scale parameter; using parsed zoom if any", 'debug')

	# If permalink contains x/y/crs style parameters (e.g. from QMapPermalink generate
	# output), try to detect and convert them to WGS84 (lat/lon) for MapLibre.
	# Prefer QGIS transformation APIs if available (when running inside QGIS).
	# If QGIS is not available, fall back only to the built-in
	# EPSG:3857 inverse mercator conversion. `pyproj` is intentionally not used.
	# Quick parse for x, y, crs parameters in the original permalink_text
	# examples: '.../qgis-map?x=123456&y=456789&crs=EPSG:3857'
	from urllib.parse import urlparse, parse_qs
	parsed_url = urlparse(permalink_text)
	qs = parse_qs(parsed_url.query)
	if 'x' in qs and 'y' in qs:
		x_val = float(qs['x'][0])
		y_val = float(qs['y'][0])
		crs_param = qs.get('crs', [None])[0]
		# override zoom from query if present
		if 'zoom' in qs:
			try:
				zoom = float(qs['zoom'][0])
			except Exception:
				pass
		if crs_param:
			# normalize crs string (accept 'EPSG:3857' or numeric)
			src_crs = str(crs_param)
			converted = None
			conversion_method = None
			conversion_errors = []
			# If CRS explicitly states EPSG:4326, the x/y are already lon/lat
			# (QMapPermalink uses x=lon,y=lat for EPSG:4326). Treat that as
			# a short-circuit to avoid attempting QGIS or other transforms
			# which may not be available outside QGIS.
			if '4326' in src_crs:
				try:
					lat = float(y_val)
					lon = float(x_val)
					_qgis_log(f"Detected source CRS EPSG:4326; using x/y as lon/lat -> lat={lat}, lon={lon}, zoom={zoom}")
				except Exception:
					pass
				# skip further conversion attempts
				converted = (lat, lon)
				conversion_method = 'direct'

			# try QGIS
			try:
				from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsPointXY
				src = QgsCoordinateReferenceSystem(str(src_crs))
				if src.isValid():
					dest = QgsCoordinateReferenceSystem('EPSG:4326')
					transform = QgsCoordinateTransform(src, dest, QgsProject.instance())
					pt = transform.transform(QgsPointXY(float(x_val), float(y_val)))
					converted = (float(pt.y()), float(pt.x()))
					conversion_method = 'qgis'
			except Exception:
				conversion_errors.append(('qgis', traceback.format_exc()))
			# try built-in EPSG:3857 inverse mercator
			try:
				sc = str(src_crs).upper()
				if '3857' in sc or '900913' in sc:
					import math
					R = 6378137.0
					lon_deg = (float(x_val) / R) * (180.0 / math.pi)
					lat_rad = 2 * math.atan(math.exp(float(y_val) / R)) - math.pi / 2.0
					lat_deg = lat_rad * (180.0 / math.pi)
					converted = (float(lat_deg), float(lon_deg))
					conversion_method = 'builtin'
			except Exception:
				conversion_errors.append(('builtin', traceback.format_exc()))
			# If none of the methods produced a converted point, surface an error
			if converted is None:
				err_msg = f"Point conversion failed for CRS '{src_crs}'. Attempts:\n"
				for name, tb in conversion_errors:
					err_msg += f"- {name}: {tb}\n"
				raise RuntimeError(err_msg)
			else:
				# converted is (lat, lon)
				lat, lon = converted
				_qgis_log(f"Converted point from CRS {src_crs}: method={conversion_method}, lat={lat}, lon={lon}, zoom={zoom}")



		# NOTE: fitBounds-based scale/viewport adjustment disabled.
		# Per request, do not apply map.fitBounds from permalink bbox parameters.
		# Always leave fit_js empty so no fitBounds JS is injected into the generated HTML.
		fit_js = ''

	# If zoom is still None at this point, use a safe default
	if zoom is None:
		zoom = 10

	# Clip and format zoom for output (sane range for most tile servers)
	try:
		_zoom_val = float(zoom) if zoom is not None else None
		if _zoom_val is None:
			_zoom_out = None
		else:
			# ensure zoom is not negative; do not artificially cap the maximum zoom
			_zoom_out = max(0.0, _zoom_val)
			# round to 2 decimal places for tidy HTML output
			_zoom_out = float(f"{_zoom_out:.2f}")
	except Exception:
		_zoom_out = None

	# Log final map target used for MapLibre
	_qgis_log(f"MapLibre target coordinates: lat={lat}, lon={lon}, zoom={_zoom_out}")

	# Choose tile template: prefer local WMTS when running inside QGIS so
	# the generated MapLibre HTML points at the plugin's /wmts endpoint.
	tile_template = choose_tile_template()
	try:
		_qgis_log(f"Using tile template for MapLibre: {tile_template}", 'debug')
	except Exception:
		# best-effort logging; ignore if logging is unavailable
		pass

	# Extract themes and bookmarks from permalink if available
	themes_list = []
	bookmarks_list = []
	try:
		from urllib.parse import urlparse, parse_qs
		parsed_url = urlparse(permalink_text)
		qs = parse_qs(parsed_url.query)
		
		# Try to get themes from QGIS project if available
		try:
			from qgis.core import QgsProject
			project = QgsProject.instance()
			# Get theme names from map theme collection
			if project:
				theme_collection = project.mapThemeCollection()
				if theme_collection:
					themes_list = theme_collection.mapThemes()
					_qgis_log(f"Found {len(themes_list)} themes from QGIS project")
		except Exception as e:
			_qgis_log(f"Could not get themes from QGIS: {e}", 'debug')
		
		# Try to get bookmarks from QGIS project if available
		try:
			from qgis.core import QgsProject, QgsBookmarkManager, QgsApplication
			project = QgsProject.instance()
			if project:
				# Get project bookmarks
				project_bookmarks = []
				bookmark_manager = project.bookmarkManager()
				if bookmark_manager:
					project_bookmarks = bookmark_manager.bookmarks()
					_qgis_log(f"Found {len(project_bookmarks)} project bookmarks", 'info')
				else:
					_qgis_log("Project bookmark manager is None", 'info')
				
				# Get user (application-level) bookmarks
				_qgis_log("Attempting to get user bookmarks from QgsApplication...", 'info')
				user_bookmarks = []
				try:
					app_bookmark_manager = QgsApplication.bookmarkManager()
					_qgis_log(f"QgsApplication.bookmarkManager() returned: {app_bookmark_manager}", 'info')
					if app_bookmark_manager:
						user_bookmarks = app_bookmark_manager.bookmarks()
						_qgis_log(f"Found {len(user_bookmarks)} user bookmarks", 'info')
					else:
						_qgis_log("Application bookmark manager is None", 'info')
				except Exception as e:
					_qgis_log(f"Could not get user bookmarks: {e}", 'warning')
					import traceback
					_qgis_log(traceback.format_exc(), 'warning')
				
				# Combine both lists
				qgis_bookmarks = project_bookmarks + user_bookmarks
				_qgis_log(f"Total {len(qgis_bookmarks)} bookmarks (project + user)", 'info')
				
				# Log all bookmark names for debugging
				bookmark_names = [bm.name() for bm in qgis_bookmarks]
				_qgis_log(f"Bookmark names: {', '.join(bookmark_names)}", 'info')
				
				for bm in qgis_bookmarks:
					try:
						bookmark_name = bm.name()
						_qgis_log(f"Processing bookmark: {bookmark_name}")
						
						# Get bookmark extent and convert to EPSG:3857 if needed
						extent = bm.extent()
						center_x = extent.center().x()
						center_y = extent.center().y()
						
						_qgis_log(f"  Extent center coords: ({center_x}, {center_y})")
						
						# Convert from bookmark CRS to EPSG:3857 for MapLibre
						from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPointXY
						
						# Get CRS from extent (more reliable than bookmark.crs())
						src_crs = extent.crs()
						
						if src_crs is None or not src_crs.isValid():
							# Fallback: try to get from bookmark object
							try:
								if hasattr(bm, 'crs') and callable(bm.crs):
									src_crs = bm.crs()
							except Exception:
								pass
						
						if src_crs is None or not src_crs.isValid():
							# Last resort: guess based on coordinate values
							# If coordinates are > 180, likely EPSG:3857
							if abs(center_x) > 180 or abs(center_y) > 180:
								src_crs = QgsCoordinateReferenceSystem('EPSG:3857')
								_qgis_log(f"  Auto-detected CRS as EPSG:3857 based on coordinate range")
							else:
								src_crs = QgsCoordinateReferenceSystem('EPSG:4326')
								_qgis_log(f"  Using default CRS EPSG:4326")
						else:
							_qgis_log(f"  Bookmark CRS: {src_crs.authid()}")
						
						dest_crs = QgsCoordinateReferenceSystem('EPSG:3857')
						
						# Only transform if source CRS is different from destination
						if src_crs.authid() == 'EPSG:3857':
							# Already in the target CRS
							final_x = center_x
							final_y = center_y
							_qgis_log(f"  No transformation needed (already EPSG:3857)")
						else:
							# Transform to EPSG:3857
							transform = QgsCoordinateTransform(src_crs, dest_crs, project)
							pt = transform.transform(QgsPointXY(center_x, center_y))
							final_x = pt.x()
							final_y = pt.y()
							_qgis_log(f"  Transformed from {src_crs.authid()} to EPSG:3857")
						
						_qgis_log(f"  Final coords EPSG:3857: ({final_x}, {final_y})")
						
						# Convert EPSG:3857 to EPSG:4326 (lon/lat) for MapLibre
						wgs84_crs = QgsCoordinateReferenceSystem('EPSG:4326')
						to_wgs84 = QgsCoordinateTransform(dest_crs, wgs84_crs, project)
						wgs84_pt = to_wgs84.transform(QgsPointXY(final_x, final_y))
						
						# MapLibre expects [longitude, latitude]
						bookmark_lon = float(wgs84_pt.x())
						bookmark_lat = float(wgs84_pt.y())
						_qgis_log(f"  Converted to WGS84: lon={bookmark_lon}, lat={bookmark_lat}")
						
						bookmarks_list.append({
							'name': bookmark_name,
							'lon': bookmark_lon,  # longitude (x in WGS84)
							'lat': bookmark_lat,  # latitude (y in WGS84)
							'zoom': 14  # default zoom for bookmarks
						})
						_qgis_log(f"  Successfully added bookmark {bookmark_name}")
					except Exception as e:
						_qgis_log(f"Error processing bookmark {bookmark_name}: {e}", 'warning')
						import traceback
						_qgis_log(traceback.format_exc(), 'warning')
				_qgis_log(f"Successfully processed {len(bookmarks_list)} bookmarks from QGIS project", 'info')
				
				# Log final bookmark list for debugging
				for i, bm in enumerate(bookmarks_list):
					_qgis_log(f"  [{i}] {bm['name']}: lon={bm['lon']:.6f}, lat={bm['lat']:.6f}", 'info')
		except Exception as e:
			_qgis_log(f"Could not get bookmarks from QGIS: {e}", 'warning')
			import traceback
			_qgis_log(traceback.format_exc(), 'warning')
	except Exception as e:
		_qgis_log(f"Error extracting themes/bookmarks: {e}", 'debug')
	
	# Prepare WFS layer parameters using helper module (moved to maplibre/qmap_maplibre_wfs.py)
	from .maplibre.qmap_maplibre_wfs import prepare_wfs_for_maplibre
	_wfs_info = prepare_wfs_for_maplibre(permalink_text, wfs_typename)
	# Unpack values used later in the template generation
	_final_typename = _wfs_info['final_typename']
	_wfs_typename = _wfs_info['wfs_typename']
	_wfs_query_url = _wfs_info['wfs_query_url']
	_wfs_source_id = _wfs_info['wfs_source_id']
	_wfs_layer_id = _wfs_info['wfs_layer_id']
	_wfs_label_id = _wfs_info['wfs_label_id']
	_wfs_layer_title = _wfs_info['wfs_layer_title']
	_wfs_label_title = _wfs_info['wfs_label_title']
	_wfs_source_id_js = _wfs_info['wfs_source_id_js']
	_wfs_layer_id_js = _wfs_info['wfs_layer_id_js']
	_wfs_label_id_js = _wfs_info['wfs_label_id_js']
	_wfs_layer_title_js = _wfs_info['wfs_layer_title_js']
	_wfs_label_title_js = _wfs_info['wfs_label_title_js']
	style_url = _wfs_info['style_url']
	mapbox_layers = _wfs_info['mapbox_layers']
	style_json = _wfs_info['style_json']
	wfs_layers_js = _wfs_info['wfs_layers_js']

	html = '''<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no" />
  <title>MapLibre Viewer</title>
	<link href="https://unpkg.com/maplibre-gl@latest/dist/maplibre-gl.css" rel="stylesheet" />
  <style>html,body,#map{{height:100%;margin:0;padding:0}}#map{{position:fixed;inset:0}}</style>
</head>
<body>
<div id="map"></div>
<!-- Theme and Bookmark selectors -->
<div id="qmp-controls" style="position:absolute;top:10px;left:10px;z-index:1002;display:flex;flex-direction:column;gap:6px;font-family:sans-serif;font-size:13px">
	<select id="qmp-themes" style="padding:6px 8px;background:#fff;border:1px solid #666;border-radius:4px;cursor:pointer;min-width:150px" title="Select theme"></select>
	<select id="qmp-bookmarks" style="padding:6px 8px;background:#fff;border:1px solid #666;border-radius:4px;cursor:pointer;min-width:150px" title="Select bookmark"></select>
</div>
<!-- Layer control panel (WMTS layer visibility checkboxes) -->
<div id="layerControl" style="position:absolute;top:110px;left:10px;z-index:1001;padding:6px;background:#fff;border:1px solid #666;border-radius:4px;max-height:60vh;overflow:auto;font-family:sans-serif;font-size:13px">
	<div style="font-weight:600;margin-bottom:6px">Layers</div>
	<!-- checkboxes will be inserted here by script -->
</div>
<button id="pitchToggle" style="position:absolute;top:10px;right:10px;z-index:1001;padding:6px 8px;background:#fff;border:1px solid #666;border-radius:4px;cursor:pointer">斜め禁止</button>
<script src="https://unpkg.com/maplibre-gl@latest/dist/maplibre-gl.js"></script>
<script>
  console.log('MapLibre script loaded');
	try {{
			// Use a dynamic style URL provided by the server.
			// MapLibre accepts a URL string for the style parameter.
			const style = __STYLE_URL__;
    
			console.log('Initializing map at lat=__LAT__, lon=__LON__, zoom=__ZOOM__');
		const map = new maplibregl.Map({{
			container: 'map',
			style: style,
			center: [__LON__, __LAT__],
			zoom: __ZOOM__,
			// Prefer local ideograph font families so CJK characters render using
			// system fonts when signed-distance-field glyphs are not available
			// via a glyphs server. Adjust the family list to match fonts installed
			// on the host (e.g. 'Noto Sans JP' on many systems).
			localIdeographFontFamily: 'Noto Sans JP, Arial Unicode MS, sans-serif'
		});

		// Expose the map instance to the window for debugging in the browser
		// console. Some MapLibre builds and script scopes keep the `map` variable
		// local to the script; exposing it makes it easier to inspect sources,
		// layers and to tweak styles from DevTools.
		try {
			window.qmap_map = map;
			// keep common alias too
			window.map = map;
		} catch (e) {
			console.warn('Unable to expose map to window for debugging', e);
		}

			// Pitch toggle button: disable/enable oblique (3D) tilt interaction
			try {{
				const pitchBtn = document.getElementById('pitchToggle');
				// Start with pitch locked (斜め禁止) as requested; rotation remains allowed.
				let pitchLocked = true;
				const _enforcePitch = function() {{
					try {{
						if (map.getPitch && Math.abs(map.getPitch()) > 0.0001) {{
							map.setPitch(0);
						}}
					}} catch (e) {{ /* ignore */ }}
				}};
				function lockPitch() {{
					try {{ map.setPitch(0); }} catch(e) {{ console.warn('setPitch failed', e); }}
					try {{ if (map.on) map.on('move', _enforcePitch); }} catch(e) {{}}
					pitchLocked = true;
					pitchBtn.textContent = '斜め許可';
				}}
				function unlockPitch() {{
					try {{ if (map.off) map.off('move', _enforcePitch); }} catch(e) {{}}
					pitchLocked = false;
					pitchBtn.textContent = '斜め禁止';
				}}
				pitchBtn.addEventListener('click', function() {{
					if (!pitchLocked) lockPitch(); else unlockPitch();
				}});
				// enforce initially
				try {{ lockPitch(); }} catch(e) {{}}
			}} catch(e) {{ console.warn('pitch toggle setup failed', e); }}
		// Defer resize and fitBounds until style/tile sources are loaded to
		// avoid missing tiles or blank initial render when the container was
		// not yet ready. Call map.resize() then apply fitBounds if present.
    
		map.on('load', function() {{
				console.log('Map loaded successfully');
				try {{ map.resize(); }} catch (e) {{ console.warn('map.resize() failed', e); }}
				
				// デバッグ: スタイルJSONの内容をログ出力
				try {{
					var currentStyle = map.getStyle();
					console.log('📄 Current map style:', JSON.stringify(currentStyle, null, 2).substring(0, 2000));
					if (currentStyle && currentStyle.layers) {{
						console.log('🎨 Style layers:', currentStyle.layers.length, 'layers');
						currentStyle.layers.forEach(function(layer) {{
							console.log('  - Layer:', layer.id, 'type:', layer.type, 'source:', layer.source, 'paint:', layer.paint);
						}});
					}}
				}} catch (e) {{ console.warn('Failed to log style', e); }}
				
				try {{
					// Delegate post-load behavior to the packaged postload script.
					// The script is copied next to the generated HTML and defines
					// `window.qmap_init_after_load(map)` which will perform WFS
					// fetching, UI population and pitch toggle setup.
					if (window.qmap_init_after_load) {{
						try {{ window.qmap_init_after_load(map); }} catch (er) {{ console.warn('qmap_init_after_load failed', er); }}
					}}
				}} catch (e) {{ console.warn('post-load init failed', e); }}
				try {{
					__FIT_JS__
				}} catch (e) {{ console.warn('fitBounds failed', e); }}
			}});
    
    map.on('error', function(e) {{
      console.error('Map error:', e);
    }});
  }} catch (e) {{
    console.error('Failed to initialize map:', e);
    document.body.innerHTML = '<div style="padding:20px;font-family:sans-serif;"><h2>Map initialization failed</h2><pre>' + e.toString() + '</pre><p>Check browser console (F12) for details.</p></div>';
  }}
</script>
__EXTERNAL_SCRIPT_TAGS__
</body>
</html>'''

	# write HTML and companion scripts to a temporary directory
	try:
		# Replace placeholders inserted to avoid f-string brace parsing issues
		html_out = html.replace('__TILE_TEMPLATE__', tile_template)
		# numeric formatting for lat/lon/zoom
		html_out = html_out.replace('__LAT__', str(float(lat)))
		html_out = html_out.replace('__LON__', str(float(lon)))
		html_out = html_out.replace('__ZOOM__', str(float(_zoom_out) if _zoom_out is not None else '0'))
		# fit_js may be empty string
		html_out = html_out.replace('__FIT_JS__', fit_js or '')
		# WFS query URL (already URL-encoded where needed)
		html_out = html_out.replace('__WFS_QUERY_URL__', _wfs_query_url)
		
		# WFS source/layer/label ids and titles (JSON-escaped JS literals)
		# Insert dynamic style URL as a JSON string literal so JS receives a proper string
		# Debug: log the style_url value
		try:
			_qgis_log(f"🎨 Style URL being inserted into HTML: {style_url}", 'info')
			_qgis_log(f"🎨 JSON-encoded style URL: {_jsonmod.dumps(style_url)}", 'info')
		except Exception:
			pass
		html_out = html_out.replace('__STYLE_URL__', _jsonmod.dumps(style_url))
		# Clear inline placeholders (we now use external scripts)
		html_out = html_out.replace('__WFS_LAYERS_JS__', '')
		html_out = html_out.replace('__WMTS_LAYERS_JS__', '')

		# Create a temp directory and copy packaged scripts into it
		temp_dir = tempfile.mkdtemp(prefix='qmap_maplibre_')
		path = os.path.join(temp_dir, 'index.html')
		pkg_scripts_dir = os.path.join(os.path.dirname(__file__), 'maplibre', 'scripts')
		for _script in ('wmts_layers.js', 'qmap_postload.js', 'show_zoom.js'):
			try:
				with open(os.path.join(pkg_scripts_dir, _script), 'rb') as rf:
					with open(os.path.join(temp_dir, _script), 'wb') as wf:
						wf.write(rf.read())
			except Exception:
				# ignore copy failures; continue to write HTML
				pass

		# Build script tags: inline the contents of the packaged scripts so that
		# the generated HTML works both when opened via file:// and when served
		# by an HTTP endpoint that may not be serving the script files.
		def _read_script(name):
			p = os.path.join(temp_dir, name)
			try:
				with open(p, 'r', encoding='utf-8') as rf:
					return rf.read()
			except Exception:
				return None

		wmts_js = _read_script('wmts_layers.js')
		post_js = _read_script('qmap_postload.js')
		show_js = _read_script('show_zoom.js')
		# Server-side GetCapabilities checks removed. Delegate WFS capability
		# detection and fetching entirely to the client-side postload script.
		# This avoids the HTML generator performing network requests during
		# HTML creation and keeps WFS calls initiated only by the browser.

		config_script = (
			"<script>\n"
			"  window.__QMAP_CONFIG__ = {\n"
			f"    style: {_jsonmod.dumps(style_url)},\n"
			f"    lat: {float(lat)},\n"
			f"    lon: {float(lon)},\n"
			f"    zoom: {float(_zoom_out) if _zoom_out is not None else 0}\n"
			"  };\n"
			f"  // Theme and bookmark data for selectors\n"
			f"  const themes = {_jsonmod.dumps(themes_list)};\n"
			f"  const bookmarks = {_jsonmod.dumps(bookmarks_list)};\n"
			f"  const initialX = {float(lon)};\n"
			f"  const initialY = {float(lat)};\n"
			f"  const initialZoom = {float(_zoom_out) if _zoom_out is not None else 0};\n"
			"</script>\n"
		)

		script_tags = config_script
		# WMTS/WMS: Always include regardless of WFS availability
		# This ensures base map tiles (WMTS/WMS) are always loaded
		if wmts_js is not None:
			script_tags += "<script>\n" + wmts_js + "\n</script>\n"
		else:
			script_tags += "<script src=\"wmts_layers.js\"></script>\n"
		
		# WFS: Only include postload when the script was successfully read
		# This separates WFS-specific functionality from base map rendering
		if post_js is not None:
			script_tags += "<script>\n" + post_js + "\n</script>\n"
		# Include show_zoom script if present
		if show_js is not None:
			script_tags += "<script>\n" + show_js + "\n</script>\n"
		# Note: Do NOT include external <script src="qmap_postload.js"> fallback
		# when post_js is None, as this allows the HTML to work without WFS

		html_out = html_out.replace('__EXTERNAL_SCRIPT_TAGS__', script_tags)
		# The template used double-braces ({{ }}) to avoid f-string parsing during
		# development. Convert double-braces into single-brace for valid JS/CSS.
		html_out = html_out.replace('{{', '{').replace('}}', '}')
		with open(path, 'w', encoding='utf-8') as f:
			f.write(html_out)
		_qgis_log(f"MapLibre HTML written to: {path}")
		# open file URL using a proper file URI when possible
		try:
			from pathlib import Path
			file_uri = Path(path).as_uri()
			webbrowser.open(file_uri)
		except Exception:
			webbrowser.open('file://' + path)
		return path
	except Exception as e:
		raise RuntimeError(f"Failed to create or open MapLibre HTML file: {e}") from e

    
