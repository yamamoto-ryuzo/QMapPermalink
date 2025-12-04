# -*- coding: utf-8 -*-
"""geo_webview WFS Service

WFS (Web Feature Service) 機能を提供する専用クラス。
QGISベクターレイヤーから地物をGeoJSON/GML形式で提供。
"""

import json
import re
import time
import threading
from typing import Optional, Dict, Any, List, Tuple
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeatureRequest, 
    QgsJsonExporter, QgsMessageLog, Qgis, QgsRectangle,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform
)
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QColor


class GeoWebViewWFSService:
    """geo_webview用WFSサービスクラス

    WFS GetCapabilitiesおよびGetFeatureリクエストを処理し、
    QGISベクターレイヤーから地物をGeoJSON/GML形式で提供します。
    """

    def __init__(self, iface, server_port: int = 8089):
        """WFSサービスを初期化

        Args:
            iface: QGISインターフェース
            server_port: サーバーポート番号
        """
        self.iface = iface
        self.server_port = server_port
        
        # レスポンスキャッシュ (Phase 1高速化)
        self._response_cache = {}  # {cache_key: (timestamp, response_data, content_type)}
        self._cache_lock = threading.Lock()
        self._cache_ttl = 300  # 5分間キャッシュ

    def _client_friendly_typename(self, raw_id: str) -> str:
        """Return a client-friendly typename derived from a QGIS layer id.

        This is intended only for display and client convenience. It strips
        leading underscore characters that may have been introduced by
        previous sanitization or legacy workflows. The canonical id used by
        the server for lookups remains the original layer.id().
        """
        try:
            if raw_id is None:
                return ''
            # Remove leading underscores only; preserve other characters.
            return str(raw_id).lstrip('_')
        except Exception:
            return str(raw_id)
    
    def _get_cache_key(self, layer_id: str, bbox: str, srs_name: str, 
                       max_features: int, output_format: str) -> str:
        """キャッシュキーを生成
        
        Args:
            layer_id: レイヤーID
            bbox: BBOX文字列
            srs_name: SRS名
            max_features: 最大地物数
            output_format: 出力フォーマット
            
        Returns:
            str: キャッシュキー(MD5ハッシュ)
        """
        import hashlib
        key_parts = [
            layer_id,
            bbox or '',
            srs_name or '',
            str(max_features or 0),
            output_format or 'json'
        ]
        key_string = ':'.join(key_parts)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def _clear_expired_cache(self):
        """期限切れキャッシュをクリア"""
        try:
            with self._cache_lock:
                current_time = time.time()
                expired_keys = [
                    key for key, (timestamp, _, _) in self._response_cache.items()
                    if current_time - timestamp > self._cache_ttl
                ]
                for key in expired_keys:
                    del self._response_cache[key]
                if expired_keys:
                    from qgis.core import QgsMessageLog, Qgis
                    QgsMessageLog.logMessage(
                        f"🧹 WFS Cache: {len(expired_keys)}個の期限切れエントリを削除",
                        "geo_webview", Qgis.Info
                    )
        except Exception:
            pass

    def handle_wfs_request(self, conn, params: Dict[str, list], host: Optional[str] = None) -> None:
        """WFSエンドポイントを処理"""
        from qgis.core import QgsMessageLog, Qgis


        # デバッグ情報

        request = params.get('REQUEST', [''])[0].upper()
        service = params.get('SERVICE', [''])[0].upper()

        if service != 'WFS':
            from . import http_server
            http_server.send_wfs_error_response(conn, "InvalidParameterValue", "SERVICE parameter must be WFS", locator='SERVICE')
            return

        if request == 'GETCAPABILITIES':
            self._handle_wfs_get_capabilities(conn, params, host)
        elif request == 'GETFEATURE':
            self._handle_wfs_get_feature(conn, params)
        elif request == 'DESCRIBEFEATURETYPE':
            self._handle_wfs_describe_feature_type(conn, params)
        elif request == 'GETSTYLES':
            self._handle_wfs_get_styles(conn, params)
        else:
            from . import http_server
            http_server.send_wfs_error_response(conn, "InvalidRequest", f"Request {request} is not supported")

    def _handle_wfs_get_capabilities(self, conn, params: Dict[str, list], host: Optional[str] = None) -> None:
        """WFS GetCapabilitiesリクエストを処理"""
        from qgis.core import QgsMessageLog, Qgis

        # Determine base host for OnlineResource entries
        try:
            base_host = host if host else f"localhost:{self.server_port}"
        except Exception:
            base_host = f"localhost:{self.server_port}"

        # Prefer project-level WFSLayers entry if present (same logic as /wfs-layers)
        project = QgsProject.instance()
        try:
            wfs_ids, ok = project.readListEntry('WFSLayers', '/')
        except Exception:
            wfs_ids, ok = ([], False)

        vector_layers = []
        if ok and wfs_ids:
            for lid in [str(i) for i in wfs_ids]:
                try:
                    layer = QgsProject.instance().mapLayer(lid)
                    if not layer:
                        continue
                    # only include vector layers
                    if isinstance(layer, QgsVectorLayer):
                        vector_layers.append(layer)
                except Exception:
                    continue
        else:
            # No WFSLayers defined -> return empty FeatureTypeList
            from . import http_server
            xml_content = (
                f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                f"<WFS_Capabilities version=\"2.0.0\" xmlns=\"http://www.opengis.net/wfs/2.0\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" xsi:schemaLocation=\"http://www.opengis.net/wfs/2.0 http://schemas.opengis.net/wfs/2.0/wfs.xsd\">\n"
                f"  <ServiceIdentification>\n"
                f"    <Title>QGIS Map Permalink WFS Service</Title>\n"
                f"    <Abstract>Dynamic WFS service for QGIS vector layers</Abstract>\n"
                f"    <ServiceType>WFS</ServiceType>\n"
                f"    <ServiceTypeVersion>2.0.0</ServiceTypeVersion>\n"
                f"  </ServiceIdentification>\n"
                f"  <FeatureTypeList>\n"
                f"  </FeatureTypeList>\n"
                f"</WFS_Capabilities>"
            )
            http_server.send_http_response(conn, 200, "OK", xml_content, content_type="text/xml; charset=utf-8")
            return

        # Build FeatureType entries
        feature_types_xml = ""
        for layer in vector_layers:
            # Use layer.id() as the canonical typename (FeatureType <Name>).
            # We expose the true QGIS layer id as the FeatureType <Name> so
            # clients can rely on using layer.id() as the authoritative
            # typename. Human-readable titles remain available in <Title>.
            raw_id = layer.id()
            client_typename = self._client_friendly_typename(raw_id)
            safe_tag = re.sub(r'[^A-Za-z0-9_]', '_', str(raw_id))
            crs = layer.crs().authid() if layer.crs().isValid() else 'EPSG:4326'
            extent = self._get_layer_extent(layer)

            feature_types_xml += (
                f"\n    <FeatureType>"
                # Expose a client-friendly typename (readable) while the
                # server will continue to support requests using the true
                # canonical layer.id(). Clients may use either form; server
                # matching accepts both (see _find_layer_by_name).
                # expose the canonical QGIS layer id as the FeatureType name
                f"\n      <Name>{raw_id}</Name>"
                f"\n      <Title>{layer.name()}</Title>"
                f"\n      <Abstract>Vector layer from QGIS project</Abstract>"
                f"\n      <DefaultCRS>{crs}</DefaultCRS>"
                f"\n      <OutputFormats>"
                f"\n        <Format>application/json</Format>"
                f"\n        <Format>application/gml+xml</Format>"
                f"\n      </OutputFormats>"
                f"\n      <WGS84BoundingBox>"
                f"\n        <LowerCorner>{extent['minx']} {extent['miny']}</LowerCorner>"
                f"\n        <UpperCorner>{extent['maxx']} {extent['maxy']}</UpperCorner>"
                f"\n      </WGS84BoundingBox>"
                f"\n    </FeatureType>"
            )

        xml_content = (
            f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            f"<WFS_Capabilities version=\"2.0.0\" xmlns=\"http://www.opengis.net/wfs/2.0\" "
            f"xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" "
            f"xmlns:xlink=\"http://www.w3.org/1999/xlink\" "
            f"xsi:schemaLocation=\"http://www.opengis.net/wfs/2.0 http://schemas.opengis.net/wfs/2.0/wfs.xsd\">\n"
            f"  <ServiceIdentification>\n"
            f"    <Title>QGIS Map Permalink WFS Service</Title>\n"
            f"    <Abstract>Dynamic WFS service for QGIS vector layers</Abstract>\n"
            f"    <ServiceType>WFS</ServiceType>\n"
            f"    <ServiceTypeVersion>2.0.0</ServiceTypeVersion>\n"
            f"    <Fees>NONE</Fees>\n"
            f"    <AccessConstraints>NONE</AccessConstraints>\n"
            f"  </ServiceIdentification>\n"
            f"  <ServiceProvider>\n"
            f"    <ProviderName>QMapPermalink</ProviderName>\n"
            f"  </ServiceProvider>\n"
            f"  <OperationsMetadata>\n"
            f"    <Operation name=\"GetCapabilities\">\n"
            f"      <DCP><HTTP><Get xlink:href=\"http://{base_host}/wfs\"/></HTTP></DCP>\n"
            f"    </Operation>\n"
            f"    <Operation name=\"DescribeFeatureType\">\n"
            f"      <DCP><HTTP><Get xlink:href=\"http://{base_host}/wfs\"/></HTTP></DCP>\n"
            f"    </Operation>\n"
            f"    <Operation name=\"GetFeature\">\n"
            f"      <DCP><HTTP><Get xlink:href=\"http://{base_host}/wfs\"/></HTTP></DCP>\n"
            f"    </Operation>\n"
            f"    <Operation name=\"GetStyles\">\n"
            f"      <DCP><HTTP><Get xlink:href=\"http://{base_host}/wfs\"/></HTTP></DCP>\n"
            f"    </Operation>\n"
            f"  </OperationsMetadata>\n"
            f"  <FeatureTypeList>{feature_types_xml}\n"
            f"  </FeatureTypeList>\n"
            f"</WFS_Capabilities>"
        )

        from . import http_server
        http_server.send_http_response(conn, 200, "OK", xml_content, content_type="text/xml; charset=utf-8")

    def _handle_wfs_get_feature(self, conn, params: Dict[str, list]) -> None:
        """WFS GetFeatureリクエストを処理"""
        from qgis.core import QgsMessageLog, Qgis

        try:
            # パラメータの解析
            type_name = params.get('TYPENAME', params.get('TYPENAMES', ['']))[0]
            if not type_name:
                from . import http_server
                http_server.send_wfs_error_response(conn, "MissingParameterValue", "TYPENAME parameter is required", locator='TYPENAME')
                return

            output_format = params.get('OUTPUTFORMAT', ['application/json'])[0]
            max_features = params.get('MAXFEATURES', [None])[0]
            if max_features:
                try:
                    max_features = int(max_features)
                except:
                    max_features = None

            bbox = params.get('BBOX', [None])[0]
            srs_name = params.get('SRSNAME', [None])[0]

            # レイヤーの検索
            layer = self._find_layer_by_name(type_name)
            if not layer:
                from . import http_server
                http_server.send_wfs_error_response(conn, "InvalidParameterValue", f"Layer '{type_name}' not found", locator='TYPENAME')
                return
            
            # 🚀 Phase 1高速化: キャッシュチェック
            cache_key = self._get_cache_key(
                layer.id(), 
                bbox or '', 
                srs_name or '', 
                max_features or 0,
                output_format
            )
            
            with self._cache_lock:
                if cache_key in self._response_cache:
                    timestamp, cached_data, cached_content_type = self._response_cache[cache_key]
                    if time.time() - timestamp < self._cache_ttl:
                        # キャッシュヒット!
                        QgsMessageLog.logMessage(
                            f"⚡ WFS Cache HIT: {type_name} (saved ~{int((time.time()-timestamp)*1000)}ms)",
                            "geo_webview", Qgis.Info
                        )
                        from . import http_server
                        http_server.send_http_response(
                            conn, 200, "OK", cached_data, 
                            content_type=cached_content_type
                        )
                        return
            
            # キャッシュミス: 通常処理
            start_time = time.time()

            # 地物のクエリ
            features = self._query_features(layer, bbox, srs_name, max_features)

            # 出力フォーマットに応じたレスポンス生成（柔軟な判定）
            of = (output_format or '').lower()
            if 'gml' in of or of in ('gml', 'application/gml+xml'):
                response_content = self._features_to_gml(features, layer)
                content_type = "application/gml+xml; charset=utf-8"
            else:
                # default/fallback to GeoJSON
                response_content = self._features_to_geojson(features, layer)
                content_type = "application/json; charset=utf-8"
            
            # 🚀 Phase 1高速化: キャッシュに保存
            elapsed_time = int((time.time() - start_time) * 1000)
            with self._cache_lock:
                self._response_cache[cache_key] = (time.time(), response_content, content_type)
                QgsMessageLog.logMessage(
                    f"💾 WFS Cache MISS: {type_name} ({len(features)}地物, {elapsed_time}ms) - キャッシュに保存",
                    "geo_webview", Qgis.Info
                )
            
            # 期限切れキャッシュのクリーンアップ(10%の確率で実行)
            import random
            if random.random() < 0.1:
                self._clear_expired_cache()

            from . import http_server
            http_server.send_http_response(conn, 200, "OK", response_content, content_type=content_type)

        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            import traceback
            QgsMessageLog.logMessage(f"❌ WFS GetFeature error: {e}", "geo_webview", Qgis.Critical)
            QgsMessageLog.logMessage(f"❌ Error traceback: {traceback.format_exc()}", "geo_webview", Qgis.Critical)
            from . import http_server
            # Return an OWS-style ExceptionReport for better WFS compatibility
            try:
                http_server.send_wfs_error_response(conn, "InternalError", f"WFS GetFeature failed: {str(e)}")
            except Exception:
                http_server.send_http_response(conn, 500, "Internal Server Error", f"WFS GetFeature failed: {str(e)}")

    def _handle_wfs_describe_feature_type(self, conn, params: Dict[str, list]) -> None:
        """WFS DescribeFeatureTypeリクエストを処理"""
        from qgis.core import QgsMessageLog, Qgis

        try:
            type_name = params.get('TYPENAME', params.get('TYPENAMES', ['']))[0]
            if not type_name:
                from . import http_server
                http_server.send_wfs_error_response(conn, "MissingParameterValue", "TYPENAME parameter is required", locator='TYPENAME')
                return

            # レイヤーの検索
            layer = self._find_layer_by_name(type_name)
            if not layer:
                from . import http_server
                http_server.send_wfs_error_response(conn, "InvalidParameterValue", f"Layer '{type_name}' not found", locator='TYPENAME')
                return

            # スキーマの生成
            schema_xml = self._generate_feature_type_schema(layer)

            from . import http_server
            http_server.send_http_response(conn, 200, "OK", schema_xml, content_type="text/xml; charset=utf-8")

        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            import traceback
            QgsMessageLog.logMessage(f"❌ WFS DescribeFeatureType error: {e}", "geo_webview", Qgis.Critical)
            from . import http_server
            http_server.send_http_response(conn, 500, "Internal Server Error", f"WFS DescribeFeatureType failed: {str(e)}")

    def _handle_wfs_get_styles(self, conn, params: Dict[str, list]) -> None:
        """WFS GetStylesリクエストを処理"""
        from qgis.core import QgsMessageLog, Qgis

        try:
            from qgis.core import QgsMessageLog, Qgis
            
            type_name = params.get('TYPENAME', params.get('TYPENAMES', ['']))[0]
            if not type_name:
                from . import http_server
                http_server.send_wfs_error_response(conn, "MissingParameterValue", "TYPENAME parameter is required", locator='TYPENAME')
                return

            # レイヤーの検索
            layer = self._find_layer_by_name(type_name)
            if not layer:
                from . import http_server
                http_server.send_wfs_error_response(conn, "InvalidParameterValue", f"Layer '{type_name}' not found", locator='TYPENAME')
                return

            # SLDの生成
            sld_xml = self._generate_sld(layer)

            from . import http_server
            http_server.send_http_response(conn, 200, "OK", sld_xml, content_type="application/vnd.ogc.sld+xml; charset=utf-8")

        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            import traceback
            QgsMessageLog.logMessage(f"❌ WFS GetStyles error: {e}", "geo_webview", Qgis.Critical)
            from . import http_server
            http_server.send_http_response(conn, 500, "Internal Server Error", f"WFS GetStyles failed: {str(e)}")

    def _get_vector_layers(self) -> List[QgsVectorLayer]:
        """プロジェクトからベクターレイヤーを取得"""
        project = QgsProject.instance()

        # Prefer project-level WFSLayers entry if present (QGIS project OWS/WFS export list)
        try:
            wfs_ids, ok = project.readListEntry('WFSLayers', '/')
        except Exception:
            wfs_ids, ok = ([], False)

        vector_layers: List[QgsVectorLayer] = []

        if ok and wfs_ids:
            # Iterate only the IDs listed in the project WFSLayers entry
            for lid in [str(i) for i in wfs_ids]:
                try:
                    layer = QgsProject.instance().mapLayer(lid)
                    if not layer:
                        continue
                    if isinstance(layer, QgsVectorLayer):
                        vector_layers.append(layer)
                except Exception:
                    continue

        # If no WFSLayers defined in the project, return empty list (do not
        # fall back to publishing all vector layers).
        return vector_layers

    def _find_layer_by_name(self, type_name: str) -> Optional[QgsVectorLayer]:
        """レイヤー名でレイヤーを検索

        改善: クライアント側が送る TYPENAME はいくつかの形式が混在することがあるため
        以下のマッチングを試みます（順に）:
          1. そのままの layer.id() と一致
          2. URLデコードした値と layer.id() の一致
          3. client-friendly typename (layer.id() を加工したもの) と一致
          4. layer.name() (人間可読名) と一致

        この柔軟性により、パーマリンクや外部クライアントが異なる形式を使っていても
        正しくレイヤーを解決できます。
        """
        from urllib.parse import unquote_plus

        vector_layers = self._get_vector_layers()
        if not type_name:
            return None

        # Try to be resilient to URL-encoded names
        try:
            decoded = unquote_plus(type_name)
        except Exception:
            decoded = type_name

        for layer in vector_layers:
            try:
                lid = layer.id()
                # client-friendly form (stripped leading underscores etc.)
                client_name = self._client_friendly_typename(lid)
                lname = layer.name()

                # Exact match against canonical id
                if lid == type_name or lid == decoded:
                    return layer

                # Match against client-friendly derived name
                if client_name == type_name or client_name == decoded:
                    return layer

                # Match against human-readable layer name
                if lname == type_name or lname == decoded:
                    return layer
            except Exception:
                continue

        return None

    def _get_layer_extent(self, layer: QgsVectorLayer) -> Dict[str, float]:
        """レイヤーの範囲を取得（WGS84に変換）"""
        try:
            extent = layer.extent()
            crs = layer.crs()

            if crs.authid() != 'EPSG:4326':
                transform = QgsCoordinateTransform(crs, QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance())
                extent = transform.transformBoundingBox(extent)

            return {
                'minx': extent.xMinimum(),
                'miny': extent.yMinimum(),
                'maxx': extent.xMaximum(),
                'maxy': extent.yMaximum()
            }
        except:
            return {'minx': -180, 'miny': -90, 'maxx': 180, 'maxy': 90}

    def _query_features(self, layer: QgsVectorLayer, bbox: Optional[str] = None,
                       srs_name: Optional[str] = None, max_features: Optional[int] = None) -> List:
        """レイヤーから地物をクエリ(Phase 1最適化版)"""
        request = QgsFeatureRequest()
        
        # 🚀 Phase 1最適化: インデックスを使用した高速検索
        request.setFlags(QgsFeatureRequest.ExactIntersect)

        # BBOXフィルタ
        if bbox:
            try:
                coords = [float(x) for x in bbox.split(',')]
                if len(coords) == 4:
                    minx, miny, maxx, maxy = coords
                    rect = QgsRectangle(minx, miny, maxx, maxy)

                    # SRS変換
                    if srs_name and srs_name != layer.crs().authid():
                        src_crs = QgsCoordinateReferenceSystem(srs_name)
                        tgt_crs = layer.crs()
                        if src_crs.isValid():
                            transform = QgsCoordinateTransform(src_crs, tgt_crs, QgsProject.instance())
                            rect = transform.transformBoundingBox(rect)

                    request.setFilterRect(rect)
            except:
                pass

        # 🚀 Phase 1最適化: イテレータを使って効率的に取得
        features = []
        iterator = layer.getFeatures(request)
        
        # 最大地物数制限
        count = 0
        for feature in iterator:
            features.append(feature)
            count += 1
            if max_features and count >= max_features:
                break

        return features

    def _features_to_geojson(self, features: List, layer: QgsVectorLayer) -> str:
        """地物をGeoJSONに変換"""
        exporter = QgsJsonExporter(layer)

        # GeoJSON FeatureCollectionの作成
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        for feature in features:
            feature_json = json.loads(exporter.exportFeature(feature))

            # Normalize geometry coordinates: remove Z/M components, coerce strings to numbers
            try:
                geom = feature_json.get('geometry')
                if geom and 'coordinates' in geom and geom['coordinates'] is not None:
                    def _normalize_coords(c):
                        # If this is a nested list (Multi*) then recurse
                        if isinstance(c, list) and c and isinstance(c[0], list):
                            return [_normalize_coords(sub) for sub in c]
                        # If coordinates are flat list like [x, y, z?], coerce first two to floats
                        if isinstance(c, list):
                            out = []
                            # take first two elements only
                            for i in range(min(2, len(c))):
                                try:
                                    out.append(float(c[i]))
                                except Exception:
                                    # try to parse numeric inside strings
                                    try:
                                        out.append(float(str(c[i]).strip()))
                                    except Exception:
                                        out.append(None)
                            # if only one coordinate present, pad with None
                            while len(out) < 2:
                                out.append(None)
                            return out
                        # not a list: try to coerce to two-number list? return as-is
                        return c

                    try:
                        feature_json['geometry']['coordinates'] = _normalize_coords(feature_json['geometry']['coordinates'])
                    except Exception:
                        pass

                # If geometry is invalid (missing coordinates or contains None), skip this feature
                def _coords_valid(c):
                    # Recursively check nested coordinate lists for numeric x,y
                    if isinstance(c, list) and c:
                        if isinstance(c[0], list):
                            return all(_coords_valid(sub) for sub in c)
                        # flat coordinate [x,y]
                        if len(c) >= 2:
                            try:
                                if c[0] is None or c[1] is None:
                                    return False
                                float(c[0]); float(c[1])
                                return True
                            except Exception:
                                return False
                        return False
                    return False

                if not geom or 'coordinates' not in geom or not _coords_valid(geom.get('coordinates')):
                    # skip features without valid geometry
                    try:
                        QgsMessageLog.logMessage(f"⚠️ Skipping feature {feature.id()} due to invalid geometry", "geo_webview", Qgis.Warning)
                    except Exception:
                        pass
                    continue
            except Exception:
                # non-fatal: if any unexpected error in geometry handling, skip this feature
                try:
                    QgsMessageLog.logMessage(f"⚠️ Skipping feature {feature.id()} due to geometry normalization error", "geo_webview", Qgis.Warning)
                except Exception:
                    pass
                continue
            except Exception:
                # non-fatal: leave geometry as-is
                pass

            # try to attach simple style hints extracted from the QGIS symbol
            # NOTE: intentionally do NOT include per-feature style hints inside the
            # GeoJSON properties. Styling is now unified via WFS GetStyles (SLD) and
            # converted to Mapbox/MapLibre style layers by `sld_to_mapbox_style`.
            # Embedding `_qgis_style` or flattening style keys into feature
            # properties caused conflicts and made MapLibre prefer feature-level
            # hints over SLD defaults. By omitting these hints we ensure a single
            # authoritative source of style (the SLD).
            # Leave feature properties untouched.
            pass

            # Try to attach a human-readable label for the feature if available.
            # This uses the layer's displayExpression (if set) or the layer's
            # display field as a fallback.
            try:
                label_text = self._extract_feature_label(layer, feature)
                if label_text is not None:
                    try:
                        s = str(label_text).strip()
                    except Exception:
                        s = ''

                    # Treat empty strings, whitespace-only, and common null-like tokens as no label
                    if s and s.lower() not in ('null', 'none', 'nan'):
                        if 'properties' not in feature_json or feature_json['properties'] is None:
                            feature_json['properties'] = {}
                        feature_json['properties']['label'] = s
                        try:
                            # Log label extraction for debugging in QGIS message log
                            from qgis.core import QgsMessageLog, Qgis
                        except Exception:
                            pass
            except Exception:
                # non-fatal
                pass
            
            # Ensure properties exist
            try:
                if 'properties' not in feature_json or feature_json['properties'] is None:
                    feature_json['properties'] = {}
                # Normalize visibility-related property: if '表示非表示' is missing or null, treat as '表示'
                try:
                    vis = feature_json['properties'].get('表示非表示')
                    if vis is None or (isinstance(vis, str) and vis.strip() == ''):
                        feature_json['properties']['表示非表示'] = '表示'
                except Exception:
                    feature_json['properties']['表示非表示'] = '表示'
            except Exception:
                # non-fatal: continue without property normalization
                pass

            geojson["features"].append(feature_json)

        return json.dumps(geojson, ensure_ascii=False, indent=2)

    def _extract_style_hint(self, layer: QgsVectorLayer, feature) -> Dict[str, Any]:
        """Extract a minimal style hint for a feature from the layer's renderer.

        Returns a dict suitable for client-side MapLibre usage, e.g.
        { 'geomType':'LineString', 'stroke':'#rrggbb', 'stroke-width':2 }

        This is best-effort: we handle simple single-symbol renderers and
        fall back to empty dict for complex cases.
        """
        try:
            from qgis.core import (QgsMarkerSymbol, QgsLineSymbol, QgsFillSymbol,
                                   QgsRuleBasedRenderer, QgsCategorizedSymbolRenderer,
                                   QgsRenderContext, QgsExpressionContext,
                                   QgsExpressionContextUtils)
            renderer = layer.renderer()
            if renderer is None:
                return {}

            # Create render context for symbolForFeature
            context = QgsRenderContext()
            context.setExpressionContext(QgsExpressionContext())
            context.expressionContext().appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
            context.expressionContext().setFeature(feature)

            # Get the actual symbol for this feature
            symbol = renderer.symbolForFeature(feature, context)
            if symbol is None:
                # Fall back to the renderer's default symbol based on renderer type
                try:
                    from qgis.core import (QgsSingleSymbolRenderer, QgsCategorizedSymbolRenderer,
                                           QgsGraduatedSymbolRenderer, QgsRuleBasedRenderer)
                    if isinstance(renderer, QgsSingleSymbolRenderer):
                        symbol = renderer.symbol()
                    elif isinstance(renderer, QgsCategorizedSymbolRenderer):
                        categories = renderer.categories()
                        if categories:
                            symbol = categories[0].symbol()
                    elif isinstance(renderer, QgsGraduatedSymbolRenderer):
                        ranges = renderer.ranges()
                        if ranges:
                            symbol = ranges[0].symbol()
                    elif isinstance(renderer, QgsRuleBasedRenderer):
                        # For rule-based, use the first child rule's symbol
                        root_rule = renderer.rootRule()
                        if root_rule:
                            children = root_rule.children()
                            for child in children:
                                if child.symbol():
                                    symbol = child.symbol()
                                    break
                    # If still None, try renderer.symbol() as last resort
                    if symbol is None:
                        symbol = renderer.symbol()
                except Exception:
                    pass
            if symbol is None:
                return {}

            style = {}

            # Extract geometry type
            if isinstance(symbol, QgsMarkerSymbol):
                style['geomType'] = 'Point'
            elif isinstance(symbol, QgsLineSymbol):
                style['geomType'] = 'LineString'
            elif isinstance(symbol, QgsFillSymbol):
                style['geomType'] = 'Polygon'

            # Extract color information
            try:
                color = symbol.color()
                if hasattr(color, 'name') and color.isValid():
                    if isinstance(symbol, (QgsLineSymbol, QgsMarkerSymbol)):
                        style['stroke'] = color.name()
                    elif isinstance(symbol, QgsFillSymbol):
                        style['fill'] = color.name()
            except Exception:
                pass

            # Extract stroke width for lines
            if isinstance(symbol, QgsLineSymbol):
                try:
                    width = symbol.width()
                    if width > 0:
                        style['stroke-width'] = width
                except Exception:
                    pass

            # Extract fill opacity for polygons
            if isinstance(symbol, QgsFillSymbol):
                try:
                    opacity = symbol.opacity()
                    if opacity < 1.0:
                        style['fill-opacity'] = opacity
                except Exception:
                    pass

            return style
        except Exception:
            return {}

    def _extract_feature_label(self, layer: QgsVectorLayer, feature) -> str:
        """Extract a display label for a feature.

        Tries the layer's displayExpression first, then falls back to the
        display field. Returns an empty string if no label can be determined.
        """
        try:
            # First, prefer explicit labeling settings if present. Many users
            # configure labels via the layer's labeling (QgsPalLayerSettings) —
            # prefer that over the displayExpression/displayField heuristics.
            try:
                lab = None
                try:
                    lab = layer.labeling()
                except Exception:
                    lab = None
                if lab is not None:
                    try:
                        settings = lab.settings()
                    except Exception:
                        settings = None
                    if settings is not None:
                        # settings may expose methods or attributes depending on QGIS
                        # version. Try to obtain an expression first, then a field name.
                        expr_candidate = None
                        field_candidate = None
                        try:
                            if hasattr(settings, 'expression'):
                                expr_candidate = settings.expression() if callable(getattr(settings, 'expression')) else settings.expression
                        except Exception:
                            expr_candidate = None
                        try:
                            if hasattr(settings, 'fieldName'):
                                field_candidate = settings.fieldName() if callable(getattr(settings, 'fieldName')) else settings.fieldName
                        except Exception:
                            field_candidate = None

                        # If an expression is configured in the labeling settings, evaluate it
                        if expr_candidate:
                            try:
                                from qgis.core import QgsExpression, QgsExpressionContext, QgsExpressionContextUtils
                                expr = QgsExpression(str(expr_candidate))
                                ctx = QgsExpressionContext()
                                ctx.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
                                ctx.setFeature(feature)
                                val = expr.evaluate(ctx)
                                if not expr.hasEvalError() and val is not None:
                                    return str(val)
                            except Exception:
                                # fall through to fieldCandidate/displayExpression
                                pass

                        # If a field name is configured for labeling, use the attribute
                        if field_candidate:
                            try:
                                val = feature.attribute(field_candidate)
                                if val is not None:
                                    return str(val)
                            except Exception:
                                pass
            except Exception:
                # ignore labeling inspection errors and continue to other fallbacks
                pass

            # Next, prefer displayExpression (can be an expression like "concat(name, ' (', id, ')')")
            expr_str = ''
            try:
                # method exists on QgsVectorLayer in modern QGIS
                expr_str = layer.displayExpression()
            except Exception:
                expr_str = ''

            if expr_str:
                try:
                    from qgis.core import QgsExpression, QgsExpressionContext, QgsExpressionContextUtils
                    expr = QgsExpression(expr_str)
                    ctx = QgsExpressionContext()
                    # include project and layer scopes so functions like @project can work
                    ctx.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
                    ctx.setFeature(feature)
                    val = expr.evaluate(ctx)
                    if expr.hasEvalError():
                        # fall through to field fallback
                        raise Exception('expression eval error')
                    return '' if val is None else str(val)
                except Exception:
                    pass

            # Fallback: layer.displayField() or form display field
            try:
                df = None
                try:
                    df = layer.displayField()
                except Exception:
                    df = None
                if df:
                    val = feature.attribute(df)
                    return '' if val is None else str(val)
            except Exception:
                pass

        except Exception:
            pass

        return ''

    def _features_to_gml(self, features: List, layer: QgsVectorLayer) -> str:
        """地物をGMLに変換（簡易版）"""
        # Use sanitized layer.id() for XML element names in GML output
        raw_id = layer.id()
        layer_name = re.sub(r'[^A-Za-z0-9_]', '_', str(raw_id))
        crs = layer.crs().authid() if layer.crs().isValid() else 'EPSG:4326'

        gml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs"
                   xmlns:gml="http://www.opengis.net/gml"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/2.0/wfs.xsd">
    """

        for feature in features:
            geom = feature.geometry()
            if geom:
                gml_geom = self._geometry_to_gml(geom, crs)
                properties = self._feature_properties_to_gml(feature)

                gml += f"""  <gml:featureMember>
    <{layer_name} gml:id="{feature.id()}">
      <gml:boundedBy>
        <gml:Envelope srsName="{crs}">
          <gml:lowerCorner>{geom.boundingBox().xMinimum()} {geom.boundingBox().yMinimum()}</gml:lowerCorner>
          <gml:upperCorner>{geom.boundingBox().xMaximum()} {geom.boundingBox().yMaximum()}</gml:upperCorner>
        </gml:Envelope>
      </gml:boundedBy>
      {gml_geom}
      {properties}
    </{layer_name}>
  </gml:featureMember>
