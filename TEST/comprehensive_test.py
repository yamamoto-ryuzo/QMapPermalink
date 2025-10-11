#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMap Permalink HTTPサーバー 総合テストスイート

全エンドポイントの動作確認とPNG画像生成機能のテスト
テストファイルはTESTフォルダに配置
"""

import urllib.request
import urllib.parse
import urllib.error
import socket
import time
import os


class QMapPermalinkTester:
    """QMap Permalink HTTPサーバーテスター"""
    
    def __init__(self):
        self.base_port_range = (8089, 8099)
        self.active_port = None
        self.test_results = []
    
    def find_active_server(self):
        """アクティブなHTTPサーバーのポートを探す"""
        print("🔍 QMap Permalink HTTPサーバーを検索中...")
        
        for port in range(*self.base_port_range):
            try:
                test_url = f"http://localhost:{port}/qgis-map?lat=35.681236&lon=139.767125&z=16"
                request = urllib.request.Request(test_url)
                
                with urllib.request.urlopen(request, timeout=3) as response:
                    if response.getcode() == 200:
                        print(f"✅ ポート {port} でQMap Permalink HTTPサーバーが応答中")
                        self.active_port = port
                        return port
                        
            except:
                continue
        
        print(f"❌ ポート{self.base_port_range[0]}-{self.base_port_range[1]}でHTTPサーバーが見つかりませんでした")
        return None
    
    def test_endpoint_availability(self):
        """全エンドポイントの利用可否をテスト"""
        if not self.active_port:
            return False
        
        print("\\n" + "=" * 60)
        print("🔍 QMap Permalink エンドポイント利用可否テスト")
        print("=" * 60)
        
        endpoints = [
            ("/qgis-map", "OpenLayersインタラクティブマップ"),
            ("/qgis-image", "QGIS実画像埋め込みHTML"),
            ("/qgis-png", "PNG画像直接レスポンス")
        ]
        
        base_params = "?lat=35.681236&lon=139.767125&z=16&width=400&height=300"
        
        for endpoint, description in endpoints:
            test_url = f"http://localhost:{self.active_port}{endpoint}{base_params}"
            print(f"\\n📋 テスト: {endpoint} ({description})")
            
            try:
                request = urllib.request.Request(test_url)
                timeout = 30 if endpoint == "/qgis-png" else 10
                
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
                    
                    self.test_results.append({
                        'endpoint': endpoint,
                        'status': 'success',
                        'status_code': status_code,
                        'content_type': content_type,
                        'size': content_length,
                        'response_time': elapsed_time
                    })
                    
                    if status_code == 200:
                        print(f"   🎉 {endpoint} は正常に動作しています！")
                        
            except socket.timeout:
                elapsed_time = time.time() - start_time
                print(f"   ❌ タイムアウト: {elapsed_time:.2f}秒")
                self.test_results.append({
                    'endpoint': endpoint,
                    'status': 'timeout',
                    'response_time': elapsed_time
                })
                
            except urllib.error.HTTPError as e:
                print(f"   ❌ HTTPエラー: {e.code} {e.reason}")
                self.test_results.append({
                    'endpoint': endpoint,
                    'status': 'http_error',
                    'error_code': e.code,
                    'error_reason': e.reason
                })
                
            except Exception as e:
                print(f"   ❌ エラー: {e}")
                self.test_results.append({
                    'endpoint': endpoint,
                    'status': 'error',
                    'error': str(e)
                })
        
        return True
    
    def test_png_generation(self):
        """PNG画像生成の詳細テスト"""
        if not self.active_port:
            return False
        
        print("\\n" + "=" * 60)
        print("🖼️ QMap Permalink PNG画像生成テスト")
        print("=" * 60)
        
        test_cases = [
            {
                "name": "小サイズ画像",
                "params": "?lat=35.681236&lon=139.767125&z=16&width=200&height=150",
                "timeout": 30
            },
            {
                "name": "標準サイズ画像",
                "params": "?lat=35.681236&lon=139.767125&z=16&width=400&height=300",
                "timeout": 45
            },
            {
                "name": "高ズームレベル",
                "params": "?lat=35.681236&lon=139.767125&z=18&width=400&height=300",
                "timeout": 60
            }
        ]
        
        png_success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n📋 PNGテストケース {i}: {test_case['name']}")
            
            test_url = f"http://localhost:{self.active_port}/qgis-png{test_case['params']}"
            print(f"🌐 URL: {test_url}")
            
            try:
                request = urllib.request.Request(test_url)
                start_time = time.time()
                
                print("📤 PNG生成リクエスト送信中...")
                with urllib.request.urlopen(request, timeout=test_case['timeout']) as response:
                    elapsed_time = time.time() - start_time
                    
                    status_code = response.getcode()
                    content_type = response.headers.get('Content-Type', '')
                    content = response.read()
                    
                    print(f"📥 レスポンス受信 ({elapsed_time:.2f}秒)")
                    print(f"✅ ステータス: {status_code}")
                    print(f"📋 Content-Type: {content_type}")
                    print(f"📏 データサイズ: {len(content):,} bytes")
                    
                    # PNG画像の検証
                    if self._validate_png_image(content, content_type):
                        # PNG画像として保存
                        output_filename = f"qmap_test_output_{i}_{test_case['name'].replace(' ', '_')}.png"
                        output_path = os.path.join(os.path.dirname(__file__), output_filename)
                        
                        with open(output_path, 'wb') as f:
                            f.write(content)
                        
                        print(f"💾 PNG画像を保存: {output_filename}")
                        print("🎉 PNG生成テスト成功！")
                        png_success_count += 1
                    else:
                        print("❌ PNG画像の検証に失敗")
                        
            except socket.timeout:
                elapsed_time = time.time() - start_time
                print(f"❌ タイムアウト: {elapsed_time:.2f}秒")
                print("💡 PNG生成に時間がかかりすぎています")
                
            except Exception as e:
                print(f"❌ PNGテストエラー: {e}")
        
        print(f"\\n📊 PNG生成テスト結果: {png_success_count}/{len(test_cases)} 成功")
        return png_success_count > 0
    
    def _validate_png_image(self, content, content_type):
        """PNG画像データの妥当性を検証"""
        # Content-Type チェック
        if 'image/png' not in content_type.lower():
            print(f"❌ Content-Typeが正しくありません: {content_type}")
            return False
        
        # データサイズチェック
        if len(content) == 0:
            print("❌ 画像データが空です")
            return False
        
        # PNG署名チェック (89 50 4E 47 0D 0A 1A 0A)
        if len(content) >= 8:
            png_signature = content[:8]
            expected_signature = b'\\x89PNG\\r\\n\\x1a\\n'
            
            if png_signature == expected_signature:
                print("✅ PNG署名検証成功")
                return True
            else:
                print(f"❌ PNG署名が不正: {png_signature} != {expected_signature}")
                return False
        else:
            print(f"❌ データが短すぎます: {len(content)} bytes")
            return False
    
    def generate_test_report(self):
        """テスト結果レポートを生成"""
        print("\\n" + "=" * 60)
        print("📊 QMap Permalink HTTPサーバー テスト結果レポート")
        print("=" * 60)
        
        if not self.test_results:
            print("❌ テスト結果がありません")
            return
        
        success_count = sum(1 for result in self.test_results if result.get('status') == 'success')
        total_tests = len(self.test_results)
        
        print(f"📈 総合結果: {success_count}/{total_tests} エンドポイント成功")
        print(f"🌐 テスト対象サーバー: http://localhost:{self.active_port}")
        
        print("\\n📋 詳細結果:")
        for result in self.test_results:
            endpoint = result['endpoint']
            status = result['status']
            
            if status == 'success':
                print(f"   ✅ {endpoint}: 成功 ({result.get('response_time', 0):.2f}秒)")
            elif status == 'timeout':
                print(f"   ⏰ {endpoint}: タイムアウト")
            elif status == 'http_error':
                print(f"   ❌ {endpoint}: HTTPエラー {result.get('error_code')}")
            else:
                print(f"   ❌ {endpoint}: エラー")
        
        if success_count == total_tests:
            print("\\n🎉 全エンドポイントが正常に動作しています！")
        elif success_count > 0:
            print("\\n⚠️ 一部のエンドポイントに問題があります")
        else:
            print("\\n❌ すべてのエンドポイントで問題が発生しています")
    
    def run_comprehensive_test(self):
        """包括的テストの実行"""
        print("=" * 60)
        print("🧪 QMap Permalink HTTPサーバー 包括的テスト開始")
        print("=" * 60)
        
        # サーバー検索
        if not self.find_active_server():
            print("\\n❌ HTTPサーバーが見つからないためテストを中断します")
            print("💡 QGISでQMap Permalinkプラグインを有効化してHTTPサーバーを起動してください")
            return False
        
        # エンドポイント利用可否テスト
        self.test_endpoint_availability()
        
        # PNG生成テスト
        png_success = self.test_png_generation()
        
        # テストレポート生成
        self.generate_test_report()
        
        print("\\n" + "=" * 60)
        print("🏁 包括的テスト完了")
        print("=" * 60)
        
        return png_success


if __name__ == "__main__":
    tester = QMapPermalinkTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\\n✅ QMap Permalink HTTPサーバーは正常に動作しています")
    else:
        print("\\n❌ QMap Permalink HTTPサーバーに問題があります")
        print("💡 QGISのメッセージログパネル「QMapPermalink」タブで詳細を確認してください")