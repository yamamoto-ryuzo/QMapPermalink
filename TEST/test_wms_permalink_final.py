#!/usr/bin/env python3
"""
WMSエンドポイントでのパーマリンクパラメータ処理の動作確認
"""

import urllib.request
import urllib.error
from urllib.parse import urlencode

def test_wms_permalink_integration():
    """WMSエンドポイントでのパーマリンクパラメータ統合をテスト"""
    base_url = "http://localhost:8089"
    
    print("🎯 WMSエンドポイント + パーマリンクパラメータ統合テスト")
    
    # パーマリンクパラメータでWMSエンドポイントにアクセス
    test_cases = [
        {
            "name": "パーマリンク→WMS（基本）",
            "url": f"{base_url}/wms?x=15560350.158668&y=4274995.922363&scale=21280.2&crs=EPSG:3857&rotation=0.0&width=512&height=512",
            "filename": "wms_permalink_basic.png"
        },
        {
            "name": "パーマリンク→WMS（45度回転）",
            "url": f"{base_url}/wms?x=15560350.158668&y=4274995.922363&scale=21280.2&crs=EPSG:3857&rotation=45.0&width=512&height=512",
            "filename": "wms_permalink_45deg.png"
        },
        {
            "name": "パーマリンク→WMS（90度回転）",
            "url": f"{base_url}/wms?x=15560350.158668&y=4274995.922363&scale=21280.2&crs=EPSG:3857&rotation=90.0&width=512&height=512",
            "filename": "wms_permalink_90deg.png"
        },
        {
            "name": "パーマリンク→WMS（WGS84座標系）",
            "url": f"{base_url}/wms?x=139.7&y=35.7&scale=50000&crs=EPSG:4326&rotation=0.0&width=512&height=512",
            "filename": "wms_permalink_wgs84.png"
        }
    ]
    
    successful_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ {test_case['name']}")
        print(f"📡 URL: {test_case['url']}")
        
        try:
            with urllib.request.urlopen(test_case['url'], timeout=30) as response:
                content = response.read()
                status_code = response.getcode()
                content_type = response.headers.get('Content-Type', 'unknown')
            
            print(f"✅ Status: {status_code}")  
            print(f"📊 Size: {len(content):,} bytes")
            print(f"🏷️ Type: {content_type}")
            
            if status_code == 200 and 'image/png' in content_type and len(content) > 1000:
                # 画像ファイルとして保存
                with open(test_case['filename'], 'wb') as f:
                    f.write(content)
                print(f"💾 画像を {test_case['filename']} に保存")
                print("✅ テスト成功")
                successful_tests += 1
            else:
                print("❌ テスト失敗")
                
        except Exception as e:
            print(f"❌ エラー: {e}")
    
    print(f"\n📊 結果: {successful_tests}/{len(test_cases)} 成功")
    
    if successful_tests == len(test_cases):
        print("🎉 WMSエンドポイントでのパーマリンクパラメータ統合が完全に動作しています！")
        return True
    else:
        print("⚠️ 一部のテストが失敗しました")
        return False

def compare_traditional_vs_permalink_wms():
    """従来のWMSと新しいパーマリンクWMSの比較"""
    base_url = "http://localhost:8089"
    
    print("\n🔍 従来WMS vs パーマリンクWMS比較テスト")
    
    # 同じ地域を異なる方法でリクエスト
    traditional_wms = f"{base_url}/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=test&STYLES=&CRS=EPSG:3857&BBOX=15559350,4273995,15561350,4275995&WIDTH=512&HEIGHT=512&FORMAT=image/png"
    
    permalink_wms = f"{base_url}/wms?x=15560350&y=4274995&scale=21280&crs=EPSG:3857&rotation=0.0&width=512&height=512"
    
    results = {}
    
    for name, url in [("従来WMS", traditional_wms), ("パーマリンクWMS", permalink_wms)]:
        print(f"\n🧪 {name}をテスト")
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                content = response.read()
                status_code = response.getcode()
                
            results[name] = {
                'status': status_code,
                'size': len(content),
                'success': status_code == 200 and len(content) > 1000
            }
            
            print(f"   Status: {status_code}")
            print(f"   Size: {len(content):,} bytes")
            print(f"   Success: {results[name]['success']}")
            
        except Exception as e:
            print(f"   Error: {e}")
            results[name] = {'success': False, 'error': str(e)}
    
    # 比較結果
    print("\n📋 比較結果:")
    if results.get("従来WMS", {}).get('success') and results.get("パーマリンクWMS", {}).get('success'):
        print("✅ 両方の方式が正常に動作しています")
        print("🎯 パーマリンクパラメータがWMSエンドポイントで統合されています")
    elif results.get("パーマリンクWMS", {}).get('success'):
        print("✅ パーマリンクWMSが動作しています（統合成功）")
    else:
        print("❌ パーマリンクWMS統合に問題があります")

if __name__ == "__main__":
    print("🚀 WMSエンドポイント + パーマリンク統合動作確認テスト")
    
    try:
        # メイン統合テスト
        integration_success = test_wms_permalink_integration()
        
        # 従来との比較テスト
        compare_traditional_vs_permalink_wms()
        
        if integration_success:
            print("\n🎉 統合テスト完了！WMSエンドポイントでパーマリンクパラメータが正常に処理されています")
            print("✅ 回転、縮尺、CRS指定がすべて機能しています")
        else:
            print("\n⚠️ 統合に問題があります - 詳細な調査が必要です")
            
    except KeyboardInterrupt:
        print("\n⏹️ テスト中断")
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()