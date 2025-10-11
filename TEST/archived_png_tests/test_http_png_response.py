#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTPサーバーのPNGレスポンス機能テスト

/qgis-png エンドポイントに対するリクエストを送信し、
実際にPNG画像データが返ってくるかを確認するテストスクリプト。
"""

import requests
import time
import io
from PIL import Image


def test_qgis_png_endpoint():
    """QGISのPNGエンドポイントをテスト"""
    
    # 基本URL（通常は8089ポートで動作）
    base_url = "http://localhost:8089"
    
    # テストケース
    test_cases = [
        {
            "name": "東京駅周辺",
            "url": f"{base_url}/qgis-png?lat=35.681236&lon=139.767125&z=16&width=800&height=600"
        },
        {
            "name": "小さい画像サイズ",
            "url": f"{base_url}/qgis-png?lat=35.681236&lon=139.767125&z=14&width=400&height=300"
        },
        {
            "name": "x,yパラメータ形式",
            "url": f"{base_url}/qgis-png?x=139.767125&y=35.681236&z=15&width=600&height=400"
        }
    ]
    
    print("=" * 60)
    print("🧪 QMap Permalink HTTPサーバー PNGレスポンステスト")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 テストケース {i}: {test_case['name']}")
        print(f"🌐 URL: {test_case['url']}")
        
        try:
            # HTTPリクエストを送信
            print("📤 HTTPリクエスト送信中...")
            response = requests.get(test_case['url'], timeout=30)
            
            print(f"📥 HTTPステータスコード: {response.status_code}")
            print(f"📋 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"📏 Content-Length: {len(response.content)} bytes")
            
            # ステータスコードをチェック
            if response.status_code != 200:
                print(f"❌ HTTPエラー: {response.status_code}")
                print(f"📄 レスポンス内容: {response.text[:200]}...")
                continue
            
            # Content-Typeをチェック
            content_type = response.headers.get('Content-Type', '')
            if 'image/png' not in content_type:
                print(f"❌ Content-Typeが画像ではありません: {content_type}")
                print(f"📄 レスポンス内容: {response.text[:200]}...")
                continue
            
            # 画像データの妥当性をチェック
            try:
                # PILで画像を開いてみる
                image_data = io.BytesIO(response.content)
                with Image.open(image_data) as img:
                    print(f"✅ PNG画像取得成功!")
                    print(f"📐 画像サイズ: {img.size[0]}x{img.size[1]}")
                    print(f"🎨 画像モード: {img.mode}")
                    print(f"🔍 画像フォーマット: {img.format}")
                    
                    # テスト用画像として保存
                    output_filename = f"test_output_{i}.png"
                    with open(output_filename, 'wb') as f:
                        f.write(response.content)
                    print(f"💾 テスト画像を保存: {output_filename}")
                    
            except Exception as img_error:
                print(f"❌ 画像データの検証に失敗: {img_error}")
                print(f"🔍 レスポンス先頭32バイト: {response.content[:32]}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 接続エラー: HTTPサーバーが起動していない可能性があります")
            print("💡 QGISでQMap Permalinkプラグインを有効にし、HTTPサーバーを起動してください")
            
        except requests.exceptions.Timeout:
            print("❌ タイムアウトエラー: リクエストが30秒以内に完了しませんでした")
            
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 テスト完了")
    print("=" * 60)


def test_basic_connectivity():
    """基本的な接続テスト"""
    print("\n🔗 基本接続テスト")
    
    # ポート範囲をテスト
    for port in range(8089, 8100):
        try:
            url = f"http://localhost:{port}/qgis-map?lat=35.681236&lon=139.767125&z=16"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ ポート {port} でサーバーが応答中")
                return port
        except:
            continue
    
    print("❌ 8089-8099の範囲でHTTPサーバーが見つかりません")
    return None


if __name__ == "__main__":
    # 基本接続テスト
    active_port = test_basic_connectivity()
    
    if active_port:
        # メインテスト実行
        test_qgis_png_endpoint()
    else:
        print("\n💡 HTTPサーバーを起動してからもう一度実行してください:")
        print("   1. QGISでQMap Permalinkプラグインを有効化")
        print("   2. プラグインパネルでHTTPサーバーを起動")
        print("   3. このテストスクリプトを再実行")