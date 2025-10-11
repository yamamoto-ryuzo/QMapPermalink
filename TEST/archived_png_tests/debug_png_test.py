#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PNG エンドポイントデバッグテスト

ログ出力を詳細に確認しながらPNG生成プロセスを追跡
"""

import urllib.request
import urllib.parse
import urllib.error
import socket
import time


def test_png_with_debug():
    """PNG エンドポイントをデバッグログ付きでテスト"""
    
    print("=" * 60)
    print("🔍 QMap Permalink PNG エンドポイント デバッグテスト")
    print("=" * 60)
    
    # サーバー検索
    active_port = find_active_server()
    if not active_port:
        print("❌ HTTPサーバーが見つかりません")
        return False
    
    # シンプルなPNGリクエスト
    test_url = f"http://localhost:{active_port}/qgis-png?lat=35.681236&lon=139.767125&z=16&width=200&height=150"
    
    print(f"🌐 テストURL: {test_url}")
    print("📤 PNG生成リクエスト送信中...")
    print("💡 QGISのメッセージログパネル「QMapPermalink」タブでログを確認してください")
    print("⏳ 最大60秒待機します...")
    
    try:
        request = urllib.request.Request(test_url)
        start_time = time.time()
        
        with urllib.request.urlopen(request, timeout=60) as response:
            elapsed_time = time.time() - start_time
            
            status_code = response.getcode()
            content_type = response.headers.get('Content-Type', '')
            content = response.read()
            
            print(f"\\n📥 レスポンス受信完了 ({elapsed_time:.2f}秒)")
            print(f"✅ ステータス: {status_code}")
            print(f"📋 Content-Type: {content_type}")
            print(f"📏 データサイズ: {len(content):,} bytes")
            
            # レスポンスヘッダーを詳細表示
            print("\\n📋 レスポンスヘッダー:")
            for header_name, header_value in response.headers.items():
                print(f"   {header_name}: {header_value}")
            
            # PNG画像の検証
            if 'image/png' in content_type.lower() and len(content) > 0:
                # PNG署名チェック
                if len(content) >= 8:
                    png_signature = content[:8]
                    expected_signature = b'\\x89PNG\\r\\n\\x1a\\n'
                    
                    print(f"\\n🔍 PNG署名検証:")
                    print(f"   受信署名: {png_signature}")
                    print(f"   期待署名: {expected_signature}")
                    
                    if png_signature == expected_signature:
                        print("✅ PNG署名検証成功！")
                        
                        # PNG画像として保存
                        output_filename = "debug_test_output.png"
                        with open(output_filename, 'wb') as f:
                            f.write(content)
                        
                        print(f"💾 PNG画像を保存: {output_filename}")
                        print("🎉 PNG生成テスト成功！")
                        return True
                    else:
                        print("❌ PNG署名が不正です")
                else:
                    print("❌ データが短すぎます")
            else:
                print("❌ PNG画像ではありません")
                # エラーメッセージを表示
                try:
                    error_text = content.decode('utf-8', errors='replace')[:500]
                    print(f"📄 レスポンス内容: {error_text}")
                except:
                    print(f"📄 バイナリデータ: {content[:50]}...")
                    
            return False
            
    except socket.timeout:
        elapsed_time = time.time() - start_time
        print(f"\\n❌ タイムアウト: {elapsed_time:.2f}秒後にタイムアウト")
        print("💡 PNG生成に時間がかかりすぎています")
        print("🔍 QGISのメッセージログでどこまで処理が進んだか確認してください")
        return False
        
    except urllib.error.HTTPError as e:
        elapsed_time = time.time() - start_time
        print(f"\\n❌ HTTPエラー ({elapsed_time:.2f}秒後): {e.code} {e.reason}")
        try:
            error_content = e.read().decode('utf-8', errors='replace')[:300]
            print(f"📄 エラーレスポンス: {error_content}")
        except:
            pass
        return False
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\\n❌ 予期しないエラー ({elapsed_time:.2f}秒後): {e}")
        return False


def find_active_server():
    """アクティブなHTTPサーバーのポートを探す"""
    print("🔍 HTTPサーバーを検索中...")
    
    for port in range(8089, 8100):
        try:
            test_url = f"http://localhost:{port}/qgis-map?lat=35.681236&lon=139.767125&z=16"
            request = urllib.request.Request(test_url)
            
            with urllib.request.urlopen(request, timeout=3) as response:
                if response.getcode() == 200:
                    print(f"✅ ポート {port} でHTTPサーバーが応答中")
                    return port
                    
        except:
            continue
    
    print("❌ HTTPサーバーが見つかりませんでした")
    return None


def test_server_endpoints():
    """各エンドポイントの基本テスト"""
    active_port = find_active_server()
    if not active_port:
        return
    
    print(f"\\n📋 基本エンドポイントテスト (ポート: {active_port})")
    print("-" * 40)
    
    endpoints = [
        ("/qgis-map", "OpenLayersマップ", 10),
        ("/qgis-image", "QGIS画像HTML", 20),
        ("/qgis-png", "PNG画像直接", 60)
    ]
    
    base_params = "?lat=35.681236&lon=139.767125&z=16"
    
    for endpoint, description, timeout in endpoints:
        print(f"\\n📍 {endpoint} ({description})")
        
        try:
            test_url = f"http://localhost:{active_port}{endpoint}{base_params}"
            request = urllib.request.Request(test_url)
            
            start_time = time.time()
            with urllib.request.urlopen(request, timeout=timeout) as response:
                elapsed_time = time.time() - start_time
                
                status_code = response.getcode()
                content_type = response.headers.get('Content-Type', '')
                content_length = len(response.read())
                
                print(f"   ✅ ステータス: {status_code}")
                print(f"   📋 Content-Type: {content_type}")
                print(f"   📏 サイズ: {content_length:,} bytes")
                print(f"   ⏱️ 応答時間: {elapsed_time:.2f}秒")
                
        except socket.timeout:
            elapsed_time = time.time() - start_time
            print(f"   ❌ タイムアウト: {elapsed_time:.2f}秒")
            
        except Exception as e:
            print(f"   ❌ エラー: {e}")


if __name__ == "__main__":
    # 基本エンドポイントテスト
    test_server_endpoints()
    
    print("\\n" + "=" * 60)
    
    # PNG詳細テスト
    success = test_png_with_debug()
    
    print("\\n" + "=" * 60)
    print("🏁 デバッグテスト完了")
    
    if success:
        print("✅ PNG生成機能は正常に動作しています")
    else:
        print("❌ PNG生成に問題があります")
        print("💡 QGISのメッセージログパネル「QMapPermalink」タブで詳細ログを確認してください")
    
    print("=" * 60)