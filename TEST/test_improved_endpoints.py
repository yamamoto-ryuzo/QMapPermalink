#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改善されたQMapPermalinkエンドポイントテスト v1.9.7

PNG直接エンドポイントを削除し、安定した2つのエンドポイントをテスト：
- /qgis-map: OpenLayersインタラクティブマップ
- /qgis-image: QGIS実画像HTML埋め込み
"""

import requests
import time

def discover_qmap_server():
    """QMapPermalinkサーバーを発見"""
    print("🔍 QMapPermalinkサーバー発見中...")
    
    for port in range(8089, 8099):
        try:
            response = requests.get(f"http://localhost:{port}/qgis-map", timeout=2)
            if response.status_code == 200:
                print(f"✅ QMapPermalinkサーバー発見: ポート {port}")
                return port
        except requests.exceptions.RequestException:
            continue
    
    print("❌ QMapPermalinkサーバーが見つかりません")
    print("   QGISでQMapPermalinkプラグインを有効化し、HTTPサーバーを起動してください")
    return None

def test_endpoint(name, url, expected_content_checks):
    """エンドポイントをテスト"""
    print(f"\n🧪 {name} エンドポイントテスト")
    print(f"📡 URL: {url}")
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=30)
        duration = time.time() - start_time
        
        print(f"⏱️ レスポンス時間: {duration:.2f}秒")
        print(f"📊 ステータス: {response.status_code}")
        print(f"📄 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"📏 Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            # コンテンツチェック
            content = response.text
            all_checks_passed = True
            
            for check_name, check_value in expected_content_checks.items():
                if check_value in content:
                    print(f"✅ {check_name}: 見つかりました")
                else:
                    print(f"❌ {check_name}: 見つかりませんでした")
                    all_checks_passed = False
            
            if all_checks_passed:
                print(f"🎉 {name} エンドポイント: すべてのテストに合格")
                return True
            else:
                print(f"⚠️ {name} エンドポイント: 一部のテストが失敗")
                return False
        else:
            print(f"❌ {name} エンドポイント: HTTPエラー {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ {name} エンドポイント: タイムアウト (30秒)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name} エンドポイント: リクエストエラー - {e}")
        return False

def main():
    """メインテスト実行"""
    print("🚀 QMapPermalink v1.9.7 改善エンドポイントテスト")
    print("=" * 60)
    
    # サーバー発見
    server_port = discover_qmap_server()
    if not server_port:
        return
    
    # テストパラメータ（東京駅周辺）
    base_params = "lat=35.681236&lon=139.767125&z=16"
    
    # テスト結果
    results = {}
    
    # OpenLayersマップエンドポイントテスト
    results["OpenLayers"] = test_endpoint(
        "OpenLayers Map",
        f"http://localhost:{server_port}/qgis-map?{base_params}",
        {
            "OpenLayers CDN": "cdn.jsdelivr.net/npm/ol@",
            "マップコンテナ": 'id="map"',
            "QMap Permalink": "QMap Permalink",
            "Interactive Map": "Interactive Map",
            "JavaScript初期化": "ol.Map("
        }
    )
    
    # QGIS実画像エンドポイントテスト
    results["QGIS Image"] = test_endpoint(
        "QGIS Real Image",
        f"http://localhost:{server_port}/qgis-image?{base_params}&width=400&height=300",
        {
            "画像埋め込み": "data:image/png;base64,",
            "QGIS Real Image": "QGIS Real Image",
            "QMap Permalink": "QMap Permalink",
            "実画像表示": "QGISマップビュー（実画像）",
            "画像クリック機能": "onclick="
        }
    )
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    passed_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    for endpoint_name, passed in results.items():
        status = "✅ 合格" if passed else "❌ 失敗"
        print(f"  {endpoint_name:15} {status}")
    
    print(f"\n🎯 総合結果: {passed_count}/{total_count} エンドポイントが正常動作")
    
    if passed_count == total_count:
        print("🎉 すべてのエンドポイントが正常に動作しています！")
        print("💡 PNG直接エンドポイントの削除により、HTTPサーバーの安定性が向上しました")
    else:
        print("⚠️ 一部のエンドポイントに問題があります")
        print("🔧 QGISプラグインの設定やネットワーク接続を確認してください")
    
    print("\n📋 利用可能なエンドポイント:")
    print(f"  🗺️ OpenLayersマップ: http://localhost:{server_port}/qgis-map")
    print(f"  🖼️ QGIS実画像:      http://localhost:{server_port}/qgis-image")

if __name__ == "__main__":
    main()