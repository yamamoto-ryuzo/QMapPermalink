# -*- coding: utf-8 -*-
"""
QGISのマップビューをWMSのように配信するための拡張機能

このモジュールは、現在のQMapPermalinkプラグインに以下の機能を追加します：
1. WMS GetMapリクエストの処理
2. タイル配信機能
3. GetCapabilities機能
4. レイヤー情報の取得
"""

import math
import json
from xml.etree.ElementTree import Element, SubElement, tostring


class QGISWMSLikeService:
    """QGISマップビューをWMSのように配信するクラス"""
    
    def __init__(self, iface, webmap_generator):
        """
        Args:
            iface: QGISインターフェース
            webmap_generator: WebMapGeneratorインスタンス
        """
        self.iface = iface
        self.webmap_generator = webmap_generator
        
    def handle_wms_request(self, conn, params):
        """WMSリクエストを処理
        
        サポートするリクエスト：
        - GetMap: 指定されたBBOXとサイズで地図画像を返す
        - GetCapabilities: サービスの機能と利用可能なレイヤーを返す
        - GetFeatureInfo: 指定座標の地物情報を返す
        """
        from qgis.core import QgsMessageLog, Qgis
        
        # リクエストタイプを取得
        request = params.get('REQUEST', [''])[0].upper()
        service = params.get('SERVICE', [''])[0].upper()
        
        if service != 'WMS':
            self._send_error_response(conn, "InvalidParameterValue", 
                                    "SERVICE parameter must be WMS")
            return
            
        QgsMessageLog.logMessage(f"🌐 WMS Request: {request}", "QMapPermalink", Qgis.Info)
        
        if request == 'GETCAPABILITIES':
            self._handle_get_capabilities(conn, params)
        elif request == 'GETMAP':
            self._handle_get_map(conn, params)
        elif request == 'GETFEATUREINFO':
            self._handle_get_feature_info(conn, params)
        else:
            self._send_error_response(conn, "InvalidRequest", 
                                    f"Request {request} is not supported")
    
    def _handle_get_capabilities(self, conn, params):
        """GetCapabilitiesリクエストを処理"""
        from qgis.core import QgsProject, QgsMessageLog, Qgis
        
        QgsMessageLog.logMessage("📋 Generating WMS GetCapabilities", "QMapPermalink", Qgis.Info)
        
        # 現在のプロジェクトからレイヤー情報を取得
        project = QgsProject.instance()
        layers = project.mapLayers()
        
        # XML Capabilitiesレスポンスを生成
        root = Element('WMS_Capabilities', version='1.3.0')
        
        # Service section
        service = SubElement(root, 'Service')
        SubElement(service, 'Name').text = 'WMS'
        SubElement(service, 'Title').text = 'QGIS Map Permalink WMS Service'
        SubElement(service, 'Abstract').text = 'WMS service for current QGIS map view'
        
        # Capability section
        capability = SubElement(root, 'Capability')
        
        # Request section
        request_elem = SubElement(capability, 'Request')
        
        # GetCapabilities
        get_cap = SubElement(request_elem, 'GetCapabilities')
        SubElement(get_cap, 'Format').text = 'text/xml'
        
        # GetMap
        get_map = SubElement(request_elem, 'GetMap')
        SubElement(get_map, 'Format').text = 'image/png'
        SubElement(get_map, 'Format').text = 'image/jpeg'
        
        # Layer section
        layer_elem = SubElement(capability, 'Layer')
        SubElement(layer_elem, 'Title').text = 'QGIS Map View'
        
        # 各レイヤーの情報を追加
        for layer_id, layer in layers.items():
            layer_sub = SubElement(layer_elem, 'Layer', queryable='1')
            SubElement(layer_sub, 'Name').text = layer.name()
            SubElement(layer_sub, 'Title').text = layer.name()
            
            # CRS情報
            crs = layer.crs()
            if crs.isValid():
                SubElement(layer_sub, 'CRS').text = crs.authid()
            
            # Extent情報
            extent = layer.extent()
            if not extent.isEmpty():
                bbox = SubElement(layer_sub, 'BoundingBox', CRS=crs.authid())
                bbox.set('minx', str(extent.xMinimum()))
                bbox.set('miny', str(extent.yMinimum()))
                bbox.set('maxx', str(extent.xMaximum()))
                bbox.set('maxy', str(extent.yMaximum()))
        
        # XMLレスポンスを送信
        xml_content = tostring(root, encoding='utf-8', method='xml')
        xml_string = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_content.decode('utf-8')
        
        self._send_xml_response(conn, xml_string)
    
    def _handle_get_map(self, conn, params):
        """GetMapリクエストを処理"""
        from qgis.core import QgsMessageLog, Qgis, QgsRectangle, QgsCoordinateReferenceSystem
        
        QgsMessageLog.logMessage("🗺️ Processing WMS GetMap request", "QMapPermalink", Qgis.Info)
        
        try:
            # 必須パラメータを取得
            bbox = params.get('BBOX', [None])[0]
            width = int(params.get('WIDTH', ['800'])[0])
            height = int(params.get('HEIGHT', ['600'])[0])
            crs = params.get('CRS', ['EPSG:4326'])[0]
            format_type = params.get('FORMAT', ['image/png'])[0]
            
            if not bbox:
                self._send_error_response(conn, "MissingParameterValue", 
                                        "BBOX parameter is required")
                return
            
            # BBOXを解析
            bbox_coords = [float(x) for x in bbox.split(',')]
            if len(bbox_coords) != 4:
                self._send_error_response(conn, "InvalidParameterValue", 
                                        "BBOX must contain 4 coordinates")
                return
            
            minx, miny, maxx, maxy = bbox_coords
            
            QgsMessageLog.logMessage(f"📐 GetMap params: BBOX={bbox}, SIZE={width}x{height}, CRS={crs}", 
                                   "QMapPermalink", Qgis.Info)
            
            # QGISマップキャンバスを指定された範囲に設定
            canvas = self.iface.mapCanvas()
            if not canvas:
                self._send_error_response(conn, "InternalError", "Map canvas not available")
                return
            
            # 座標系を設定
            target_crs = QgsCoordinateReferenceSystem(crs)
            if not target_crs.isValid():
                self._send_error_response(conn, "InvalidCRS", f"CRS {crs} is not valid")
                return
            
            # 範囲を設定
            extent = QgsRectangle(minx, miny, maxx, maxy)
            
            # WebMapGeneratorを使って画像を生成
            if self.webmap_generator and hasattr(self.webmap_generator, 'generate_map_image_from_extent'):
                # 新しいメソッドを使用（後で実装）
                image_data, content_type, success = self.webmap_generator.generate_map_image_from_extent(
                    extent, target_crs, width, height, format_type)
                
                if success:
                    self._send_binary_response(conn, 200, "OK", image_data, content_type)
                else:
                    self._send_error_response(conn, "InternalError", "Failed to generate map image")
            else:
                # 既存のPNG生成機能を使用
                navigation_data = {
                    'lat': (miny + maxy) / 2,
                    'lon': (minx + maxx) / 2,
                    'scale': self._calculate_scale_from_bbox(extent, width, height)
                }
                
                result = self.webmap_generator.generate_qgis_png_response(navigation_data, width, height)
                if isinstance(result, tuple) and len(result) >= 3:
                    image_data, content_type, success = result[:3]
                    if success:
                        self._send_binary_response(conn, 200, "OK", image_data, content_type)
                    else:
                        self._send_error_response(conn, "InternalError", "Failed to generate map image")
                else:
                    self._send_error_response(conn, "InternalError", "Invalid response from image generator")
                    
        except Exception as e:
            QgsMessageLog.logMessage(f"❌ GetMap error: {e}", "QMapPermalink", Qgis.Critical)
            self._send_error_response(conn, "InternalError", str(e))
    
    def _handle_get_feature_info(self, conn, params):
        """GetFeatureInfoリクエストを処理"""
        from qgis.core import QgsMessageLog, Qgis
        
        QgsMessageLog.logMessage("ℹ️ Processing WMS GetFeatureInfo request", "QMapPermalink", Qgis.Info)
        
        try:
            # 座標パラメータを取得
            i = int(params.get('I', ['0'])[0])  # ピクセル座標X
            j = int(params.get('J', ['0'])[0])  # ピクセル座標Y
            info_format = params.get('INFO_FORMAT', ['text/plain'])[0]
            
            # 地物情報を取得（簡略化された実装）
            feature_info = self._get_feature_info_at_pixel(i, j)
            
            if info_format.lower() == 'application/json':
                response_data = json.dumps(feature_info, ensure_ascii=False, indent=2)
                self._send_json_response(conn, response_data)
            else:
                # テキスト形式
                response_text = self._format_feature_info_as_text(feature_info)
                self._send_text_response(conn, response_text)
                
        except Exception as e:
            QgsMessageLog.logMessage(f"❌ GetFeatureInfo error: {e}", "QMapPermalink", Qgis.Critical)
            self._send_error_response(conn, "InternalError", str(e))
    
    def handle_tile_request(self, conn, z, x, y, params):
        """タイルリクエストを処理 (Slippy Map Tiles)
        
        URL形式: /tiles/{z}/{x}/{y}.png
        """
        from qgis.core import QgsMessageLog, Qgis
        
        QgsMessageLog.logMessage(f"🗺️ Tile request: Z={z}, X={x}, Y={y}", "QMapPermalink", Qgis.Info)
        
        try:
            # タイル座標からBBOXを計算
            bbox = self._tile_to_bbox(int(z), int(x), int(y))
            
            # 256x256のタイル画像を生成
            tile_size = 256
            
            if self.webmap_generator:
                # ナビゲーションデータを作成
                center_lat = (bbox['south'] + bbox['north']) / 2
                center_lon = (bbox['west'] + bbox['east']) / 2
                
                navigation_data = {
                    'lat': center_lat,
                    'lon': center_lon,
                    'scale': self._zoom_to_scale(int(z))
                }
                
                result = self.webmap_generator.generate_qgis_png_response(
                    navigation_data, tile_size, tile_size)
                
                if isinstance(result, tuple) and len(result) >= 3:
                    image_data, content_type, success = result[:3]
                    if success:
                        # タイル用のキャッシュヘッダーを追加
                        headers = {
                            'Cache-Control': 'public, max-age=3600',
                            'Content-Type': content_type
                        }
                        self._send_binary_response_with_headers(conn, 200, "OK", 
                                                             image_data, headers)
                    else:
                        self._send_error_response(conn, "InternalError", 
                                                "Failed to generate tile image")
                else:
                    self._send_error_response(conn, "InternalError", 
                                            "Invalid response from image generator")
            else:
                self._send_error_response(conn, "ServiceUnavailable", 
                                        "WebMap generator not available")
                
        except Exception as e:
            QgsMessageLog.logMessage(f"❌ Tile generation error: {e}", "QMapPermalink", Qgis.Critical)
            self._send_error_response(conn, "InternalError", str(e))
    
    def _tile_to_bbox(self, z, x, y):
        """タイル座標をWGS84 BBOXに変換"""
        n = 2.0 ** z
        lon_deg_west = x / n * 360.0 - 180.0
        lon_deg_east = (x + 1) / n * 360.0 - 180.0
        
        lat_rad_north = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        lat_rad_south = math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n)))
        
        lat_deg_north = math.degrees(lat_rad_north)
        lat_deg_south = math.degrees(lat_rad_south)
        
        return {
            'west': lon_deg_west,
            'east': lon_deg_east,
            'north': lat_deg_north,
            'south': lat_deg_south
        }
    
    def _zoom_to_scale(self, zoom):
        """ズームレベルをスケールに変換"""
        # Web Mercatorのズームレベルからスケールを概算
        # ズーム0で約1:500,000,000のスケール
        return 559082264.0 / (2 ** zoom)
    
    def _calculate_scale_from_bbox(self, extent, width, height):
        """BBOXとピクセルサイズからスケールを計算"""
        # 簡略化された計算（実際にはCRSを考慮する必要がある）
        extent_width = extent.width()
        meters_per_pixel = extent_width / width
        # 1インチ = 0.0254メートル、1インチ = 96ピクセル（標準DPI）
        scale = meters_per_pixel * 96 / 0.0254
        return scale
    
    def _get_feature_info_at_pixel(self, pixel_x, pixel_y):
        """指定されたピクセル座標の地物情報を取得"""
        from qgis.core import QgsProject
        
        # 簡略化された実装
        feature_info = {
            'pixel_coordinates': {'x': pixel_x, 'y': pixel_y},
            'layers': []
        }
        
        # 現在のプロジェクトからレイヤー情報を取得
        project = QgsProject.instance()
        layers = project.mapLayers()
        
        for layer_id, layer in layers.items():
            if layer.isValid():
                layer_info = {
                    'name': layer.name(),
                    'type': layer.type(),
                    'features': []  # 実際の実装では空間検索を行う
                }
                feature_info['layers'].append(layer_info)
        
        return feature_info
    
    def _format_feature_info_as_text(self, feature_info):
        """地物情報をテキスト形式でフォーマット"""
        lines = [f"Feature Info at pixel ({feature_info['pixel_coordinates']['x']}, {feature_info['pixel_coordinates']['y']})"]
        lines.append("")
        
        for layer in feature_info['layers']:
            lines.append(f"Layer: {layer['name']} ({layer['type']})")
            if layer['features']:
                for feature in layer['features']:
                    lines.append(f"  - {feature}")
            else:
                lines.append("  - No features found")
            lines.append("")
        
        return "\n".join(lines)
    
    # HTTP レスポンス送信メソッド群
    def _send_error_response(self, conn, error_code, error_message):
        """WMSエラーレスポンスを送信"""
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<ServiceExceptionReport version="1.3.0">
    <ServiceException code="{error_code}">{error_message}</ServiceException>
