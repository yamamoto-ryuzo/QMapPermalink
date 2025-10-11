#!/usr/bin/env python3
"""
両エンドポイント対応テスト
/wms (PNG直接) と /qgis-map (OpenLayers HTML) の両方をテスト
"""

import sys
import urllib.request
import urllib.error
from urllib.parse import urlparse, parse_qs

def test_dual_endpoint_architecture():
    """デュアルエンドポイント構成のテスト"""
    
    print("🏗️ デュアルエンドポイント構成テスト")
    print("="*50)
    
    # テストパラメータ
    test_params = {
        'x': '15557945.984400',
        'y': '4257187.015550', 
        'scale': '21280.2',
        'crs': 'EPSG:3857',
        'rotation': '0.00'
    }
    
    print(f"📋 テストパラメータ:")
    for key, value in test_params.items():
        print(f"   {key}: {value}")
    
    # 1. WMSエンドポイント（直接PNG画像）
    print(f"\n1️⃣ WMSエンドポイント（直接PNG画像）")
    wms_url = f"http://localhost:8089/wms?x={test_params['x']}&y={test_params['y']}&scale={test_params['scale']}&crs={test_params['crs']}&rotation={test_params['rotation']}&width=800&height=600"
    print(f"   🔗 URL: {wms_url}")
    
    try:
        with urllib.request.urlopen(wms_url, timeout=10) as response:
            content = response.read()
            status_code = response.getcode()
            content_type = response.headers.get('Content-Type', 'unknown')
            
        print(f"   ✅ Status: {status_code}")
        print(f"   📊 Size: {len(content):,} bytes")
        print(f"   🏷️ Type: {content_type}")
        
        if status_code == 200 and 'image/png' in content_type:
            print("   ✅ WMSエンドポイント: 正常動作（PNG画像直接返却）")
            wms_success = True
        else:
            print("   ❌ WMSエンドポイント: 異常")
            wms_success = False
            
    except Exception as e:
        print(f"   ❌ WMSエンドポイントエラー: {e}")
        wms_success = False
    
    # 2. OpenLayersエンドポイント（HTMLページ）
    print(f"\n2️⃣ OpenLayersエンドポイント（HTMLページ）")
    html_url = f"http://localhost:8089/qgis-map?x={test_params['x']}&y={test_params['y']}&scale={test_params['scale']}&crs={test_params['crs']}&rotation={test_params['rotation']}"
    print(f"   🔗 URL: {html_url}")
    
    try:
        with urllib.request.urlopen(html_url, timeout=15) as response:
            content = response.read().decode('utf-8')
            status_code = response.getcode()
            content_type = response.headers.get('Content-Type', 'unknown')
            
        print(f"   ✅ Status: {status_code}")
        print(f"   📊 Size: {len(content):,} characters")
        print(f"   🏷️ Type: {content_type}")
        
        if status_code == 200 and 'text/html' in content_type:
            print("   ✅ OpenLayersエンドポイント: 正常動作（HTMLページ生成）")
            
            # HTML内容の詳細チェック
            html_checks = [
                ('OpenLayers', 'OpenLayersライブラリ'),
                ('/wms', 'WMSエンドポイント参照'),
                ('QMap Permalink', 'タイトル'),
                ('ol.Map', 'OpenLayersマップ初期化')
            ]
            
            print("   📋 HTML内容チェック:")
            for check_text, description in html_checks:
                if check_text in content:
                    print(f"      ✅ {description}: 確認")
                else:
                    print(f"      ⚠️ {description}: 見つからない")
            
            html_success = True
        else:
            print("   ❌ OpenLayersエンドポイント: 異常")
            html_success = False
            
    except Exception as e:
        print(f"   ❌ OpenLayersエンドポイントエラー: {e}")
        html_success = False
    
    # 3. 構成の説明
    print(f"\n3️⃣ エンドポイント構成")
    print("   📍 /wms エンドポイント:")
    print("      ├─ 用途: 直接PNG画像返却")
    print("      ├─ レスポンス: image/png")
    print("      └─ 使用場面: 他のアプリケーションからの画像取得")
    
    print("\n   🌐 /qgis-map エンドポイント:")
    print("      ├─ 用途: OpenLayersベースHTMLページ生成")
    print("      ├─ レスポンス: text/html")
    print("      ├─ 内部動作: /wmsエンドポイントを画像ソースとして参照")
    print("      └─ 使用場面: ブラウザでのインタラクティブ表示")
    
    # 4. 総合結果
    print(f"\n📊 総合テスト結果:")
    if wms_success and html_success:
        print("   ✅ デュアルエンドポイント構成: 完全動作")
        print("   🎯 両方のエンドポイントが正常に機能しています")
        return True
    else:
        print("   ❌ デュアルエンドポイント構成: 一部問題あり")
        if not wms_success:
            print("   🔧 WMSエンドポイントの修正が必要")
        if not html_success:
            print("   🔧 OpenLayersエンドポイントの修正が必要")
        return False

def demonstrate_use_cases():
    """使用ケースの説明"""
    print(f"\n💡 使用ケース")
    print("="*40)
    
    print("1️⃣ UIから生成されるパーマリンク:")
    print("   📌 形式: http://localhost:8089/qgis-map?x=...&y=...&scale=...")
    print("   📌 動作: OpenLayersページが表示される")
    print("   📌 特徴: ブラウザでインタラクティブに操作可能")
    
    print("\n2️⃣ 直接画像取得:")
    print("   📌 形式: http://localhost:8089/wms?x=...&y=...&scale=...&width=...&height=...")
    print("   📌 動作: PNG画像が直接返される")
    print("   📌 特徴: 他のアプリケーションからの画像取得に最適")
    
    print("\n3️⃣ OpenLayersページ内での画像取得:")
    print("   📌 /qgis-map ページの内部で /wms エンドポイントを参照")
    print("   📌 HTMLページ内のJavaScriptが /wms から画像を取得")
    print("   📌 シームレスな統合動作")

def provide_update_instructions():
    """更新手順の説明"""
    print(f"\n🔄 プラグイン更新手順")
    print("="*40)
    
    print("📦 新しいバージョン: 1.10.22")
    print("📁 ファイル: dist/qmap_permalink_1.10.22.zip")
    
    print("\n🚀 更新方法:")
    print("1️⃣ QGISでプラグイン無効化/有効化")
    print("2️⃣ QGISの完全再起動")
    print("3️⃣ 手動インストール（推奨）")
    
    print("\n✅ 更新後の確認:")
    print("📌 Generate Permalinkボタン → /qgis-map URL生成")
    print("📌 生成されたURLをブラウザで開く → OpenLayersページ表示")
    print("📌 OpenLayersページ内で /wms から画像が読み込まれる")

if __name__ == "__main__":
    print("🚀 デュアルエンドポイント構成テスト開始")
    
    try:
        # デュアルエンドポイントのテスト
        success = test_dual_endpoint_architecture()
        
        # 使用ケースの説明
        demonstrate_use_cases()
        
        # 更新手順の説明
        provide_update_instructions()
        
        print(f"\n📋 まとめ:")
        if success:
            print("✅ デュアルエンドポイント構成完成")
            print("🎯 /wms (PNG直接) + /qgis-map (OpenLayers HTML)")
            print("🔧 HTMLページ内で /wms を参照する統合構成")
        else:
            print("⚠️ 一部のエンドポイントに問題があります")
            print("🔧 サーバーの起動状況を確認してください")
        
    except KeyboardInterrupt:
        print("\n⏹️ テスト中断")
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()