"""

        gml += "</wfs:FeatureCollection>"
        return gml

    def _geometry_to_gml(self, geometry, crs: str) -> str:
        """ジオメトリをGMLに変換（簡易版）"""
        if geometry.isEmpty():
            return ""

        wkt = geometry.asWkt()
        wkt_u = wkt.upper()

        # helper: extract list of (x,y) tuples from a coordinate string
        def _coords_from_str(s: str):
            parts = [p.strip() for p in s.split(',') if p.strip()]
            coords = []
            for p in parts:
                nums = re.findall(r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", p)
                if len(nums) >= 2:
                    coords.append((nums[0], nums[1]))
            return coords

        # Point
        if wkt_u.startswith('POINT'):
            inner = wkt[wkt.find('(') + 1:wkt.rfind(')')]
            nums = re.findall(r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", inner)
            if len(nums) >= 2:
                return f'<gml:Point srsName="{crs}"><gml:coordinates>{nums[0]},{nums[1]}</gml:coordinates></gml:Point>'
            return ''

        # MultiPoint
        if wkt_u.startswith('MULTIPOINT'):
            inner = wkt[wkt.find('(') + 1:wkt.rfind(')')]
            # normalize cases like ((x y),(x y)) and (x y, x y)
            inner = inner.replace('),(', ');(').replace(') , (', ');(')
            # split on ');(' or commas
            parts = []
            if ');(' in inner:
                parts = [p.replace('(', '').replace(')', '').strip() for p in inner.split(');(')]
            else:
                parts = [p.strip() for p in inner.split(',') if p.strip()]
            pts = []
            for p in parts:
                nums = re.findall(r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", p)
                if len(nums) >= 2:
                    pts.append((nums[0], nums[1]))
            if not pts:
                return ''
            out = [f'<gml:Point srsName="{crs}"><gml:coordinates>{x},{y}</gml:coordinates></gml:Point>' for x, y in pts]
            members = '\n'.join([f'    <gml:pointMember>{p}</gml:pointMember>' for p in out])
            return f'<gml:MultiPoint srsName="{crs}">\n{members}\n</gml:MultiPoint>'

        # LineString / MultiLineString
        if wkt_u.startswith('LINESTRING') or wkt_u.startswith('MULTILINESTRING'):
            if wkt_u.startswith('LINESTRING'):
                inner = wkt[wkt.find('(') + 1:wkt.rfind(')')]
                coords = _coords_from_str(inner)
                coord_str = ' '.join([f"{x},{y}" for x, y in coords])
                return f'<gml:LineString srsName="{crs}"><gml:coordinates>{coord_str}</gml:coordinates></gml:LineString>'

            # MULTILINESTRING
            inner = wkt[wkt.find('(') + 1:wkt.rfind(')')]
            # extract each linestring by finding parenthesis groups
            groups = re.findall(r"\([^()]*\)", inner)
            members = []
            for g in groups:
                txt = g.replace('(', '').replace(')', '')
                coords = _coords_from_str(txt)
                if coords:
                    coord_str = ' '.join([f"{x},{y}" for x, y in coords])
                    members.append(f'<gml:lineStringMember><gml:LineString srsName="{crs}"><gml:coordinates>{coord_str}</gml:coordinates></gml:LineString></gml:lineStringMember>')
            if members:
                return f'<gml:MultiLineString srsName="{crs}">\n' + '\n'.join(members) + '\n</gml:MultiLineString>'
            return ''

        # Polygon / MultiPolygon (outer rings only)
        if wkt_u.startswith('POLYGON') or wkt_u.startswith('MULTIPOLYGON'):
            if wkt_u.startswith('POLYGON'):
                # extract first linear ring
                inner = wkt[wkt.find('((') + 2:wkt.rfind('))')]
                coords = _coords_from_str(inner)
                coord_str = ' '.join([f"{x},{y}" for x, y in coords])
                return f'<gml:Polygon srsName="{crs}"><gml:outerBoundaryIs><gml:LinearRing><gml:coordinates>{coord_str}</gml:coordinates></gml:LinearRing></gml:outerBoundaryIs></gml:Polygon>'

            # MULTIPOLYGON
            inner = wkt[wkt.find('(') + 1:wkt.rfind(')')]
            # find polygon groups like ((...))
            poly_groups = re.findall(r"\(\([^()]*\)\)", wkt)
            members = []
            for pg in poly_groups:
                ring = pg.replace('(', '').replace(')', '')
                coords = _coords_from_str(ring)
                if coords:
                    coord_str = ' '.join([f"{x},{y}" for x, y in coords])
                    members.append(f'<gml:polygonMember><gml:Polygon srsName="{crs}"><gml:outerBoundaryIs><gml:LinearRing><gml:coordinates>{coord_str}</gml:coordinates></gml:LinearRing></gml:outerBoundaryIs></gml:Polygon></gml:polygonMember>')
            if members:
                return f'<gml:MultiPolygon srsName="{crs}">\n' + '\n'.join(members) + '\n</gml:MultiPolygon>'
            return ''

        # Fallback: return empty string for unsupported/complex types
        return ""

    def _feature_properties_to_gml(self, feature) -> str:
        """地物の属性をGMLに変換"""
        properties = ""
        fields = feature.fields()

        for i in range(fields.count()):
            field = fields.field(i)
            value = feature.attribute(i)
            if value is not None:
                properties += f"      <{field.name()}>{str(value)}</{field.name()}>\n"

        return properties

    def _generate_feature_type_schema(self, layer: QgsVectorLayer) -> str:
        """レイヤーのスキーマをXMLで生成"""
        # Use sanitized layer.id() as the schema element name to ensure ASCII-safe names
        raw_id = layer.id()
        layer_name = re.sub(r'[^A-Za-z0-9_]', '_', str(raw_id))
        # XML名前空間プレフィックスとして有効なASCIIのみの名前を作成
        safe_prefix = ''.join(c for c in layer_name if (ord(c) < 128 and (c.isalnum() or c == '_')))
        if not safe_prefix:
            safe_prefix = 'layer'
        # ユニークな名前空間URIを作成（ASCIIのみ）
        namespace_uri = f"http://www.opengis.net/{safe_prefix}"
        
        fields = layer.fields()

        schema = f"""<?xml version="1.0" encoding="UTF-8"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:gml="http://www.opengis.net/gml"
            xmlns:{safe_prefix}="{namespace_uri}"
            targetNamespace="{namespace_uri}"
            elementFormDefault="qualified">
  <xsd:import namespace="http://www.opengis.net/gml" schemaLocation="http://schemas.opengis.net/gml/3.1.1/base/gml.xsd"/>
  <xsd:element name="{layer_name}" type="{safe_prefix}:{layer_name}Type" substitutionGroup="gml:_Feature"/>
  <xsd:complexType name="{layer_name}Type">
    <xsd:complexContent>
      <xsd:extension base="gml:AbstractFeatureType">
        <xsd:sequence>
