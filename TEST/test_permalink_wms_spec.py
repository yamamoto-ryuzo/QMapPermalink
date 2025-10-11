#!/usr/bin/env python3
"""
パーマリンクのWMS仕様対応確認テスト
"""

import urllib.request
import urllib.error
from urllib.parse import urlencode, urlparse, parse_qs
import webbrowser
import os

def test_permalink_generation_wms_compliance():
    """パーマリンク生成がWMS仕様に準拠しているかテスト"""
    
    print("🔍 パーマリンクのWMS仕様対応確認テスト")
    print("="*60)
    
    # 1. 生成されるパーマリンクのURLパターンを確認
    print("\n1️⃣ パーマリンク生成URL形式の確認")
    
    expected_patterns = [
        "WMSエンドポイント使用: /wms?x=...&y=...&scale=...&crs=...&rotation=...&width=...&height=...",
        "従来の/qgis-mapエンドポイント廃止",
        "パーマリンクパラメータ形式での統一"
    ]
    
    for pattern in expected_patterns:
        print(f"   📋 {pattern}")
    
    # 2. 実際のパーマリンクエンドポイントをテスト
    print("\n2️⃣ 実際のパーマリンクエンドポイント動作テスト")
    
    base_url = "http://localhost:8089"
    
    # WMS形式のパーマリンクをテスト
    wms_permalink_urls = [
        {
            "name": "WMSパーマリンク（基本）",
            "url": f"{base_url}/wms?x=15560350.158668&y=4274995.922363&scale=21280.2&crs=EPSG:3857&rotation=0.0&width=800&height=600",
            "expected_content_type": "image/png"
        },
        {
            "name": "WMSパーマリンク（回転付き）",
            "url": f"{base_url}/wms?x=15560350.158668&y=4274995.922363&scale=10640.1&crs=EPSG:3857&rotation=45.0&width=512&height=512",
            "expected_content_type": "image/png"
        }
    ]
    
    wms_success = 0
    
    for test_case in wms_permalink_urls:
        print(f"\n🧪 {test_case['name']}")
        print(f"   URL: {test_case['url']}")
        
        try:
            with urllib.request.urlopen(test_case['url'], timeout=15) as response:
                content = response.read()
                status_code = response.getcode()
                content_type = response.headers.get('Content-Type', 'unknown')
            
            print(f"   ✅ Status: {status_code}")
            print(f"   📊 Size: {len(content):,} bytes")
            print(f"   🏷️ Type: {content_type}")
            
            if (status_code == 200 and 
                test_case['expected_content_type'] in content_type and 
                len(content) > 1000):
                print(f"   ✅ WMS仕様準拠: 成功")
                wms_success += 1
            else:
                print(f"   ❌ WMS仕様準拠: 失敗")
                
        except Exception as e:
            print(f"   ❌ エラー: {e}")
    
    # 3. HTMLページ生成のテスト（WMSエンドポイント使用確認）
    print(f"\n3️⃣ HTMLページ生成でのWMSエンドポイント使用確認")
    
    html_test_url = f"{base_url}/qgis-map?x=15560350.158668&y=4274995.922363&scale=21280.2&crs=EPSG:3857&rotation=0.0&width=800&height=600"
    
    try:
        print(f"   URL: {html_test_url}")
        
        with urllib.request.urlopen(html_test_url, timeout=20) as response:
            content = response.read()
            status_code = response.getcode()
            content_type = response.headers.get('Content-Type', 'unknown')
        
        print(f"   ✅ Status: {status_code}")
        print(f"   📊 Size: {len(content):,} bytes")
        print(f"   🏷️ Type: {content_type}")
        
        if status_code == 200 and 'text/html' in content_type:
            html_content = content.decode('utf-8', errors='ignore')
            
            # HTMLの内容をチェック
            wms_checks = [
                ('/wms?x=' in html_content, "WMSエンドポイントURL参照"),
                ('src="http://localhost:' in html_content and '/wms?' in html_content, "画像ソースでWMS使用"),
                ('QMap Permalink' in html_content, "適切なタイトル"),
                ('rotation=' in html_content, "回転パラメータ含有"),
                ('scale=' in html_content, "縮尺パラメータ含有")
            ]
            
            html_success = 0
            for check, description in wms_checks:
                if check:
                    print(f"   ✅ {description}: OK")
                    html_success += 1
                else:
                    print(f"   ❌ {description}: NG")
            
            # HTMLファイルとして保存
            with open("wms_permalink_page.html", "wb") as f:
                f.write(content)
            print(f"   💾 HTMLページを wms_permalink_page.html に保存")
            
            if html_success >= 4:
                print(f"   ✅ HTMLページのWMS統合: 成功 ({html_success}/5)")
            else:
                print(f"   ⚠️ HTMLページのWMS統合: 部分的成功 ({html_success}/5)")
                
        else:
            print(f"   ❌ HTMLページ生成失敗")
            html_success = 0
            
    except Exception as e:
        print(f"   ❌ HTMLページテストエラー: {e}")
        html_success = 0
    
    # 4. 総合結果
    print(f"\n📊 総合結果")
    print("="*60)
    print(f"WMS画像エンドポイント: {wms_success}/{len(wms_permalink_urls)} 成功")
    print(f"HTMLページWMS統合: {'成功' if html_success >= 4 else '失敗'}")
    
    overall_success = (wms_success == len(wms_permalink_urls) and html_success >= 4)
    
    if overall_success:
        print("\n🎉 パーマリンクのWMS仕様対応完了！")
        print("✅ すべてのパーマリンクがWMSエンドポイントを使用")
        print("✅ HTMLページもWMSエンドポイント統合済み")
        print("✅ 回転・縮尺・CRS指定すべて対応")
    else:
        print("\n⚠️ パーマリンクのWMS仕様対応に問題があります")
        print("🔧 QGISでプラグインを再読み込みしてから再テストしてください")
    
    return overall_success

def analyze_url_patterns():
    """URLパターンの分析"""
    print("\n🔍 URLパターン分析")
    print("="*40)
    
    sample_urls = [
        "旧形式: http://localhost:8089/qgis-map?x=123&y=456&scale=1000",
        "新形式: http://localhost:8089/wms?x=123&y=456&scale=1000&crs=EPSG:3857&rotation=0.0&width=800&height=600",
        "従来WMS: http://localhost:8089/wms?SERVICE=WMS&REQUEST=GetMap&BBOX=1,2,3,4&..."
    ]
    
    for url_example in sample_urls:
        print(f"   📋 {url_example}")
    
    print("\n✅ 新しいパーマリンク仕様:")
    print("   🎯 エンドポイント: /wms （統一）")
    print("   📍 パラメータ: x, y, scale, crs, rotation, width, height")
    print("   🖼️ レスポンス: PNG画像（直接表示可能）")
    print("   🌐 HTMLページ: WMSエンドポイントを参照")

if __name__ == "__main__":
    print("🚀 パーマリンクWMS仕様対応確認テスト")
    
    try:
        # URLパターン分析
        analyze_url_patterns()
        
        # 実際の動作テスト
        success = test_permalink_generation_wms_compliance()
        
        if success:
            print("\n🏆 テスト完了: パーマリンクのWMS仕様対応が正常に動作しています")
        else:
            print("\n🔧 追加作業が必要: 一部の機能が期待通りに動作していません")
            
    except KeyboardInterrupt:
        print("\n⏹️ テスト中断")
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()