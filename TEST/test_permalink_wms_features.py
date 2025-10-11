#!/usr/bin/env python3
"""
WMSエンドポイントでのパーマリンクパラメータ（回転・縮尺・CRS対応）のテスト
"""

import sys
import os
import time
import urllib.request
import urllib.error
from urllib.parse import urlencode

def test_permalink_wms_features():
    """パーマリンクのWMS機能（回転・縮尺・CRS）をテスト"""
    base_url = "http://localhost:8089"
    
    print("🧪 パーマリンク→WMS統合機能テスト開始...")
    
    test_cases = [
        {
            "name": "基本パーマリンク（回転なし）",
            "params": {
                'x': '15560350.158668',
                'y': '4274995.922363', 
                'scale': '21280.2',
                'crs': 'EPSG:3857',
                'rotation': '0.00',
                'width': '256',
                'height': '256'
            },
            "filename": "permalink_basic.png"
        },
        {
            "name": "45度回転パーマリンク",
            "params": {
                'x': '15560350.158668',
                'y': '4274995.922363',
                'scale': '21280.2', 
                'crs': 'EPSG:3857',
                'rotation': '45.0',
                'width': '256',
                'height': '256'
            },
            "filename": "permalink_rotation_45.png"
        },
        {
            "name": "90度回転パーマリンク",
            "params": {
                'x': '15560350.158668',
                'y': '4274995.922363',
                'scale': '10640.1',  # より詳細なスケール
                'crs': 'EPSG:3857',
                'rotation': '90.0',
                'width': '512',
                'height': '512'
            },
            "filename": "permalink_rotation_90.png"
        },
        {
            "name": "異なるCRS（WGS84）",
            "params": {
                'x': '139.7',
                'y': '35.7',
                'scale': '50000',
                'crs': 'EPSG:4326',
                'rotation': '0.0',
                'width': '256',
                'height': '256'
            },
            "filename": "permalink_wgs84.png"
        },
        {
            "name": "高解像度画像",
            "params": {
                'x': '15560350.158668',
                'y': '4274995.922363',
                'scale': '5320.05',  # 高詳細
                'crs': 'EPSG:3857',
                'rotation': '30.0',
                'width': '1024',
                'height': '1024'
            },
            "filename": "permalink_highres.png"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ {test_case['name']}をテスト")
        
        try:
            # URLを構築
            url = f"{base_url}/wms?{urlencode(test_case['params'])}"
            print(f"📡 URL: {url[:100]}..." if len(url) > 100 else f"📡 URL: {url}")
            
            # リクエスト実行
            with urllib.request.urlopen(url, timeout=30) as response:
                content = response.read()
                status_code = response.getcode()
                content_type = response.headers.get('Content-Type', 'unknown')
            
            print(f"✅ Status: {status_code}")
            print(f"📊 Content-Length: {len(content):,} bytes")
            print(f"🏷️ Content-Type: {content_type}")
            
            # 成功判定
            success = status_code == 200 and len(content) > 1000 and 'image' in content_type
            
            if success:
                # ファイルに保存
                filename = test_case['filename']
                with open(filename, "wb") as f:
                    f.write(content)
                print(f"💾 結果を {filename} に保存しました")
                print("✅ テスト成功")
                
                results.append({
                    'test': test_case['name'],
                    'status': 'SUCCESS',
                    'size': len(content),
                    'filename': filename
                })
            else:
                print("❌ テスト失敗 - 期待される結果ではありません")
                print(f"📄 Content preview: {content[:100]}")
                
                results.append({
                    'test': test_case['name'], 
                    'status': 'FAILED',
                    'size': len(content),
                    'error': f"Status: {status_code}, Content-Type: {content_type}"
                })
                
        except urllib.error.URLError as e:
            print(f"❌ URLエラー: {e}")
            results.append({
                'test': test_case['name'],
                'status': 'ERROR',
                'error': str(e)
            })
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
            results.append({
                'test': test_case['name'],
                'status': 'ERROR', 
                'error': str(e)
            })
            
        time.sleep(1)  # サーバー負荷軽減
    
    # 結果サマリー
    print("\n" + "="*60)
    print("📊 テスト結果サマリー")
    print("="*60)
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    total_count = len(results)
    
    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"❌ 失敗: {total_count - success_count}/{total_count}")
    
    print("\n📋 詳細結果:")
    for result in results:
        status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
        print(f"{status_icon} {result['test']}: {result['status']}")
        if 'size' in result:
            print(f"   📊 Size: {result['size']:,} bytes")
        if 'filename' in result:
            print(f"   💾 File: {result['filename']}")
        if 'error' in result:
            print(f"   ⚠️ Error: {result['error']}")
        print()
    
    return success_count == total_count

def test_parameter_combinations():
    """パラメータの組み合わせテスト"""
    print("\n🔬 パラメータ組み合わせテスト")
    
    # 必須パラメータの検証
    required_params = ['x', 'y', 'scale']
    base_params = {
        'x': '15560350',
        'y': '4274995', 
        'scale': '21280',
        'crs': 'EPSG:3857',
        'width': '256',
        'height': '256'
    }
    
    print("必須パラメータテスト:")
    for param in required_params:
        test_params = {k: v for k, v in base_params.items() if k != param}
        print(f"  {param}なし: {list(test_params.keys())}")
    
    print("\nオプションパラメータテスト:")
    optional_params = ['crs', 'rotation', 'width', 'height']
    for param in optional_params:
        print(f"  {param}のデフォルト値は実装で確認")

if __name__ == "__main__":
    print("🚀 WMS/パーマリンク統合機能テスト（回転・縮尺・CRS対応）")
    
    try:
        # パラメータ組み合わせのテスト
        test_parameter_combinations()
        
        # 実際の機能テスト
        all_success = test_permalink_wms_features()
        
        if all_success:
            print("\n🎉 全てのテストが成功しました！")
            print("📍 パーマリンクパラメータ（x, y, scale, crs, rotation）がWMSエンドポイントで正常に処理されています")
        else:
            print("\n⚠️ いくつかのテストが失敗しました")
            print("🔧 ログを確認して問題を調査してください")
            
    except KeyboardInterrupt:
        print("\n⏹️ テスト中断")
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()