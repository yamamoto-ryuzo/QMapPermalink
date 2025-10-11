#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PNG エンドポイント専用テスト - 長いタイムアウト対応

/qgis-png エンドポイントのテストを長いタイムアウトで実行
"""

import urllib.request
import urllib.parse
import urllib.error
import socket
import time


def test_png_endpoint_extended():
    """PNG エンドポイントを拡張タイムアウトでテスト"""
    
    print("=" * 60)
    print("🖼️ QMap Permalink PNG エンドポイント 拡張テスト")
    print("=" * 60)
    
    # ポート確認
    active_port = find_active_server()
    if not active_port:
        print("❌ HTTPサーバーが見つかりません")
        return False
    
    # テストケース
    test_cases = [
        {
            "name": "小さい画像 (200x150)",
            "url": f"http://localhost:{active_port}/qgis-png?lat=35.681236&lon=139.767125&z=16&width=200&height=150",
            "timeout": 30
        },
        {
            "name": "標準画像 (400x300)",
            "url": f"http://localhost:{active_port}/qgis-png?lat=35.681236&lon=139.767125&z=16&width=400&height=300",
            "timeout": 45
        },
        {
            "name": "大きい画像 (800x600)",
            "url": f"http://localhost:{active_port}/qgis-png?lat=35.681236&lon=139.767125&z=16&width=800&height=600",
            "timeout": 60
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\\n📋 テストケース {i}: {test_case['name']}")
        print(f"🌐 URL: {test_case['url']}")
        print(f"⏱️ タイムアウト: {test_case['timeout']}秒")
        
        start_time = time.time()
        
        try:
            request = urllib.request.Request(test_case['url'])
            
            print("📤 HTTPリクエスト送信中...")
            with urllib.request.urlopen(request, timeout=test_case['timeout']) as response:
                end_time = time.time()
                elapsed_time = end_time - start_time
                
                status_code = response.getcode()
                content_type = response.headers.get('Content-Type', '')
                content = response.read()
                content_length = len(content)
                
                print(f"📥 レスポンス受信完了 ({elapsed_time:.2f}秒)")
                print(f"✅ ステータス: {status_code}")
                print(f"📋 Content-Type: {content_type}")
                print(f"📏 データサイズ: {content_length:,} bytes")
                
                # Content-Type チェック
                if 'image/png' in content_type.lower():
                    print("✅ PNG画像として認識されました")
                    
                    # PNG署名チェック (89 50 4E 47 0D 0A 1A 0A)
                    if len(content) >= 8:
                        png_signature = content[:8]
                        expected_signature = b'\\x89PNG\\r\\n\\x1a\\n'
                        
                        if png_signature == expected_signature:
                            print("✅ PNG画像の署名が正しく確認されました")
                            
                            # テスト用に画像保存
                            output_filename = f"test_png_output_{i}_{test_case['name'].replace(' ', '_').replace('(', '').replace(')', '')}.png"
                            with open(output_filename, 'wb') as f:
                                f.write(content)
                            print(f"💾 PNG画像を保存: {output_filename}")
                            
                            success_count += 1
                            print("🎉 PNGテスト成功！")
                            
                        else:
                            print(f"❌ PNG署名が不正: {png_signature}")
                            print(f"🔍 期待された署名: {expected_signature}")
                    else:
                        print(f"❌ データが短すぎます: {content_length} bytes")
                else:
                    print(f"❌ PNG画像ではありません: {content_type}")
                    # エラーメッセージを表示
                    try:
                        error_text = content.decode('utf-8', errors='replace')[:500]
                        print(f"📄 エラー内容: {error_text}")
                    except:
                        print(f"📄 バイナリデータ: {content[:50]}...")
                        
        except socket.timeout:
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"❌ タイムアウト: {elapsed_time:.2f}秒後にタイムアウト")
            print("💡 画像生成に時間がかかりすぎています")
            
        except urllib.error.HTTPError as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"❌ HTTPエラー ({elapsed_time:.2f}秒後): {e.code} {e.reason}")
            try:
                error_content = e.read().decode('utf-8', errors='replace')[:300]
                print(f"📄 エラーレスポンス: {error_content}")
            except:
                pass
                
        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"❌ 予期しないエラー ({elapsed_time:.2f}秒後): {e}")
    
    print(f"\\n" + "=" * 60)
    print(f"🏁 テスト完了: {success_count}/{len(test_cases)} 成功")
    
    if success_count > 0:
        print("✅ PNG エンドポイントは正常に動作しています！")
    else:
        print("❌ PNG エンドポイントに問題があります")
        print("💡 QGISのログメッセージパネルでエラー詳細を確認してください")
    
    return success_count > 0


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


def test_qgis_image_endpoint():
    """QGIS画像エンドポイントもテスト"""
    active_port = find_active_server()
    if not active_port:
        return
    
    print(f"\\n🖼️ /qgis-image エンドポイントテスト")
    test_url = f"http://localhost:{active_port}/qgis-image?lat=35.681236&lon=139.767125&z=16&width=400&height=300"
    
    try:
        request = urllib.request.Request(test_url)
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read()
            content_type = response.headers.get('Content-Type', '')
            
            print(f"✅ ステータス: {response.getcode()}")
            print(f"📋 Content-Type: {content_type}")
            print(f"📏 サイズ: {len(content):,} bytes")
            
            if 'text/html' in content_type:
                # HTMLファイルとして保存
                with open('test_qgis_image_output.html', 'wb') as f:
                    f.write(content)
                print("💾 HTML画像ページを保存: test_qgis_image_output.html")
                print("🌐 ブラウザで開いて確認してください")
                
    except Exception as e:
        print(f"❌ /qgis-image テストエラー: {e}")


if __name__ == "__main__":
    # PNG エンドポイントテスト
    png_success = test_png_endpoint_extended()
    
    # QGIS画像エンドポイントテスト
    test_qgis_image_endpoint()
    
    print("\\n" + "=" * 60)
    print("🏁 全テスト完了")
    if png_success:
        print("🎉 PNG画像生成機能は正常に動作しています！")
    else:
        print("💡 問題がある場合は、QGISのメッセージログを確認してください")
    print("=" * 60)