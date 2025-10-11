#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMapPermalink HTTPレスポンス内容詳細確認ツール

実際のHTTPレスポンス内容を詳しく確認して、
問題の原因を特定します。
"""

import urllib.request
import urllib.error

def inspect_response(name, url):
    """HTTPレスポンスの詳細を確認"""
    print(f"\n📋 {name} レスポンス詳細")
    print("=" * 60)
    print(f"🌐 URL: {url}")
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8', errors='ignore')
            
            print(f"📊 ステータス: {response.getcode()}")
            print(f"📄 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"📏 Content-Length: {len(content)} bytes")
            print(f"🔗 実際のURL: {response.geturl()}")
            
            # ヘッダー情報
            print(f"\n📨 レスポンスヘッダー:")
            for key, value in response.headers.items():
                print(f"  {key}: {value}")
            
            # コンテンツのプレビュー
            print(f"\n📄 レスポンス内容 (最初の500文字):")
            print("-" * 50)
            print(content[:500])
            print("-" * 50)
            
            # エラーメッセージの検索
            error_indicators = [
                'error', 'Error', 'ERROR',
                'エラー', 'failed', 'Failed',
                'exception', 'Exception',
                'traceback', 'Traceback'
            ]
            
            found_errors = []
            for indicator in error_indicators:
                if indicator in content:
                    found_errors.append(indicator)
            
            if found_errors:
                print(f"\n⚠️ エラー指標を検出: {', '.join(found_errors)}")
            else:
                print(f"\n✅ エラー指標は見つかりませんでした")
            
            # 期待されるコンテンツの確認
            if name == "OpenLayers Map":
                expected_items = [
                    ('OpenLayers CDN', 'cdn.jsdelivr.net/npm/ol@'),
                    ('マップコンテナ', 'id="map"'),  
                    ('OpenLayers Map', 'new ol.Map('),
                    ('マップ初期化', 'ol.View(')
                ]
            elif name == "QGIS Real Image":
                expected_items = [
                    ('Base64画像', 'data:image/png;base64,'),
                    ('画像タグ', '<img src='),
                    ('QGIS画像', 'QGIS'),
                    ('画像表示', 'image')
                ]
            else:
                expected_items = []
            
            print(f"\n🔍 期待されるコンテンツの確認:")
            for item_name, search_text in expected_items:
                if search_text in content:
                    print(f"  ✅ {item_name}: 見つかりました")
                else:
                    print(f"  ❌ {item_name}: 見つかりませんでした")
            
            return True
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTPエラー: {e.code} - {e.reason}")
        try:
            error_content = e.read().decode('utf-8', errors='ignore')
            print(f"📄 エラー内容:")
            print(error_content[:300])
        except Exception:
            pass
        return False
    except Exception as e:
        print(f"❌ リクエストエラー: {e}")
        return False

def main():
    """メイン確認実行"""
    print("🔍 QMapPermalink HTTPレスポンス詳細確認")
    
    # サーバーポート
    server_port = 8089
    base_params = "lat=35.681236&lon=139.767125&z=16"
    
    # OpenLayersマップ確認
    inspect_response(
        "OpenLayers Map",
        f"http://localhost:{server_port}/qgis-map?{base_params}"
    )
    
    # QGIS実画像確認  
    inspect_response(
        "QGIS Real Image", 
        f"http://localhost:{server_port}/qgis-image?{base_params}&width=400&height=300"
    )
    
    # 削除されたPNGエンドポイント確認
    inspect_response(
        "Deleted PNG Endpoint",
        f"http://localhost:{server_port}/qgis-png?{base_params}"
    )

if __name__ == "__main__":
    main()