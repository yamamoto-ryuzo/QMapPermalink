#!/usr/bin/env python3
"""
統合WMS/パーマリンクエンドポイントのテスト
"""

import sys
import os
import time
import urllib.request
import urllib.error
from urllib.parse import urlencode

def test_wms_permalink_integration():
    """WMSエンドポイントでのパーマリンクパラメータ処理をテスト"""
    base_url = "http://localhost:8089"
    
    print("🧪 WMS/パーマリンクエンドポイント統合テスト開始...")
    
    # 1. 標準的なWMS GetMapリクエスト
    print("\n1️⃣ 標準WMS GetMapリクエストテスト")
    wms_params = {
        'SERVICE': 'WMS',
        'VERSION': '1.3.0',
        'REQUEST': 'GetMap',
        'LAYERS': 'test',
        'STYLES': '',
        'CRS': 'EPSG:3857',
        'BBOX': '15559350,4273995,15561350,4275995',
        'WIDTH': '512',
        'HEIGHT': '512',
        'FORMAT': 'image/png'
    }
    
    try:
        wms_url = f"{base_url}/wms?{urlencode(wms_params)}"
        print(f"📡 WMS URL: {wms_url}")
        
        with urllib.request.urlopen(wms_url) as response:
            content = response.read()
            status_code = response.getcode()
            content_type = response.headers.get('Content-Type', 'unknown')
            
        print(f"✅ WMS Status: {status_code}")
        print(f"📊 WMS Content-Length: {len(content)} bytes")
        print(f"🏷️ WMS Content-Type: {content_type}")
        
        if status_code == 200 and len(content) > 1000:
            print("✅ 標準WMSリクエスト成功")
        else:
            print("⚠️ 標準WMSリクエストが期待される結果ではありません")
            
    except urllib.error.URLError as e:
        print(f"❌ 標準WMSリクエストエラー: {e}")
    except Exception as e:
        print(f"❌ 標準WMSリクエストエラー: {e}")
    
    # 2. パーマリンクパラメータでのWMSリクエスト
    print("\n2️⃣ パーマリンクパラメータWMSリクエストテスト")
    permalink_params = {
        'x': '15560350.158668',
        'y': '4274995.922363',
        'scale': '21280.2',
        'crs': 'EPSG:3857',
        'rotation': '0.00',
        'width': '512',
        'height': '512'
    }
    
    try:
        permalink_url = f"{base_url}/wms?{urlencode(permalink_params)}"
        print(f"📡 Permalink URL: {permalink_url}")
        
        with urllib.request.urlopen(permalink_url) as response:
            content = response.read()
            status_code = response.getcode()
            content_type = response.headers.get('Content-Type', 'unknown')
            
        print(f"✅ Permalink Status: {status_code}")
        print(f"📊 Permalink Content-Length: {len(content)} bytes")
        print(f"🏷️ Permalink Content-Type: {content_type}")
        
        if status_code == 200 and len(content) > 1000:
            print("✅ パーマリンクパラメータWMSリクエスト成功")
            
            # 結果を保存
            with open("wms_permalink_result.png", "wb") as f:
                f.write(content)
            print("💾 結果を wms_permalink_result.png に保存しました")
            
        else:
            print("⚠️ パーマリンクパラメータWMSリクエストが期待される結果ではありません")
            print(f"📄 Response content preview: {content[:200]}")
            
    except urllib.error.URLError as e:
        print(f"❌ パーマリンクパラメータWMSリクエストエラー: {e}")
    except Exception as e:
        print(f"❌ パーマリンクパラメータWMSリクエストエラー: {e}")
    
    # 3. 混合パラメータ（予期しない動作をチェック）
    print("\n3️⃣ 混合パラメータテスト")
    mixed_params = {
        'SERVICE': 'WMS',
        'x': '15560350.158668',
        'y': '4274995.922363',
        'scale': '21280.2',
        'WIDTH': '256',
        'HEIGHT': '256'
    }
    
    try:
        mixed_url = f"{base_url}/wms?{urlencode(mixed_params)}"
        print(f"📡 Mixed URL: {mixed_url}")
        
        with urllib.request.urlopen(mixed_url) as response:
            content = response.read()
            status_code = response.getcode()
            
        print(f"✅ Mixed Status: {status_code}")
        print(f"📊 Mixed Content-Length: {len(content)} bytes")
        
        if status_code == 200:
            print("✅ 混合パラメータリクエスト処理済み")
        else:
            print("⚠️ 混合パラメータで予期しない結果")
            
    except urllib.error.URLError as e:
        print(f"❌ 混合パラメータリクエストエラー: {e}")
    except Exception as e:
        print(f"❌ 混合パラメータリクエストエラー: {e}")
    
    print("\n🏁 WMS/パーマリンクエンドポイント統合テスト完了")

def test_parameter_detection():
    """パラメータ検出ロジックをテスト"""
    print("\n🔍 パラメータ検出ロジックテスト")
    
    # パーマリンクパラメータの存在確認
    permalink_params = ['x', 'y', 'scale', 'crs']
    wms_params = ['SERVICE', 'REQUEST', 'LAYERS', 'BBOX']
    
    test_cases = [
        {'x': '123', 'y': '456', 'scale': '1000', 'crs': 'EPSG:3857'},  # パーマリンク
        {'SERVICE': 'WMS', 'REQUEST': 'GetMap', 'LAYERS': 'test', 'BBOX': '1,2,3,4'},  # WMS
        {'x': '123', 'SERVICE': 'WMS'},  # 混合
        {}  # 空
    ]
    
    for i, params in enumerate(test_cases, 1):
        has_permalink = any(p in params for p in permalink_params)
        has_wms = any(p in params for p in wms_params)
        
        print(f"ケース {i}: {params}")
        print(f"  📍 パーマリンクパラメータ検出: {has_permalink}")
        print(f"  🗺️ WMSパラメータ検出: {has_wms}")
        
        if has_permalink and not has_wms:
            print("  ➡️ パーマリンクとして処理")
        elif has_wms and not has_permalink:
            print("  ➡️ WMSとして処理")
        elif has_permalink and has_wms:
            print("  ➡️ 混合 - 優先ルールが必要")
        else:
            print("  ➡️ 不明なリクエスト")
        print()

if __name__ == "__main__":
    print("🚀 統合WMS/パーマリンクエンドポイントテスト")
    
    # パラメータ検出のテスト
    test_parameter_detection()
    
    # 実際のエンドポイントテスト
    try:
        test_wms_permalink_integration()
    except KeyboardInterrupt:
        print("\n⏹️ テスト中断")
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()