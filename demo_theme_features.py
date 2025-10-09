#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMapPermalink テーマ機能デモスクリプト

このスクリプトは、QMapPermalinkプラグインの新しいテーマ機能をデモンストレーションするためのものです。
テーマ機能の使用例や実装方法を示します。
"""

# テーマ機能を含むパーマリンクの例
SAMPLE_PERMALINKS = {
    "basic": "http://localhost:8089/qgis-map?x=139.01234&y=35.12345&scale=1000.0",
    
    "with_theme": "http://localhost:8089/qgis-map?x=139.01234&y=35.12345&scale=1000.0&crs=EPSG:4326&rotation=0.00&theme=%7B%22version%22%3A%221.0%22%2C%22current_theme%22%3A%22StandardMap%22%2C%22layer_states%22%3A%7B%22layer1%22%3A%7B%22name%22%3A%22Base%20Layer%22%2C%22visible%22%3Atrue%2C%22opacity%22%3A1.0%7D%7D%7D",
    
    "complex_theme": """http://localhost:8089/qgis-map?x=139.01234&y=35.12345&scale=1000.0&crs=EPSG:4326&rotation=0.00&theme=%7B%22version%22%3A%221.0%22%2C%22current_theme%22%3A%22DetailedMap%22%2C%22layer_states%22%3A%7B%22roads%22%3A%7B%22name%22%3A%22Roads%22%2C%22visible%22%3Atrue%2C%22opacity%22%3A0.8%2C%22current_style%22%3A%22highway_style%22%7D%2C%22buildings%22%3A%7B%22name%22%3A%22Buildings%22%2C%22visible%22%3Afalse%2C%22opacity%22%3A0.6%7D%7D%7D"""
}

def demonstrate_theme_features():
    """テーマ機能のデモンストレーション"""
    print("=== QMapPermalink テーマ機能デモ ===\n")
    
    print("1. 基本的なパーマリンク（テーマなし）:")
    print(f"   {SAMPLE_PERMALINKS['basic']}")
    print("   - 位置情報のみ")
    print("   - シンプルで短いURL")
    print("   - 従来通りの動作\n")
    
    print("2. テーマ情報を含むパーマリンク:")
    print(f"   {SAMPLE_PERMALINKS['with_theme']}")
    print("   - 位置情報 + テーマ情報")
    print("   - レイヤー状態も保存")
    print("   - 完全な地図状態の復元\n")
    
    print("3. 複雑なテーマ設定を含むパーマリンク:")
    print(f"   {SAMPLE_PERMALINKS['complex_theme'][:100]}...")
    print("   - 複数レイヤーの詳細設定")
    print("   - レイヤーごとの透明度")
    print("   - スタイル情報も含む\n")
    
    print("テーマ機能の利点:")
    print("✓ 完全な地図状態の共有")
    print("✓ 複雑なレイヤー設定の瞬時復元")
    print("✓ チーム作業での効率化")
    print("✓ 既存機能との完全互換")

def parse_theme_parameter_example():
    """テーマパラメータの解析例"""
    import urllib.parse
    import json
    
    print("\n=== テーマパラメータ解析例 ===\n")
    
    # サンプルのテーマデータ
    theme_data = {
        "version": "1.0",
        "current_theme": "StandardMap",
        "layer_states": {
            "roads": {
                "name": "Roads",
                "visible": True,
                "opacity": 0.8,
                "current_style": "highway_style"
            },
            "buildings": {
                "name": "Buildings", 
                "visible": False,
                "opacity": 0.6
            }
        },
        "available_themes": ["StandardMap", "DetailedMap", "MinimalMap"]
    }
    
    # JSONをエンコード
    theme_json = json.dumps(theme_data)
    theme_encoded = urllib.parse.quote(theme_json)
    
    print("1. 元のテーマデータ:")
    print(json.dumps(theme_data, indent=2, ensure_ascii=False))
    
    print(f"\n2. エンコード後のthemeパラメータ:")
    print(f"theme={theme_encoded}")
    
    print(f"\n3. 完全なパーマリンクURL:")
    sample_url = f"http://localhost:8089/qgis-map?x=139&y=35&scale=1000.0&theme={theme_encoded}"
    print(sample_url)
    
    # デコード例
    print(f"\n4. デコード処理例:")
    decoded_json = urllib.parse.unquote(theme_encoded)
    decoded_theme = json.loads(decoded_json)
    print("デコード成功:", decoded_theme["current_theme"])

def show_implementation_tips():
    """実装のヒント"""
    print("\n=== 実装のヒント ===\n")
    
    print("1. テーマ情報の取得:")
    print("""
    from qgis.core import QgsProject, QgsMapThemeCollection
    
    project = QgsProject.instance()
    theme_collection = project.mapThemeCollection()
    available_themes = theme_collection.mapThemes()
    """)
    
    print("2. レイヤー状態の取得:")
    print("""
    root = project.layerTreeRoot()
    for child in root.children():
        if isinstance(child, QgsLayerTreeLayer):
            layer = child.layer()
            visible = child.isVisible()
            opacity = layer.opacity()
    """)
    
    print("3. テーマの適用:")
    print("""
    from qgis.core import QgsLayerTreeModel
    
    root = project.layerTreeRoot()
    model = QgsLayerTreeModel(root)
    theme_collection.applyTheme(theme_name, root, model)
    """)

if __name__ == "__main__":
    demonstrate_theme_features()
    parse_theme_parameter_example()
    show_implementation_tips()