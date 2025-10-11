#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QGIS パーマリンク機能の基本テストスクリプト

既存機能（WMS機能が利用できない場合）のテスト用
"""

import urllib.request
import urllib.parse
import sys
import time
from urllib.error import URLError, HTTPError

class QGISBasicTest:
    def __init__(self, base_url="http://localhost:8089"):
        self.base_url = base_url
        
    def test_server_connection(self):
        """サーバー接続テスト"""
        print("🔍 サーバー接続テスト...")
        try:
            url = f"{self.base_url}/qgis-map?lat=35.681&lon=139.767&scale=25000"
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status == 200:
                    print("✅ サーバー接続成功")
                    return True
                else:
                    print(f"❌ サーバー接続失敗: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ サーバー接続エラー: {e}")
            return False
    
    def test_qgis_map(self):
        """QGIS Map エンドポイントテスト"""
        print("\n🗺️ QGIS Map エンドポイントテスト...")
        try:
            url = f"{self.base_url}/qgis-map?lat=35.681&lon=139.767&scale=25000"
            
            with urllib.request.urlopen(url, timeout=30) as response:
                if response.status == 200:
                    content = response.read().decode('utf-8')
                    print("✅ QGIS Map 成功")
                    print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
                    print(f"   Content-Length: {len(content)} chars")
                    
                    # HTMLの基本構造をチェック
                    if '<html' in content.lower() and '</html>' in content.lower():
                        print("✅ 有効なHTMLを受信")
                        if 'OpenLayers' in content:
                            print("✅ OpenLayersマップが埋め込まれています")
                    else:
                        print("⚠️ HTMLの構造が不正")
                    
                    return True
                else:
                    print(f"❌ QGIS Map 失敗: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ QGIS Map エラー: {e}")
            return False
    
    def test_qgis_png(self):
        """QGIS PNG エンドポイントテスト"""
        print("\n📸 QGIS PNG エンドポイントテスト...")
        try:
            url = f"{self.base_url}/qgis-png?lat=35.681&lon=139.767&scale=25000&width=400&height=300"
            
            with urllib.request.urlopen(url, timeout=60) as response:
                if response.status == 200:
                    content = response.read()
                    print("✅ QGIS PNG 成功")
                    print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
                    print(f"   Content-Length: {len(content)} bytes")
                    
                    # PNG形式の確認
                    if content.startswith(b'\x89PNG\r\n\x1a\n'):
                        print("✅ 有効なPNG画像を受信")
                    else:
                        print("⚠️ PNG画像ではない可能性があります")
                        print(f"   先頭バイト: {content[:16]}")
                    
                    # ファイルに保存
                    filename = f"test_qgis_png_{int(time.time())}.png"
                    with open(filename, 'wb') as f:
                        f.write(content)
                    print(f"📁 画像ファイルを保存: {filename}")
                    
                    return True
                else:
                    print(f"❌ QGIS PNG 失敗: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ QGIS PNG エラー: {e}")
            return False
    
    def test_qgis_image(self):
        """QGIS Image エンドポイントテスト"""
        print("\n🖼️ QGIS Image エンドポイントテスト...")
        try:
            url = f"{self.base_url}/qgis-image?lat=35.681&lon=139.767&scale=25000"
            
            with urllib.request.urlopen(url, timeout=30) as response:
                if response.status == 200:
                    content = response.read().decode('utf-8')
                    print("✅ QGIS Image 成功")
                    print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
                    print(f"   Content-Length: {len(content)} chars")
                    
                    # HTMLの基本構造をチェック
                    if '<html' in content.lower() and '</html>' in content.lower():
                        print("✅ 有効なHTMLを受信")
                        if '<img' in content.lower():
                            print("✅ 画像が埋め込まれています")
                    else:
                        print("⚠️ HTMLの構造が不正")
                    
                    return True
                else:
                    print(f"❌ QGIS Image 失敗: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ QGIS Image エラー: {e}")
            return False
    
    def check_wms_availability(self):
        """WMS機能が利用可能かチェック"""
        print("\n🌐 WMS機能利用可能性チェック...")
        try:
            url = f"{self.base_url}/wms?SERVICE=WMS&REQUEST=GetCapabilities"
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status == 200:
                    print("✅ WMS機能が利用可能です")
                    return True
                else:
                    print(f"❌ WMS機能が利用できません: HTTP {response.status}")
                    return False
        except HTTPError as e:
            if e.code == 404:
                print("⚠️ WMS機能はまだ利用できません（404 Not Found）")
                print("   QGISでプラグインを更新・再起動してください")
            else:
                print(f"❌ WMS機能チェックエラー: HTTP {e.code}")
            return False
        except Exception as e:
            print(f"❌ WMS機能チェックエラー: {e}")
            return False
    
    def run_all_tests(self):
        """全テストを実行"""
        print("=" * 60)
        print("🧪 QGIS パーマリンク機能 基本テスト")
        print("=" * 60)
        
        results = []
        
        # 各テストを実行
        results.append(("サーバー接続", self.test_server_connection()))
        
        if results[0][1]:  # サーバー接続が成功した場合のみ続行
            results.append(("QGIS Map", self.test_qgis_map()))
            results.append(("QGIS PNG", self.test_qgis_png()))
            results.append(("QGIS Image", self.test_qgis_image()))
            
            # WMS機能のチェック
            wms_available = self.check_wms_availability()
            if not wms_available:
                print("\n💡 WMS機能を有効化するには：")
                print("   1. QGISを完全に終了")
                print("   2. QGISを再起動")
                print("   3. QMapPermalinkプラグインを有効化")
                print("   4. HTTPサーバーを起動")
        
        # 結果サマリー
        print("\n" + "=" * 60)
        print("📊 テスト結果サマリー")
        print("=" * 60)
        
        success_count = 0
        for test_name, success in results:
            status = "✅ 成功" if success else "❌ 失敗"
            print(f"{test_name:20} : {status}")
            if success:
                success_count += 1
        
        print(f"\n成功率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
        
        if success_count == len(results):
            print("\n🎉 基本機能は全て正常に動作しています！")
        elif success_count > 0:
            print(f"\n⚠️ 一部のテストが失敗しました。")
        else:
            print(f"\n❌ 全テスト失敗。サーバーが起動していない可能性があり���す。")
        
        return success_count, len(results)

def main():
    """メイン関数"""
    print("QGIS パーマリンク機能 基本テストスクリプト")
    print("このスクリプトは、QGISのHTTPサーバーが localhost:8089 で動作していることを前提とします。")
    print("QGISでQMapPermalinkプラグインを起動し、HTTPサーバーを開始してからテストを実行してください。\n")
    
    # コマンドライン引数の処理
    base_url = "http://localhost:8089"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"テスト対象サーバー: {base_url}\n")
    
    # テスト実行
    tester = QGISBasicTest(base_url)
    success_count, total_count = tester.run_all_tests()
    
    # 終了コード
    sys.exit(0 if success_count == total_count else 1)

if __name__ == "__main__":
    main()