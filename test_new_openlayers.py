#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新しいインタラクティブOpenLayersマップ機能のテスト
"""

import sys
import os

# プロジェクトルートをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_interactive_openlayers():
    """インタラクティブOpenLayersマップの生成をテスト"""
    print("🚀 インタラクティブOpenLayersマップテスト開始")
    
    try:
        # QMapWebMapGeneratorクラスをインポート
        from qmap_permalink.qmap_webmap_generator import QMapWebMapGenerator
        
        # テスト用ナビゲーションデータ
        navigation_data = {
            'x': 139.6917,  # 東京駅経度
            'y': 35.6895,   # 東京駅緯度
            'scale': 25000,
            'crs': 'EPSG:4326',
            'rotation': 0
        }
        
        # その他のパラメータ
        image_width = 1200
        image_height = 800  
        server_port = 8000
        
        # モックのifaceオブジェクトを作成
        class MockIface:
            pass
        
        # ジェネレータを初期化
        generator = QMapWebMapGenerator(MockIface())
        
        print("📋 テストパラメータ:")
        print(f"  navigation_data: {navigation_data}")
        print(f"  image_width: {image_width}")
        print(f"  image_height: {image_height}")
        print(f"  server_port: {server_port}")
        
        # インタラクティブマップHTMLを生成
        print("\n🗺️ インタラクティブOpenLayersマップ生成中...")
        html_content = generator.generate_wms_based_html_page(
            navigation_data=navigation_data,
            image_width=image_width,
            image_height=image_height,
            server_port=server_port
        )
        
        # 結果を保存
        output_file = "test_interactive_openlayers.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ インタラクティブマップHTMLファイルが生成されました: {output_file}")
        print(f"📏 ファイルサイズ: {len(html_content):,} 文字")
        
        # HTMLコンテンツの要素を確認
        print("\n🔍 生成されたHTMLの確認:")
        key_elements = [
            "OpenLayers",
            "ol.Map",
            "ol.layer.Tile",
            "ol.source.TileWMS",
            "fullscreen",
            "coordinates-info",
            "scale-info",
            "map-controls"
        ]
        
        for element in key_elements:
            if element in html_content:
                print(f"  ✅ {element}: 含まれています")
            else:
                print(f"  ❌ {element}: 見つかりません")
        
        print(f"\n🌐 ブラウザで確認: file:///{os.path.abspath(output_file)}")
        return True
        
    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_interactive_openlayers()
    print(f"\n{'='*50}")
    print(f"テスト結果: {'成功' if success else '失敗'}")
    print(f"{'='*50}")