</ServiceExceptionReport>"""
        
        response = f"HTTP/1.1 400 Bad Request\r\n"
        response += f"Content-Type: application/vnd.ogc.se_xml\r\n"
        response += f"Content-Length: {len(xml_content.encode('utf-8'))}\r\n"
        response += f"Connection: close\r\n\r\n"
        response += xml_content
        
        conn.sendall(response.encode('utf-8'))
    
    def _send_xml_response(self, conn, xml_content):
        """XMLレスポンスを送信"""
        response = f"HTTP/1.1 200 OK\r\n"
        response += f"Content-Type: text/xml\r\n"
        response += f"Content-Length: {len(xml_content.encode('utf-8'))}\r\n"
        response += f"Connection: close\r\n\r\n"
        response += xml_content
        
        conn.sendall(response.encode('utf-8'))
    
    def _send_json_response(self, conn, json_content):
        """JSONレスポンスを送信"""
        response = f"HTTP/1.1 200 OK\r\n"
        response += f"Content-Type: application/json\r\n"
        response += f"Content-Length: {len(json_content.encode('utf-8'))}\r\n"
        response += f"Connection: close\r\n\r\n"
        response += json_content
        
        conn.sendall(response.encode('utf-8'))
    
    def _send_text_response(self, conn, text_content):
        """テキストレスポンスを送信"""
        response = f"HTTP/1.1 200 OK\r\n"
        response += f"Content-Type: text/plain\r\n"
        response += f"Content-Length: {len(text_content.encode('utf-8'))}\r\n"
        response += f"Connection: close\r\n\r\n"
        response += text_content
        
        conn.sendall(response.encode('utf-8'))
    
    def _send_binary_response(self, conn, status_code, status_text, data, content_type):
        """バイナリレスポンスを送信"""
        response = f"HTTP/1.1 {status_code} {status_text}\r\n"
        response += f"Content-Type: {content_type}\r\n"
        response += f"Content-Length: {len(data)}\r\n"
        response += f"Connection: close\r\n\r\n"
        
        conn.sendall(response.encode('ascii'))
        conn.sendall(data)
    
    def _send_binary_response_with_headers(self, conn, status_code, status_text, data, headers):
        """ヘッダー付きバイナリレスポンスを送信"""
        response = f"HTTP/1.1 {status_code} {status_text}\r\n"
        
        for header, value in headers.items():
            response += f"{header}: {value}\r\n"
        
        response += f"Content-Length: {len(data)}\r\n"
        response += f"Connection: close\r\n\r\n"
        
        conn.sendall(response.encode('ascii'))
        conn.sendall(data)


# 使用例とテスト用のコード
if __name__ == "__main__":
    print("QGISWMSLikeService モジュール")
    print("このモジュールは、QGISのマップビューをWMSのように配信するための機能を提供します。")
    print("\n主な機能:")
    print("1. WMS GetCapabilities - サービス機能の取得")
    print("2. WMS GetMap - 指定されたBBOXでの地図画像取得")
    print("3. WMS GetFeatureInfo - 地物情報の取得")
    print("4. タイル配信 - Slippy Map Tiles形式での配信")
    print("\n使用方法:")
    print("- /wms?SERVICE=WMS&REQUEST=GetCapabilities")
    print("- /wms?SERVICE=WMS&REQUEST=GetMap&BBOX=139,35,140,36&WIDTH=800&HEIGHT=600&CRS=EPSG:4326")
    print("- /tiles/{z}/{x}/{y}.png")