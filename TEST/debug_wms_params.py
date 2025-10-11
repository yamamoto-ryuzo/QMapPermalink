#!/usr/bin/env python3
"""
WMSエンドポイントのパラメータをデバッグするスクリプト
"""

import urllib.request
import urllib.error
from urllib.parse import urlencode

def debug_wms_endpoint_params():
    """WMSエンドポイントに送信されるパラメータをデバッグ"""
    base_url = "http://localhost:8089"
    
    print("🔍 WMSエンドポイントパラメータデバッグ")
    
    # 1. 標準WMSリクエスト（動作確認）
    print("\n1️⃣ 標準WMS GetMapリクエスト（動作確認）")
    wms_params = {
        'SERVICE': 'WMS',
        'VERSION': '1.3.0', 
        'REQUEST': 'GetMap',
        'LAYERS': 'test',
        'STYLES': '',
        'CRS': 'EPSG:3857',
        'BBOX': '15559350,4273995,15561350,4275995',
        'WIDTH': '256',
        'HEIGHT': '256',
        'FORMAT': 'image/png'
    }
    
    test_request(base_url + "/wms", wms_params, "標準WMS")
    
    # 2. 最小限のパーマリンクパラメータ
    print("\n2️⃣ 最小限のパーマリンクパラメータ")
    minimal_permalink = {
        'x': '15560350.158668',
        'y': '4274995.922363',
        'scale': '21280.2'
    }
    
    test_request(base_url + "/wms", minimal_permalink, "最小パーマリンク")
    
    # 3. 完全なパーマリンクパラメータ
    print("\n3️⃣ 完全なパーマリンクパラメータ")
    full_permalink = {
        'x': '15560350.158668',
        'y': '4274995.922363', 
        'scale': '21280.2',
        'crs': 'EPSG:3857',
        'rotation': '0.0',
        'width': '256',
        'height': '256'
    }
    
    test_request(base_url + "/wms", full_permalink, "完全パーマリンク")
    
    # 4. GetCapabilitiesリクエスト
    print("\n4️⃣ GetCapabilitiesリクエスト")
    capabilities_params = {
        'SERVICE': 'WMS',
        'REQUEST': 'GetCapabilities'
    }
    
    test_request(base_url + "/wms", capabilities_params, "GetCapabilities")

def test_request(base_url, params, description):
    """リクエストをテストして結果を表示"""
    try:
        url = f"{base_url}?{urlencode(params)}"
        print(f"📡 {description} URL:")
        print(f"   {url}")
        print(f"📋 パラメータ: {list(params.keys())}")
        
        with urllib.request.urlopen(url, timeout=10) as response:
            content = response.read()
            status_code = response.getcode()
            content_type = response.headers.get('Content-Type', 'unknown')
            
        print(f"✅ Status: {status_code}")
        print(f"📊 Size: {len(content):,} bytes")
        print(f"🏷️ Type: {content_type}")
        
        if status_code == 200:
            if 'image' in content_type:
                print("🖼️ レスポンス: 画像データ")
            elif 'text' in content_type or 'xml' in content_type:
                preview = content.decode('utf-8', errors='ignore')[:200]
                print(f"📄 レスポンス preview: {preview}...")
            else:
                print(f"📄 レスポンス preview: {content[:100]}...")
        else:
            print("❌ 非200レスポンス")
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTPエラー: {e.code} {e.reason}")
        try:
            error_content = e.read().decode('utf-8', errors='ignore')
            print(f"📄 エラー内容: {error_content[:200]}...")
        except:
            print("📄 エラー内容読み取り不可")
    except urllib.error.URLError as e:
        print(f"❌ URLエラー: {e}")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
    
    print()

if __name__ == "__main__":
    debug_wms_endpoint_params()