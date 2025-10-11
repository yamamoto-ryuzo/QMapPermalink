#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QGIS WMS配信機能の簡易テストスクリプト（標準ライブラリのみ使用）

このスクリプトは、標準ライブラリのurllib.requestを使用して
QGISのWMS配信機能をテストします。
"""

import urllib.request
import urllib.parse
import json
import sys
import time
from urllib.error import URLError, HTTPError

class QGISWMSSimpleTest:
    def __init__(self, base_url="http://localhost:8089"):
        self.base_url = base_url
        
    def test_server_connection(self):
        """サーバー接続テスト"""
        print("🔍 サーバー接続テスト...")
        try:
            url = f"{self.base_url}/wms?SERVICE=WMS&REQUEST=GetCapabilities"
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
    
    def test_get_capabilities(self):
        """GetCapabilitiesテスト"""
        print("\n📋 WMS GetCapabilities テスト...")
        try:
            url = f"{self.base_url}/wms?SERVICE=WMS&REQUEST=GetCapabilities"
            
            with urllib.request.urlopen(url, timeout=30) as response:
                if response.status == 200:
                    content = response.read().decode('utf-8')
                    print("✅ GetCapabilities 成功")
                    print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
                    print(f"   Content-Length: {len(content)} chars")
                    
                    # XMLの基本構造をチェック
                    if '<WMS_Capabilities' in content and '</WMS_Capabilities>' in content:
                        print("✅ 有効なCapabilities XMLを受信")
                        # レイヤー数をカウント
                        layer_count = content.count('<Layer queryable="1">')
                        print(f"   レイヤー数: {layer_count}")
                    else:
                        print("⚠️ Capabilities XMLの構造が不正")
                    
                    return True
                else:
                    print(f"❌ GetCapabilities 失敗: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ GetCapabilities エラー: {e}")
            return False
    
    def test_get_map(self, bbox="139.5,35.5,139.9,35.9", width=400, height=400):
        """GetMapテスト"""
        print(f"\n🗺️ WMS GetMap テスト (BBOX: {bbox}, Size: {width}x{height})...")
        try:
            params = {
                'SERVICE': 'WMS',
                'REQUEST': 'GetMap',
                'BBOX': bbox,
                'WIDTH': str(width),
                'HEIGHT': str(height),
                'CRS': 'EPSG:4326',
                'FORMAT': 'image/png'
            }
            
            query = urllib.parse.urlencode(params)
            url = f"{self.base_url}/wms?{query}"
            
            with urllib.request.urlopen(url, timeout=60) as response:
                if response.status == 200:
                    content = response.read()
                    print("✅ GetMap 成功")
                    print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
                    print(f"   Content-Length: {len(content)} bytes")
                    
                    # PNG形式の確認
                    if content.startswith(b'\x89PNG\r\n\x1a\n'):
                        print("✅ 有効なPNG画像を受信")
                    else:
                        print("⚠️ PNG画像ではない可能性があります")
                        print(f"   先頭バイト: {content[:16]}")
                    
                    # ファイルに保存
                    filename = f"test_getmap_{int(time.time())}.png"
                    with open(filename, 'wb') as f:
                        f.write(content)
                    print(f"📁 画像ファイルを保存: {filename}")
                    
                    return True
                else:
                    print(f"❌ GetMap 失敗: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ GetMap エラー: {e}")
            return False
    
    def test_get_feature_info(self, i=200, j=200):
        """GetFeatureInfoテスト"""
        print(f"\n🔍 WMS GetFeatureInfo テスト (Pixel: {i}, {j})...")
        try:
            params = {
                'SERVICE': 'WMS',
                'REQUEST': 'GetFeatureInfo',
                'I': str(i),
                'J': str(j),
                'INFO_FORMAT': 'application/json'
            }
            
            query = urllib.parse.urlencode(params)
            url = f"{self.base_url}/wms?{query}"
            
            with urllib.request.urlopen(url, timeout=30) as response:
                if response.status == 200:
                    content = response.read().decode('utf-8')
                    print("✅ GetFeatureInfo 成功")
                    print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
                    
                    try:
                        data = json.loads(content)
                        print(f"   レイヤー数: {len(data.get('layers', []))}")
                        
                        for i, layer in enumerate(data.get('layers', [])[:3]):  # 最初の3レイヤーのみ表示
                            print(f"   Layer {i+1}: {layer.get('name', 'N/A')} (Type: {layer.get('type', 'N/A')})")
                        
                    except json.JSONDecodeError:
                        print("⚠️ JSONレスポンスの解析に失敗")
                        print(f"   Response: {content[:200]}...")
                    
                    return True
                else:
                    print(f"❌ GetFeatureInfo 失敗: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ GetFeatureInfo エラー: {e}")
            return False
    
    def test_tile_endpoint(self, z=10, x=904, y=403):
        """タイルエンドポイントテスト"""
        print(f"\n🗺️ タイル配信テスト (Z: {z}, X: {x}, Y: {y})...")
        try:
            url = f"{self.base_url}/tiles/{z}/{x}/{y}.png"
            
            with urllib.request.urlopen(url, timeout=60) as response:
                if response.status == 200:
                    content = response.read()
                    print("✅ タイル配信 成功")
                    print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
                    print(f"   Content-Length: {len(content)} bytes")
                    
                    # PNG形式の確認
                    if content.startswith(b'\x89PNG\r\n\x1a\n'):
                        print("✅ 有効なPNG画像を受信")
                    else:
                        print("⚠️ PNG画像ではない可能性があります")
                        print(f"   先頭バイト: {content[:16]}")
                    
                    # ファイルに保存
                    filename = f"test_tile_{z}_{x}_{y}_{int(time.time())}.png"
                    with open(filename, 'wb') as f:
                        f.write(content)
                    print(f"📁 タイル画像を保存: {filename}")
                    
                    return True
                else:
                    print(f"❌ タイル配信 失敗: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ タイル配信 エラー: {e}")
            return False
    
    def test_existing_endpoints(self):
        """既存エンドポイントのテスト"""
        print("\n🔄 既存エンドポイントテスト...")
        
        # QGIS Map エンドポイント
        try:
            params = {'lat': '35.681', 'lon': '139.767', 'scale': '25000'}
            query = urllib.parse.urlencode(params)
            url = f"{self.base_url}/qgis-map?{query}"
            
            with urllib.request.urlopen(url, timeout=30) as response:
                if response.status == 200:
                    print("✅ /qgis-map エンドポイント 正常")
                else:
                    print(f"⚠️ /qgis-map エンドポイント 異常: HTTP {response.status}")
        except Exception as e:
            print(f"❌ /qgis-map エンドポイント エラー: {e}")
        
        # QGIS PNG エンドポイント
        try:
            params = {'lat': '35.681', 'lon': '139.767', 'scale': '25000', 'width': '400', 'height': '300'}
            query = urllib.parse.urlencode(params)
            url = f"{self.base_url}/qgis-png?{query}"
            
            with urllib.request.urlopen(url, timeout=60) as response:
                if response.status == 200:
                    content = response.read()
                    if content.startswith(b'\x89PNG\r\n\x1a\n'):
                        print("✅ /qgis-png エンドポイント 正常")
                    else:
                        print(f"⚠️ /qgis-png エンドポイント: PNG形式ではない")
                else:
                    print(f"⚠️ /qgis-png エンドポイント 異常: HTTP {response.status}")
        except Exception as e:
            print(f"❌ /qgis-png エンドポイント エラー: {e}")
    
    def run_all_tests(self):
        """全テストを実行"""
        print("=" * 60)
        print("🧪 QGIS WMS配信機能 総合テスト（簡易版）")
        print("=" * 60)
        
        results = []
        
        # 各テストを実行
        results.append(("サーバー接続", self.test_server_connection()))
        
        if results[0][1]:  # サーバー接続が成功した場合のみ続行
            results.append(("GetCapabilities", self.test_get_capabilities()))
            results.append(("GetMap", self.test_get_map()))
            results.append(("GetFeatureInfo", self.test_get_feature_info()))
            results.append(("タイル配信", self.test_tile_endpoint()))
            self.test_existing_endpoints()
        
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
            print("\n🎉 全テスト成功！WMS配信機能は正常に動作しています。")
        elif success_count > 0:
            print(f"\n⚠️ 一部のテストが失敗しました。詳細を確認してください。")
        else:
            print(f"\n❌ 全テスト失敗。サーバーが起動していない可能性があります。")
        
        return success_count, len(results)

def main():
    """メイン関数"""
    print("QGIS WMS配信機能テストスクリプト（標準ライブラリ版）")
    print("このスクリプトは、QGISのHTTPサーバーが localhost:8089 で動作していることを前提とします。")
    print("QGISでQMapPermalinkプラグインを起動し、HTTPサーバーを開始してからテストを実行してください。\n")
    
    # コマンドライン引数の処理
    base_url = "http://localhost:8089"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"テスト対象サーバー: {base_url}\n")
    
    # テスト実行
    tester = QGISWMSSimpleTest(base_url)
    success_count, total_count = tester.run_all_tests()
    
    # 終了コード
    sys.exit(0 if success_count == total_count else 1)

if __name__ == "__main__":
    main()