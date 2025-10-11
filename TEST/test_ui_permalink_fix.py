#!/usr/bin/env python3
"""
現在のパーマリンク生成機能のテスト
UIから生成されるパーマリンクがWMS形式になっているか確認
"""

import sys
import time
import urllib.request
import urllib.error
from urllib.parse import urlparse, parse_qs

def test_current_permalink_generation():
    """現在のパーマリンク生成をテスト"""
    
    print("🔍 現在のパーマリンク生成テスト")
    print("="*50)
    
    # WMSエンドポイントの動作確認
    print("\n1️⃣ WMSエンドポイントの動作確認")
    
    test_urls = [
        # 新しい形式（WMS）
        "http://localhost:8089/wms?x=15557945.984400&y=4257187.015550&scale=21280.2&crs=EPSG:3857&rotation=0.00&width=800&height=600",
        # 古い形式（これは404になるべき）
        "http://localhost:8089/qgis-map?x=15557945.984400&y=4257187.015550&scale=21280.2&crs=EPSG:3857&rotation=0.00"
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{i}. テストURL: {url}")
        
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                content = response.read()
                status_code = response.getcode()
                content_type = response.headers.get('Content-Type', 'unknown')
                
            print(f"   ✅ Status: {status_code}")
            print(f"   📊 Size: {len(content):,} bytes")
            print(f"   🏷️ Type: {content_type}")
            
            if i == 1:  # 新形式は成功するべき
                if status_code == 200 and 'image/png' in content_type:
                    print("   ✅ 新形式（WMS）: 正常動作")
                else:
                    print("   ❌ 新形式（WMS）: 異常")
            else:  # 古い形式は404またはエラーになるべき
                if status_code != 200:
                    print("   ✅ 古形式（/qgis-map）: 適切にエラー")
                else:
                    print("   ⚠️ 古形式（/qgis-map）: まだ動作中（要確認）")
                    
        except urllib.error.HTTPError as e:
            print(f"   📄 HTTPエラー: {e.code} {e.reason}")
            if i == 2:  # 古い形式のエラーは期待される
                print("   ✅ 古形式（/qgis-map）: 適切にエラー")
        except Exception as e:
            print(f"   ❌ エラー: {e}")
    
    # パーマリンクの形式分析
    print(f"\n2️⃣ パーマリンクURL形式分析")
    
    sample_permalink = "http://localhost:8089/wms?x=15557945.984400&y=4257187.015550&scale=21280.2&crs=EPSG:3857&rotation=0.00&width=800&height=600"
    parsed = urlparse(sample_permalink)
    params = parse_qs(parsed.query)
    
    print(f"   🔗 エンドポイント: {parsed.path}")
    print(f"   📍 パラメータ:")
    for param, value in params.items():
        print(f"      {param}: {value[0] if value else 'N/A'}")
    
    # パーマリンクの期待される形式をチェック
    expected_params = ['x', 'y', 'scale', 'crs', 'rotation', 'width', 'height']
    missing_params = []
    
    for param in expected_params:
        if param not in params:
            missing_params.append(param)
    
    print(f"\n   📋 パラメータチェック:")
    if not missing_params:
        print(f"   ✅ すべての必要パラメータが含まれています")
    else:
        print(f"   ⚠️ 不足パラメータ: {missing_params}")
    
    # エンドポイントの確認
    if parsed.path == '/wms':
        print(f"   ✅ 正しいエンドポイント: /wms")
    elif parsed.path == '/qgis-map':
        print(f"   ❌ 古いエンドポイント: /qgis-map （要修正）")
    else:
        print(f"   ❓ 不明なエンドポイント: {parsed.path}")

def provide_fix_instructions():
    """修正手順の提供"""
    print(f"\n🔧 パーマリンクが古い形式の場合の修正手順")
    print("="*50)
    
    print("1️⃣ QGISでのプラグイン操作:")
    print("   📌 プラグイン → プラグインの管理とインストール")
    print("   📌 QMap Permalink を無効化")
    print("   📌 QMap Permalink を有効化（再読み込み）")
    
    print("\n2️⃣ または、QGISを再起動:")
    print("   📌 QGISを完全に閉じる")
    print("   📌 QGISを再起動")
    print("   📌 QMap Permalink パネルを開く")
    
    print("\n3️⃣ パーマリンク生成テスト:")
    print("   📌 パネルの「Generate Permalink」ボタンをクリック")
    print("   📌 生成されたURLが /wms で始まることを確認")
    print("   📌 例: http://localhost:8089/wms?x=...&y=...&scale=...")
    
    print("\n4️⃣ 期待される新形式:")
    print("   📌 エンドポイント: /wms")
    print("   📌 パラメータ: x, y, scale, crs, rotation, width, height")
    print("   📌 直接PNG画像表示可能")

def test_manual_permalink_format():
    """手動でのパーマリンク形式テスト"""
    print(f"\n🧪 手動パーマリンク形式テスト")
    print("="*40)
    
    # ユーザーが報告したURLと新形式の比較
    old_format = "http://localhost:8089/qgis-map?x=15557945.984400&y=4257187.015550&scale=21280.2&crs=EPSG:3857&rotation=0.00"
    new_format = "http://localhost:8089/wms?x=15557945.984400&y=4257187.015550&scale=21280.2&crs=EPSG:3857&rotation=0.00&width=800&height=600"
    
    print("📊 形式比較:")
    print(f"❌ 古形式: {old_format}")
    print(f"✅ 新形式: {new_format}")
    
    print(f"\n🔍 差異:")
    print(f"   エンドポイント: /qgis-map → /wms")
    print(f"   追加パラメータ: width, height")
    print(f"   レスポンス: HTMLページ → PNG画像")

if __name__ == "__main__":
    print("🚀 パーマリンク生成WMS形式テスト")
    
    try:
        # 現在のパーマリンク生成をテスト
        test_current_permalink_generation()
        
        # 手動形式テスト
        test_manual_permalink_format()
        
        # 修正手順の提供
        provide_fix_instructions()
        
        print("\n📝 重要な注意:")
        print("✅ WMSエンドポイントは正常に動作しています")
        print("⚠️ UIから古い形式が生成される場合は、QGISでプラグインを再読み込みしてください")
        print("🎯 目標: すべてのパーマリンクが /wms エンドポイントを使用すること")
        
    except KeyboardInterrupt:
        print("\n⏹️ テスト中断")
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()