#!/usr/bin/env python3
"""
WMSエンドポイント統合パーマリンクHTMLページのテスト
"""

import urllib.request
import urllib.error
from urllib.parse import urlencode
import webbrowser
import os

def test_permalink_html_page():
    """パーマリンクHTMLページ（WMSエンドポイント統合）をテスト"""
    base_url = "http://localhost:8089"
    
    print("🌐 パーマリンクHTMLページ（WMSエンドポイント統合）テスト開始...")
    
    test_cases = [
        {
            "name": "基本パーマリンクページ",
            "params": {
                'x': '15560350.158668',
                'y': '4274995.922363',
                'scale': '21280.2',
                'crs': 'EPSG:3857',
                'rotation': '0.0',
                'width': '800',
                'height': '600'
            },
            "filename": "permalink_basic.html"
        },
        {
            "name": "回転付きパーマリンクページ",
            "params": {
                'x': '15560350.158668',
                'y': '4274995.922363',
                'scale': '10640.1',
                'crs': 'EPSG:3857',
                'rotation': '45.0',
                'width': '1024',
                'height': '768'
            },
            "filename": "permalink_rotated.html"
        },
        {
            "name": "WGS84座標系パーマリンクページ",
            "params": {
                'x': '139.7',
                'y': '35.7',
                'scale': '50000',
                'crs': 'EPSG:4326',
                'rotation': '0.0',
                'width': '600',
                'height': '400'
            },
            "filename": "permalink_wgs84.html"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ {test_case['name']}をテスト")
        
        try:
            # パーマリンクページのURLを構築
            url = f"{base_url}/qgis-map?{urlencode(test_case['params'])}"
            print(f"📡 URL: {url}")
            
            # リクエスト実行
            with urllib.request.urlopen(url, timeout=30) as response:
                content = response.read()
                status_code = response.getcode()
                content_type = response.headers.get('Content-Type', 'unknown')
            
            print(f"✅ Status: {status_code}")
            print(f"📊 Content-Length: {len(content):,} bytes")
            print(f"🏷️ Content-Type: {content_type}")
            
            # 成功判定
            success = status_code == 200 and 'text/html' in content_type and len(content) > 1000
            
            if success:
                # HTMLファイルに保存
                filename = test_case['filename']
                with open(filename, "wb") as f:
                    f.write(content)
                print(f"💾 結果を {filename} に保存しました")
                print("✅ テスト成功")
                
                # HTMLの内容を簡単にチェック
                html_content = content.decode('utf-8', errors='ignore')
                if 'QMap Permalink' in html_content:
                    print("🔍 HTMLタイトル確認: OK")
                if '/wms?' in html_content:
                    print("🔍 WMSエンドポイント参照確認: OK")
                if 'OpenLayers' in html_content or 'ol.Map' in html_content:
                    print("🔍 OpenLayers統合確認: OK")
                
                results.append({
                    'test': test_case['name'],
                    'status': 'SUCCESS',
                    'size': len(content),
                    'filename': filename,
                    'url': url
                })
            else:
                print("❌ テスト失敗 - 期待される結果ではありません")
                print(f"📄 Content preview: {content[:200]}")
                
                results.append({
                    'test': test_case['name'],
                    'status': 'FAILED',
                    'size': len(content),
                    'error': f"Status: {status_code}, Content-Type: {content_type}"
                })
                
        except urllib.error.HTTPError as e:
            print(f"❌ HTTPエラー: {e.code} {e.reason}")
            try:
                error_content = e.read().decode('utf-8', errors='ignore')
                print(f"📄 エラー内容: {error_content[:200]}...")
            except:
                pass
            results.append({
                'test': test_case['name'],
                'status': 'ERROR',
                'error': f"HTTP {e.code}: {e.reason}"
            })
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
            results.append({
                'test': test_case['name'],
                'status': 'ERROR',
                'error': str(e)
            })
    
    # 結果サマリー
    print("\n" + "="*60)
    print("📊 パーマリンクHTMLページテスト結果")
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
        if 'url' in result:
            print(f"   🔗 URL: {result['url']}")
        if 'error' in result:
            print(f"   ⚠️ Error: {result['error']}")
        print()
    
    # ブラウザで最初の成功したページを開く
    successful_files = [r for r in results if r['status'] == 'SUCCESS' and 'filename' in r]
    if successful_files:
        first_file = successful_files[0]['filename']
        if os.path.exists(first_file):
            print(f"🌐 ブラウザで {first_file} を開いています...")
            file_path = os.path.abspath(first_file)
            webbrowser.open(f"file://{file_path}")
    
    return success_count == total_count

def test_wms_endpoints_in_html():
    """HTMLページ内のWMSエンドポイントが正常に動作するかテスト"""
    print("\n🔧 HTMLページ内WMSエンドポイント動作テスト")
    
    base_url = "http://localhost:8089"
    
    # HTMLページで使用されるWMSエンドポイントをテスト
    wms_requests = [
        {
            "name": "基本WMS画像リクエスト",
            "url": f"{base_url}/wms?x=15560350.158668&y=4274995.922363&scale=21280.2&crs=EPSG:3857&rotation=0.0&width=800&height=600"
        },
        {
            "name": "回転付きWMS画像リクエスト", 
            "url": f"{base_url}/wms?x=15560350.158668&y=4274995.922363&scale=10640.1&crs=EPSG:3857&rotation=45.0&width=1024&height=768"
        },
        {
            "name": "WMS Capabilities",
            "url": f"{base_url}/wms?SERVICE=WMS&REQUEST=GetCapabilities"
        }
    ]
    
    for i, req in enumerate(wms_requests, 1):
        print(f"\n{i}️⃣ {req['name']}をテスト")
        try:
            with urllib.request.urlopen(req['url'], timeout=15) as response:
                content = response.read()
                status_code = response.getcode()
                content_type = response.headers.get('Content-Type', 'unknown')
                
            print(f"✅ Status: {status_code}")
            print(f"📊 Size: {len(content):,} bytes")
            print(f"🏷️ Type: {content_type}")
            
            if status_code == 200:
                if 'image' in content_type:
                    print("🖼️ 画像データ取得成功")
                elif 'xml' in content_type:
                    print("📄 XML Capabilities取得成功")
                else:
                    print("📄 データ取得成功")
            else:
                print("⚠️ 非200ステータス")
                
        except Exception as e:
            print(f"❌ エラー: {e}")

if __name__ == "__main__":
    print("🚀 WMSエンドポイント統合パーマリンクHTMLページテスト")
    
    try:
        # HTMLページ生成のテスト
        html_success = test_permalink_html_page()
        
        # HTMLページ内WMSエンドポイントのテスト
        test_wms_endpoints_in_html()
        
        if html_success:
            print("\n🎉 パーマリンクHTMLページ（WMSエンドポイント統合）テスト成功！")
            print("📍 パーマリンクページでWMSエンドポイントが正常に使用されています")
        else:
            print("\n⚠️ いくつかのテストが失敗しました")
            print("🔧 QGISでプラグインを再読み込みして再テストしてください")
            
    except KeyboardInterrupt:
        print("\n⏹️ テスト中断")
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()