"""

        for field in fields:
            field_type = self._qgis_field_type_to_xsd(field.typeName())
            schema += f"""          <xsd:element name="{field.name()}" type="{field_type}" nillable="true" minOccurs="0"/>
"""

        schema += f"""        </xsd:sequence>
      </xsd:extension>
    </xsd:complexContent>
  </xsd:complexType>
</xsd:schema>"""

        return schema

    def _qgis_field_type_to_xsd(self, qgis_type: str) -> str:
        """QGISフィールドタイプをXSDタイプに変換"""
        type_mapping = {
            'integer': 'xsd:int',
            'int4': 'xsd:int',
            'int8': 'xsd:long',
            'real': 'xsd:double',
            'double': 'xsd:double',
            'string': 'xsd:string',
            'text': 'xsd:string',
            'varchar': 'xsd:string',
            'date': 'xsd:date',
            'datetime': 'xsd:dateTime'
        }

        return type_mapping.get(qgis_type.lower(), 'xsd:string')

    def _generate_sld(self, layer: QgsVectorLayer) -> str:
        """レイヤーのSLDを生成"""
        # Use the QGIS layer id as the canonical Name inside the SLD
        # but keep the human-readable Title elsewhere.
        raw_id = layer.id()
        layer_name = str(raw_id)
        
        # Prefer to delegate complex renderer expansion to a reusable helper
        try:
            from . import sld_renderer
            # sld_renderer.renderer_to_sld will try to expand categorized,
            # graduated, rule-based and single-symbol renderers into SLD.
            try:
                return sld_renderer.renderer_to_sld(layer, layer_name)
            except Exception:
                # fall through to legacy behavior on error
                pass
        except Exception:
            # if helper not available or import failed, continue with legacy logic
            pass

        # Legacy fallback: obtain a representative symbol via symbolForFeature
        renderer = layer.renderer()
        if renderer is None:
            return self._generate_default_sld(layer_name)

        # symbolForFeatureを使ってデフォルトシンボルを取得
        symbol = None
        try:
            from qgis.core import (QgsRenderContext, QgsExpressionContext,
                                   QgsExpressionContextUtils, QgsFeature)
            dummy_feature = QgsFeature()
            context = QgsRenderContext()
            context.setExpressionContext(QgsExpressionContext())
            context.expressionContext().appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
            context.expressionContext().setFeature(dummy_feature)
            symbol = renderer.symbolForFeature(dummy_feature, context)
        except Exception as e:
            # symbolForFeatureが失敗したら、デフォルトを使用
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(f"⚠️ symbolForFeature failed for layer {layer_name}: {e}, using default SLD", "geo_webview", Qgis.Warning)
            return self._generate_default_sld(layer_name)

        if symbol is None:
            return self._generate_default_sld(layer_name)

        # シンボルタイプに応じたSLD生成
        from qgis.core import QgsMarkerSymbol, QgsLineSymbol, QgsFillSymbol

        if isinstance(symbol, QgsMarkerSymbol):
            return self._generate_point_sld(layer_name, symbol)
        elif isinstance(symbol, QgsLineSymbol):
            return self._generate_line_sld(layer_name, symbol)
        elif isinstance(symbol, QgsFillSymbol):
            return self._generate_polygon_sld(layer_name, symbol)
        else:
            return self._generate_default_sld(layer_name)

    def _generate_default_sld(self, layer_name: str) -> str:
        """デフォルトSLDを生成"""
        sld = f"""<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.1.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>{layer_name}</Name>
    <UserStyle>
      <Title>Default Style</Title>
      <FeatureTypeStyle>
        <Rule>
          <Name>default</Name>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#808080</CssParameter>
              <CssParameter name="fill-opacity">0.5</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">#000000</CssParameter>
              <CssParameter name="stroke-width">1</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""
        return sld

    def _generate_point_sld(self, layer_name: str, symbol) -> str:
        """ポイントシンボルのSLDを生成"""
        try:
            color = symbol.color()
            size = symbol.size()
            stroke_color = color.name() if color.isValid() else "#000000"
            fill_color = stroke_color
            point_size = size if size > 0 else 6
            
            sld = f"""<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.1.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>{layer_name}</Name>
    <UserStyle>
      <Title>Point Style</Title>
      <FeatureTypeStyle>
        <Rule>
          <Name>point</Name>
          <PointSymbolizer>
            <Graphic>
              <Mark>
                <WellKnownName>circle</WellKnownName>
                <Fill>
                  <CssParameter name="fill">{fill_color}</CssParameter>
                </Fill>
                <Stroke>
                  <CssParameter name="stroke">{stroke_color}</CssParameter>
                  <CssParameter name="stroke-width">1</CssParameter>
                </Stroke>
              </Mark>
              <Size>{point_size}</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""
            return sld
        except Exception:
            return self._generate_default_sld(layer_name)

    def _generate_line_sld(self, layer_name: str, symbol) -> str:
        """ラインシンボルのSLDを生成"""
        try:
            color = symbol.color()
            width = symbol.width()
            stroke_color = color.name() if color.isValid() else "#000000"
            stroke_width = width if width > 0 else 2
            
            sld = f"""<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.1.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>{layer_name}</Name>
    <UserStyle>
      <Title>Line Style</Title>
      <FeatureTypeStyle>
        <Rule>
          <Name>line</Name>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">{stroke_color}</CssParameter>
              <CssParameter name="stroke-width">{stroke_width}</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""
            return sld
        except Exception:
            return self._generate_default_sld(layer_name)

    def _generate_polygon_sld(self, layer_name: str, symbol) -> str:
        """ポリゴンシンボルのSLDを生成"""
        try:
            fill_color_obj = symbol.color()
            stroke_color_obj = symbol.strokeColor()
            stroke_width = symbol.strokeWidth()
            
            stroke_color = stroke_color_obj.name() if stroke_color_obj.isValid() else "#000000"
            stroke_width = stroke_width if stroke_width > 0 else 1
            
            opacity = symbol.opacity()
            fill_opacity = opacity if opacity >= 0 else 0.5
            
            # ブラシなし（NoBrush）の検出
            has_brush = True
            try:
                # シンボルレイヤーからブラシスタイルをチェック
                if hasattr(symbol, 'symbolLayer') and callable(symbol.symbolLayer):
                    sl = symbol.symbolLayer(0)
                    if sl is not None and hasattr(sl, 'brushStyle') and callable(sl.brushStyle):
                        from qgis.PyQt.QtCore import Qt
                        brush_style = sl.brushStyle()
                        if brush_style == Qt.NoBrush:
                            has_brush = False
                            from qgis.core import QgsMessageLog, Qgis
            except Exception as e:
                from qgis.core import QgsMessageLog, Qgis
                QgsMessageLog.logMessage(f"⚠️ Failed to check brush style: {e}", "geo_webview", Qgis.Warning)
            
            # アルファ値（透明度）もチェック
            if has_brush and fill_color_obj is not None:
                try:
                    if hasattr(fill_color_obj, 'alpha') and callable(fill_color_obj.alpha):
                        if fill_color_obj.alpha() == 0:
                            has_brush = False
                            from qgis.core import QgsMessageLog, Qgis
                except Exception:
                    pass
            
            # ブラシなしの場合はLineSymbolizerのみ（枠線のみ）
            if not has_brush:
                from qgis.core import QgsMessageLog, Qgis
                sld = f"""<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.1.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>{layer_name}</Name>
    <UserStyle>
      <Title>Polygon Style (No Fill)</Title>
      <FeatureTypeStyle>
        <Rule>
          <Name>polygon_outline</Name>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">{stroke_color}</CssParameter>
              <CssParameter name="stroke-width">{stroke_width}</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""
                return sld
            
            # 通常のポリゴン（塗りつぶしあり）
            fill_color = fill_color_obj.name() if fill_color_obj.isValid() else "#808080"
            from qgis.core import QgsMessageLog, Qgis
            
            sld = f"""<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.1.0" xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd">
  <NamedLayer>
    <Name>{layer_name}</Name>
    <UserStyle>
      <Title>Polygon Style</Title>
      <FeatureTypeStyle>
        <Rule>
          <Name>polygon</Name>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">{fill_color}</CssParameter>
              <CssParameter name="fill-opacity">{fill_opacity}</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">{stroke_color}</CssParameter>
              <CssParameter name="stroke-width">{stroke_width}</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>"""
            return sld
        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(f"❌ Failed to generate polygon SLD: {e}", "geo_webview", Qgis.Critical)
            return self._generate_default_sld(layer_name)