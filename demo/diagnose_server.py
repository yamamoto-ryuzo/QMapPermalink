#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMapPermalink HTTPサーバーの詳細診断スクリプト

現在のサーバーの状態と応答を詳しく調査します。
"""

import urllib.request
import urllib.parse
import sys
from urllib.error import URLError, HTTPError

def test_endpoint(url, description):
    """エンドポイントをテストして詳細情報を表示"""
    print(f"\n🔍 {description}")
    print(f"URL: {url}")
    print("-" * 60)
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            status = response.status
            headers = dict(response.headers)
            content = response.read()
            
            print(f"✅ ステータス: {status}")
            print(f"📋 ヘッダー:")
            for key, value in headers.items():
                print(f"   {key}: {value}")
            
            print(f"📄 コンテンツ長: {len(content)} bytes")
            
            # テキストコンテンツの場合は一部を表示
            try:
                text_content = content.decode('utf-8')
                print(f"📝 コンテンツ（最初の500文字）:")
                print(text_content[:500])
                if len(text_content) > 500:
                    print("...")
            except UnicodeDecodeError:
                print(f"🔢 バイナリコンテンツ（最初の50バイト）:")
                print(content[:50])
                
            return True
            
    except HTTPError as e:
        print(f"❌ HTTPエラー: {e.code} {e.reason}")
        try:
            error_content = e.read().decode('utf-8')
            print(f"📄 エラー内容:")
            print(error_content)
        except:
            print("📄 エラー内容を読み取れませんでした")
        return False
        
    except URLError as e:
        print(f"❌ 接続エラー: {e.reason}")
        return False
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

def main():
    """メイン診断関数"""
    print("🩺 QMapPermalink HTTPサーバー 詳細診断")
    print("=" * 60)
    
    base_url = "http://localhost:8089"
    
    # テストするエンドポイント一覧
    endpoints = [
        # 既存エンドポイント
        (f"{base_url}/qgis-map?lat=35.681&lon=139.767&scale=25000", "既存のQGIS Map エンドポイント"),
        (f"{base_url}/qgis-png?lat=35.681&lon=139.767&scale=25000&width=400&height=300", "既存のQGIS PNG エンドポイント"),
        
        # WMSエンドポイント
        (f"{base_url}/wms?SERVICE=WMS&REQUEST=GetCapabilities", "WMS GetCapabilities"),
        (f"{base_url}/wms?SERVICE=WMS&REQUEST=GetMap&BBOX=139.5,35.5,139.9,35.9&WIDTH=400&HEIGHT=400&CRS=EPSG:4326&FORMAT=image/png", "WMS GetMap"),
        
        # タイルエンドポイント
        (f"{base_url}/tiles/10/904/403.png", "タイル配信"),
        
        # 存在しないエンドポイント（404確認用）
        (f"{base_url}/nonexistent", "存在しないエンドポイント（404確認）"),
    ]
    
    results = []
    
    for url, description in endpoints:
        success = test_endpoint(url, description)
        results.append((description, success))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 診断結果サマリー")
    print("=" * 60)
    
    success_count = 0
    for description, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {description}")
        if success:
            success_count += 1
    
    print(f"\n成功: {success_count}/{len(results)}")
    
    # 推奨アクション
    print("\n" + "=" * 60)
    print("💡 推奨アクション")
    print("=" * 60)
    
    if success_count == 0:
        print("❌ 全エンドポイントが失敗 - サーバーが起動していません")
        print("   → QGISでQMapPermalinkプラグインを確認してください")
    elif results[2][1] or results[3][1] or results[4][1]:  # WMS/タイル関連が成功
        print("✅ WMS機能が動作しています")
    elif results[0][1] or results[1][1]:  # 既存機能のみ成功
        print("⚠️ 既存機能のみ動作 - WMS機能が実装されていません")
        print("   → プラグインを更新する必要があります")
        print("   → 以下の方法を試してください:")
        print("     1. QGISでプラグインを無効化→有効化")
        print("     2. QGISを再起動")
        print("     3. プラグインファイルが正しく更新されているか確認")
    else:
        print("⚠️ 部分的な動作 - 詳細を確認してください")

if __name__ == "__main__":
    main()