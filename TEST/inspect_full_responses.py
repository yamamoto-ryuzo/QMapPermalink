#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTPレスポンス完全内容確認ツール

レスポンスの全内容を確認して、実際に何が生成されているかを詳しく確認
"""

import urllib.request
import urllib.error

def inspect_full_response(name, url):
    """HTTPレスポンスの完全内容を確認"""
    print(f"\n📋 {name} レスポンス完全内容")
    print("=" * 80)
    print(f"🌐 URL: {url}")
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8', errors='ignore')
            
            print(f"📊 ステータス: {response.getcode()}")
            print(f"📄 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"📏 Content-Length: {len(content)} bytes")
            
            # 完全なコンテンツを表示
            print(f"\n📄 完全なレスポンス内容:")
            print("-" * 80)
            print(content)
            print("-" * 80)
            
            # キーワード検索
            keywords = {
                'OpenLayers CDN': 'cdn.jsdelivr.net/npm/ol@',
                'マップコンテナ': 'id="map"',
                'OpenLayers初期化': 'new ol.Map(',
                'ビュー設定': 'new ol.View(',
                'Base64画像': 'data:image/png;base64,',
                '画像タグ': '<img src=',
                'エラーメッセージ': 'error-message',
                'JavaScriptエラー': 'Error',
                'QGIS情報': 'QGIS'
            }
            
            print(f"\n🔍 キーワード検索結果:")
            for keyword_name, search_text in keywords.items():
                if search_text in content:
                    # 見つかった場合、その周辺テキストも表示
                    index = content.find(search_text)
                    surrounding = content[max(0, index-50):index+100]
                    print(f"  ✅ {keyword_name}: 見つかりました")
                    print(f"      周辺テキスト: ...{surrounding}...")
                else:
                    print(f"  ❌ {keyword_name}: 見つかりませんでした")
            
            return True
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def main():
    """メイン確認実行"""
    print("🔍 QMapPermalink HTTPレスポンス完全内容確認")
    
    # サーバーポート
    server_port = 8089
    base_params = "lat=35.681236&lon=139.767125&z=16"
    
    # OpenLayersマップ確認
    inspect_full_response(
        "OpenLayers Map",
        f"http://localhost:{server_port}/qgis-map?{base_params}"
    )
    
    # QGIS実画像確認  
    inspect_full_response(
        "QGIS Real Image", 
        f"http://localhost:{server_port}/qgis-image?{base_params}&width=400&height=300"
    )

if __name__ == "__main__":
    main()