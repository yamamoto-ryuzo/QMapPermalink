#!/usr/bin/env python3
"""
OpenLayersインタラクティブマップのテスト用HTML生成
"""

import urllib.request

def generate_test_html():
    """テスト用HTMLファイルを生成"""
    
    test_url = "http://localhost:8089/qgis-map?x=15557945.984400&y=4257187.015550&scale=21280.2&crs=EPSG:3857&rotation=0.00"
    
    print("🌐 OpenLayersインタラクティブマップのテスト")
    print("="*50)
    print(f"📍 テストURL: {test_url}")
    
    try:
        with urllib.request.urlopen(test_url, timeout=15) as response:
            html_content = response.read().decode('utf-8')
            
        # HTMLファイルとして保存
        test_file_path = "openlayers_interactive_test.html"
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"✅ HTMLファイルを生成しました: {test_file_path}")
        print(f"📊 サイズ: {len(html_content):,} 文字")
        
        # 重要な要素をチェック
        checks = [
            ("OpenLayers CDN", "https://cdn.jsdelivr.net/npm/ol@v8.2.0"),
            ("マップコンテナ", 'id="map"'),
            ("インタラクティブコントロール", "resetView()"),
            ("WMSエンドポイント参照", "/wms"),
            ("座標表示", "current-coords"),
            ("マップ初期化", "new ol.Map")
        ]
        
        print(f"\n🔍 HTML内容チェック:")
        for name, pattern in checks:
            if pattern in html_content:
                print(f"   ✅ {name}: 確認")
            else:
                print(f"   ❌ {name}: 見つからない")
        
        print(f"\n🚀 テスト手順:")
        print(f"1️⃣ ブラウザで {test_file_path} を開く")
        print(f"2️⃣ インタラクティブマップが表示されることを確認")
        print(f"3️⃣ ドラッグ、ズーム、コントロールボタンをテスト")
        print(f"4️⃣ 座標情報が動的に更新されることを確認")
        
        return test_file_path
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

def start_browser_test(file_path):
    """ブラウザでテストを開始"""
    if file_path:
        import os
        import subprocess
        
        try:
            # Windowsでデフォルトブラウザを開く
            subprocess.run(['start', file_path], shell=True, check=True)
            print(f"🌐 ブラウザでテストファイルを開きました")
        except Exception as e:
            print(f"⚠️ ブラウザを自動で開けませんでした: {e}")
            print(f"📌 手動で {file_path} をブラウザで開いてください")

if __name__ == "__main__":
    print("🧪 OpenLayersインタラクティブマップテスト")
    
    try:
        test_file = generate_test_html()
        if test_file:
            start_browser_test(test_file)
            
            print(f"\n📋 期待される動作:")
            print(f"✅ フルスクリーンインタラクティブマップ")
            print(f"✅ 初期位置: パーマリンクで指定した座標")
            print(f"✅ 自由なパン・ズーム操作")
            print(f"✅ リアルタイム座標表示")
            print(f"✅ コントロールボタン（ホーム、ズーム、全画面）")
            print(f"✅ WMSエンドポイントからの動的画像更新")
            
    except KeyboardInterrupt:
        print("\n⏹️ テスト中断")
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()