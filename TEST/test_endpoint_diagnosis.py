#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTPサーバーエンドポイント診断スクリプト

利用可能なエンドポイントを全てテストして確認する
"""

import urllib.request
import urllib.parse
import urllib.error
import socket


def test_all_possible_endpoints():
    """考えられる全てのエンドポイントをテスト"""
    
    print("=" * 60)
    print("🔍 QMap Permalink HTTPサーバー エンドポイント診断")
    print("=" * 60)
    
    # ポートを確認
    active_port = find_active_server()
    if not active_port:
        print("❌ HTTPサーバーが見つかりません")
        return
    
    # テストするエンドポイントのリスト
    endpoints_to_test = [
        "/",
        "/qgis-map",
        "/qgis-image", 
        "/qgis-png",
        "/map",
        "/image",
        "/png",
        "/status",
        "/health",
        "/version"
    ]
    
    base_params = "?lat=35.681236&lon=139.767125&z=16&width=400&height=300"
    
    for endpoint in endpoints_to_test:
        test_url = f"http://localhost:{active_port}{endpoint}{base_params}"
        print(f"\\n📋 テスト: {endpoint}")
        print(f"   URL: {test_url}")
        
        try:
            request = urllib.request.Request(test_url)
            
            with urllib.request.urlopen(request, timeout=10) as response:
                status_code = response.getcode()
                content_type = response.headers.get('Content-Type', '')
                content_length = len(response.read())
                
                print(f"   ✅ ステータス: {status_code}")
                print(f"   📋 Content-Type: {content_type}")
                print(f"   📏 サイズ: {content_length} bytes")
                
                if status_code == 200:
                    print(f"   🎉 {endpoint} は利用可能です！")
                
        except urllib.error.HTTPError as e:
            print(f"   ❌ HTTPエラー: {e.code} {e.reason}")
            if e.code == 404:
                print(f"   💡 {endpoint} は実装されていません")
            
        except urllib.error.URLError as e:
            print(f"   ❌ URL接続エラー: {e.reason}")
            
        except socket.timeout:
            print(f"   ❌ タイムアウト: {endpoint}")
            
        except Exception as e:
            print(f"   ❌ 予期しないエラー: {e}")


def find_active_server():
    """アクティブなHTTPサーバーのポートを探す"""
    print("🔍 HTTPサーバーを検索中...")
    
    for port in range(8089, 8100):
        try:
            # 簡単な接続テスト
            test_url = f"http://localhost:{port}/qgis-map?lat=35.681236&lon=139.767125&z=16"
            request = urllib.request.Request(test_url)
            
            with urllib.request.urlopen(request, timeout=3) as response:
                if response.getcode() == 200:
                    print(f"✅ ポート {port} でHTTPサーバーが応答中")
                    return port
                    
        except:
            continue
    
    print("❌ ポート8089-8099でHTTPサーバーが見つかりませんでした")
    return None


def test_server_info():
    """サーバー情報を表示"""
    active_port = find_active_server()
    if not active_port:
        return
    
    print(f"\\n🌐 HTTPサーバー情報:")
    print(f"   ポート: {active_port}")
    print(f"   ベースURL: http://localhost:{active_port}")
    
    # サーバーのレスポンスヘッダーを確認
    try:
        test_url = f"http://localhost:{active_port}/qgis-map"
        request = urllib.request.Request(test_url)
        
        with urllib.request.urlopen(request, timeout=5) as response:
            print(f"\\n📋 レスポンスヘッダー:")
            for header_name, header_value in response.headers.items():
                print(f"   {header_name}: {header_value}")
                
    except Exception as e:
        print(f"   ❌ ヘッダー取得エラー: {e}")


if __name__ == "__main__":
    test_server_info()
    test_all_possible_endpoints()
    
    print("\\n" + "=" * 60)
    print("🏁 診断完了")
    print("💡 利用可能なエンドポイントが見つかった場合は、そのURLを使用してください")
    print("❌ エンドポイントが404エラーの場合は、QGISプラグインの再読み込みが必要です")
    print("=" * 60)