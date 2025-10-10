#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テストスクリプト: WebMapGeneratorモジュール分離のテスト
QMapWebMapGenerator クラスの機能をテストして、正しくリファクタリングされているか確認する
"""

import sys
import os

# プラグインのパスを追加
plugin_path = os.path.join(os.path.dirname(__file__), 'qmap_permalink')
sys.path.insert(0, plugin_path)

def test_webmap_generator_import():
    """WebMapGeneratorモジュールのインポートテスト"""
    print("📦 WebMapGeneratorモジュールのインポートテスト...")
    
    try:
        from qmap_webmap_generator import QMapWebMapGenerator
        print("✅ QMapWebMapGenerator クラスのインポート成功")
        return True
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        return False

def test_webmap_generator_methods():
    """WebMapGeneratorクラスのメソッド存在確認テスト"""
    print("\n🔍 メソッド存在確認テスト...")
    
    try:
        from qmap_webmap_generator import QMapWebMapGenerator
        
        # モックのifaceオブジェクト
        class MockIface:
            def mapCanvas(self):
                return None
        
        generator = QMapWebMapGenerator(MockIface())
        
        # 必要なメソッドが存在するか確認
        required_methods = [
            'generate_openlayers_map',
            'get_qgis_layers_info', 
            'get_current_extent_info',
            '_resolve_coordinates',
            '_convert_to_wgs84'
        ]
        
        for method_name in required_methods:
            if hasattr(generator, method_name):
                print(f"✅ {method_name} メソッドが存在")
            else:
                print(f"❌ {method_name} メソッドが見つからない")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ メソッドテストエラー: {e}")
        return False

def test_main_plugin_integration():
    """メインプラグインでの統合テスト"""
    print("\n🔗 メインプラグイン統合テスト...")
    
    try:
        from qmap_permalink import QMapPermalink
        
        # プラグインクラスを確認
        plugin_class = QMapPermalink
        
        # WebMapGeneratorのインポートフラグを確認
        try:
            import qmap_permalink
            if hasattr(qmap_permalink, 'WEBMAP_AVAILABLE'):
                print(f"✅ WEBMAP_AVAILABLE フラグ: {qmap_permalink.WEBMAP_AVAILABLE}")
            else:
                print("❌ WEBMAP_AVAILABLE フラグが見つからない")
                return False
        except Exception as e:
            print(f"❌ プラグインモジュール確認エラー: {e}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ メインプラグインインポートエラー: {e}")
        return False

def test_method_removal():
    """古いメソッドが削除されているかテスト"""
    print("\n🗑️ 古いメソッド削除確認テスト...")
    
    try:
        from qmap_permalink import QMapPermalink
        
        # モックのifaceオブジェクト
        class MockIface:
            def mapCanvas(self):
                return None
        
        plugin = QMapPermalink(MockIface())
        
        # 削除されているべきメソッド
        removed_methods = [
            '_generate_openlayers_map',
            '_get_qgis_layers_info',
            '_get_current_extent_info'
        ]
        
        for method_name in removed_methods:
            if hasattr(plugin, method_name):
                print(f"❌ {method_name} メソッドがまだ存在している（削除されていない）")
                return False
            else:
                print(f"✅ {method_name} メソッドが正しく削除されている")
        
        return True
        
    except Exception as e:
        print(f"❌ メソッド削除テストエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("🚀 V1.8.0 WebMapGenerator分離テスト開始\n")
    
    tests = [
        ("WebMapGeneratorインポート", test_webmap_generator_import),
        ("WebMapGeneratorメソッド確認", test_webmap_generator_methods),
        ("メインプラグイン統合", test_main_plugin_integration),
        ("古いメソッド削除確認", test_method_removal)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"{'='*50}")
        print(f"テスト: {test_name}")
        print(f"{'='*50}")
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} - 成功")
        else:
            print(f"❌ {test_name} - 失敗")
        
        print()
    
    print(f"{'='*50}")
    print(f"テスト結果: {passed}/{total} 成功")
    print(f"{'='*50}")
    
    if passed == total:
        print("🎉 すべてのテストが成功しました！")
        print("✅ V1.8.0 WebMapGenerator分離は正常に完了しています")
        return True
    else:
        print("⚠️ 一部のテストが失敗しました")
        print("🔧 修正が必要な箇所があります")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)