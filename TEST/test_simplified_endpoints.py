#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMapPermalink v1.9.7 簡易エンドポイントテスト（標準ライブラリのみ）

PNG直接エンドポイントを削除し、安定した2つのエンドポイントをテスト：
- /qgis-map: OpenLayersインタラクティブマップ  
- /qgis-image: QGIS実画像HTML埋め込み
"""

import urllib.request
import urllib.error
import socket
import time

def discover_qmap_server():
    """QMapPermalinkサーバーを発見"""
    print("🔍 QMapPermalinkサーバー発見中...")
    
    for port in range(8089, 8099):
        try:
            # ソケットでポート確認
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                # HTTPリクエストで確認
                url = f"http://localhost:{port}/qgis-map"
                req = urllib.request.Request(url)
                try:
                    with urllib.request.urlopen(req, timeout=3) as response:
                        if response.getcode() == 200:
                            print(f"✅ QMapPermalinkサーバー発見: ポート {port}")
                            return port
                except Exception:
                    continue
        except Exception:
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
        req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            duration = time.time() - start_time
            content = response.read().decode('utf-8', errors='ignore')
            
            print(f"⏱️ レスポンス時間: {duration:.2f}秒")
            print(f"📊 ステータス: {response.getcode()}")
            print(f"📄 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"📏 Content-Length: {len(content)} bytes")
            
            if response.getcode() == 200:
                # コンテンツチェック
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
                print(f"❌ {name} エンドポイント: HTTPエラー {response.getcode()}")
                return False
                
    except socket.timeout:
        print(f"⏰ {name} エンドポイント: タイムアウト (30秒)")
        return False
    except urllib.error.HTTPError as e:
        print(f"❌ {name} エンドポイント: HTTPエラー {e.code} - {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"❌ {name} エンドポイント: 接続エラー - {e.reason}")
        return False
    except Exception as e:
        print(f"❌ {name} エンドポイント: 予期しないエラー - {e}")
        return False

def main():
    """メインテスト実行"""
    print("🚀 QMapPermalink v1.9.7 改善エンドポイントテスト")
    print("=" * 60)
    print("📋 テスト対象:")
    print("  ✅ /qgis-map (OpenLayersマップ)")
    print("  ✅ /qgis-image (QGIS実画像)")
    print("  ❌ /qgis-png (削除済み - パフォーマンス問題のため)")
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
    results["OpenLayers Map"] = test_endpoint(
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
    results["QGIS Real Image"] = test_endpoint(
        "QGIS Real Image",
        f"http://localhost:{server_port}/qgis-image?{base_params}&width=400&height=300",
        {
            "画像埋め込み": "data:image/png;base64,",
            "QGIS Real Image": "QGIS Real Image",
            "QMap Permalink": "QMap Permalink",
            "実画像表示": "QGISマップビュー（実画像）",
            "画像要素": "<img src="
        }
    )
    
    # 削除されたPNGエンドポイントのテスト（404エラーが期待される）
    print(f"\n🧪 削除済みPNGエンドポイント確認テスト")
    url = f"http://localhost:{server_port}/qgis-png?{base_params}"
    print(f"📡 URL: {url}")
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"⚠️ 削除されたはずのPNGエンドポイントが応答しました: {response.getcode()}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"✅ 期待通り404エラー: PNG エンドポイントは正常に削除されています")
        else:
            print(f"⚠️ 予期しないHTTPエラー: {e.code}")
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    passed_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    for endpoint_name, passed in results.items():
        status = "✅ 合格" if passed else "❌ 失敗"
        print(f"  {endpoint_name:20} {status}")
    
    print(f"\n🎯 総合結果: {passed_count}/{total_count} エンドポイントが正常動作")
    
    if passed_count == total_count:
        print("🎉 すべてのエンドポイントが正常に動作しています！")
        print("💡 PNG直接エンドポイントの削除により、HTTPサーバーの安定性が向上しました")
        print("⚡ レスポンス時間も大幅に改善されています")
    else:
        print("⚠️ 一部のエンドポイントに問題があります")
        print("🔧 QGISプラグインの設定やネットワーク接続を確認してください")
    
    print("\n📋 利用可能なエンドポイント:")
    print(f"  🗺️ OpenLayersマップ: http://localhost:{server_port}/qgis-map?lat=35.681236&lon=139.767125&z=16")
    print(f"  🖼️ QGIS実画像:      http://localhost:{server_port}/qgis-image?lat=35.681236&lon=139.767125&z=16")
    print(f"  ❌ PNG直接出力:     削除済み（パフォーマンス問題のため）")

if __name__ == "__main__":
    main()