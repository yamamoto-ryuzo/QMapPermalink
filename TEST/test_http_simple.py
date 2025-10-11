#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
シンプルなHTTPクライアントテスト - 外部依存なし

/qgis-png エンドポイントの動作確認用テストスクリプト
標準ライブラリのみを使用
"""

import urllib.request
import urllib.parse
import urllib.error
import socket
import time


def test_http_png_simple():
    """シンプルなHTTPテスト"""
    
    print("=" * 60)
    print("🧪 QMap Permalink HTTPサーバー シンプルテスト")
    print("=" * 60)
    
    # ポートを確認
    active_port = find_active_server()
    if not active_port:
        print("❌ HTTPサーバーが見つかりません")
        return
    
    # テストURL
    test_url = f"http://localhost:{active_port}/qgis-png?lat=35.681236&lon=139.767125&z=16&width=400&height=300"
    
    print(f"🌐 テストURL: {test_url}")
    print(f"📤 HTTPリクエスト送信中...")
    
    try:
        # HTTPリクエストを送信
        request = urllib.request.Request(test_url)
        
        with urllib.request.urlopen(request, timeout=30) as response:
            # レスポンス情報を表示
            status_code = response.getcode()
            headers = dict(response.headers)
            content = response.read()
            
            print(f"📥 HTTPステータスコード: {status_code}")
            print(f"📋 レスポンスヘッダー:")
            for key, value in headers.items():
                print(f"   {key}: {value}")
            
            print(f"📏 Content-Length: {len(content)} bytes")
            
            # Content-Typeをチェック
            content_type = headers.get('Content-Type', '').lower()
            print(f"🔍 Content-Type: {content_type}")
            
            if 'image/png' in content_type:
                print("✅ PNG画像として認識されました")
                
                # PNG署名をチェック (89 50 4E 47 0D 0A 1A 0A)
                if len(content) >= 8:
                    png_signature = content[:8]
                    expected_signature = b'\\x89PNG\\r\\n\\x1a\\n'
                    
                    if png_signature == expected_signature:
                        print("✅ PNG画像の署名が正しく確認されました")
                        
                        # テスト用画像として保存
                        output_filename = "test_simple_output.png"
                        with open(output_filename, 'wb') as f:
                            f.write(content)
                        print(f"💾 画像を保存: {output_filename}")
                        
                    else:
                        print(f"❌ PNG署名が不正です")
                        print(f"🔍 受信した署名: {png_signature}")
                        print(f"🔍 期待された署名: {expected_signature}")
                        
                else:
                    print(f"❌ コンテンツが短すぎます（{len(content)} bytes）")
                    
            else:
                print(f"❌ PNG画像ではありません: {content_type}")
                print(f"📄 レスポンス内容の一部:")
                try:
                    # テキストとして表示を試行
                    text_content = content.decode('utf-8', errors='replace')[:500]
                    print(text_content)
                except:
                    # バイナリ表示
                    print(f"   バイナリデータ先頭32バイト: {content[:32]}")
                    
    except urllib.error.HTTPError as e:
        print(f"❌ HTTPエラー: {e.code} {e.reason}")
        try:
            error_content = e.read().decode('utf-8', errors='replace')
            print(f"📄 エラーレスポンス: {error_content[:300]}")
        except:
            pass
            
    except urllib.error.URLError as e:
        print(f"❌ URL接続エラー: {e.reason}")
        print("💡 HTTPサーバーが起動していない可能性があります")
        
    except socket.timeout:
        print("❌ タイムアウトエラー: 30秒以内に応答がありませんでした")
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")


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


def test_all_endpoints():
    """全エンドポイントをテスト"""
    
    active_port = find_active_server()
    if not active_port:
        return
    
    endpoints = [
        ("/qgis-map", "OpenLayersマップ"),
        ("/qgis-image", "QGIS画像埋め込みHTML"),
        ("/qgis-png", "PNG画像直接レスポンス")
    ]
    
    params = "?lat=35.681236&lon=139.767125&z=16&width=400&height=300"
    
    print(f"\\n🧪 全エンドポイントテスト (ポート: {active_port})")
    print("=" * 60)
    
    for endpoint, description in endpoints:
        print(f"\\n📋 テスト: {endpoint} ({description})")
        
        try:
            test_url = f"http://localhost:{active_port}{endpoint}{params}"
            request = urllib.request.Request(test_url)
            
            with urllib.request.urlopen(request, timeout=15) as response:
                status_code = response.getcode()
                content_type = response.headers.get('Content-Type', '')
                content_length = len(response.read())
                
                print(f"   ✅ ステータス: {status_code}")
                print(f"   📋 Content-Type: {content_type}")
                print(f"   📏 サイズ: {content_length} bytes")
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")


if __name__ == "__main__":
    # メインテスト
    test_http_png_simple()
    
    # 全エンドポイントテスト
    test_all_endpoints()
    
    print("\\n" + "=" * 60)
    print("🏁 テスト完了")
    print("💡 問題がある場合は、QGISのログメッセージパネルを確認してください")
    print("=" * 60)