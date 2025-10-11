#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenLayersマップレスポンステスト
QMapPermalinkのHTTPサーバーから返されるHTMLを確認するスクリプト
"""

import urllib.request
import urllib.parse
from datetime import datetime

def test_qmap_server():
    """QMapPermalinkサーバーのレスポンスをテスト"""
    
    # テスト用のパラメータ
    params = {
        'x': '15557945.984400',
        'y': '4257187.015550', 
        'scale': '21280.2',
        'crs': 'EPSG:3857',
        'rotation': '0.00'
    }
    
    # URLを構築
    base_url = 'http://localhost:8089/qgis-map'
    query_string = urllib.parse.urlencode(params)
    full_url = f"{base_url}?{query_string}"
    
    print(f"🔍 テスト開始: {datetime.now()}")
    print(f"📡 リクエストURL: {full_url}")
    print("-" * 80)
    
    try:
        # HTTPリクエストを送信
        with urllib.request.urlopen(full_url, timeout=10) as response:
            content_type = response.headers.get('Content-Type', 'unknown')
            status_code = response.getcode()
            content = response.read().decode('utf-8')
            
            print(f"✅ ステータス: {status_code}")
            print(f"📄 Content-Type: {content_type}")
            print(f"📊 レスポンサイズ: {len(content)} 文字")
            print("-" * 80)
            
            # HTMLの主要部分をチェック
            checks = [
                ('DOCTYPE html', '<!DOCTYPE html' in content),
                ('OpenLayers CSS', 'ol@v8.2.0/ol.css' in content or 'ol.css' in content),
                ('OpenLayers JS', 'ol@v8.2.0/dist/ol.js' in content or 'ol.js' in content),
                ('マップコンテナ', '<div id="map"' in content),
                ('new ol.Map', 'new ol.Map' in content),
                ('ol.proj.fromLonLat', 'ol.proj.fromLonLat' in content)
            ]
            
            print("🔍 HTMLコンテンツ解析:")
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"  {status} {check_name}: {'OK' if result else 'NG'}")
            
            print("-" * 80)
            
            # エラーメッセージをチェック
            if 'error-message' in content:
                print("⚠️ エラーメッセージが含まれています:")
                error_start = content.find('error-message')
                error_section = content[max(0, error_start-50):error_start+200]
                print(f"  {error_section}")
            
            # HTMLの最初と最後の部分を表示
            print("📝 HTMLの最初の500文字:")
            print(content[:500])
            print("\n" + "." * 50)
            print("📝 HTMLの最後の500文字:")
            print(content[-500:])
            
            # HTMLを保存
            output_file = f"debug_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"\n💾 完全なHTMLを保存しました: {output_file}")
            
    except urllib.error.URLError as e:
        print(f"❌ 接続エラー: {e}")
        print("   サーバーが起動していることを確認してください")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")

if __name__ == "__main__":
    test_qmap_server()