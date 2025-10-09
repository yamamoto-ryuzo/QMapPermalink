#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QGISのテーマ機能調査用テストスクリプト

このスクリプトは、QGISのレイヤー状態やテーマ機能について調査するためのものです。
QMapPermalinkプラグインにテーマ機能を追加するための準備として使用します。
"""

from qgis.core import (
    QgsProject,
    QgsMapThemeCollection,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsLayerTreeUtils,
    QgsLayerTreeModel
)
from qgis.gui import QgsLayerTreeView

# QGISのテーマ機能について調査するための関数群

def get_current_layer_states():
    """現在のレイヤー状態を取得
    
    Returns:
        dict: レイヤー状態情報を含む辞書
    """
    project = QgsProject.instance()
    root = project.layerTreeRoot()
    
    layer_states = {}
    
    def collect_layer_info(node):
        """レイヤーノードから情報を収集"""
        if isinstance(node, QgsLayerTreeLayer):
            layer = node.layer()
            if layer:
                layer_states[layer.id()] = {
                    'name': layer.name(),
                    'visible': node.isVisible(),
                    'expanded': node.isExpanded(),
                    'layer_type': layer.type().name,
                    'opacity': layer.opacity() if hasattr(layer, 'opacity') else 1.0,
                }
        elif isinstance(node, QgsLayerTreeGroup):
            layer_states[node.name()] = {
                'type': 'group',
                'visible': node.isVisible(),
                'expanded': node.isExpanded(),
                'children': []
            }
            for child in node.children():
                collect_layer_info(child)
    
    for child in root.children():
        collect_layer_info(child)
    
    return layer_states

def get_map_themes():
    """利用可能なマップテーマ一覧を取得
    
    Returns:
        list: テーマ名のリスト
    """
    project = QgsProject.instance()
    theme_collection = project.mapThemeCollection()
    return theme_collection.mapThemes()

def get_current_theme():
    """現在のテーマ名を取得（存在する場合）
    
    Returns:
        str or None: 現在のテーマ名
    """
    # 現在適用されているテーマを直接取得する方法は限定的
    # 通常は、現在のレイヤー状態とテーマを比較して判定する
    project = QgsProject.instance()
    theme_collection = project.mapThemeCollection()
    
    current_layer_states = get_current_layer_states()
    
    for theme_name in theme_collection.mapThemes():
        # テーマの状態と現在の状態を比較
        # 実際の比較ロジックは複雑になるため、ここでは簡略化
        pass
    
    return None  # 簡略化のため常にNoneを返す

def apply_theme(theme_name):
    """指定されたテーマを適用
    
    Args:
        theme_name (str): 適用するテーマ名
        
    Returns:
        bool: 適用成功かどうか
    """
    try:
        project = QgsProject.instance()
        theme_collection = project.mapThemeCollection()
        
        if theme_name not in theme_collection.mapThemes():
            return False
            
        # テーマを適用
        root = project.layerTreeRoot()
        model = QgsLayerTreeModel(root)
        theme_collection.applyTheme(theme_name, root, model)
        
        return True
    except Exception as e:
        print(f"テーマ適用エラー: {e}")
        return False

def create_theme_from_current_state(theme_name):
    """現在の状態から新しいテーマを作成
    
    Args:
        theme_name (str): 作成するテーマ名
        
    Returns:
        bool: 作成成功かどうか
    """
    try:
        project = QgsProject.instance()
        theme_collection = project.mapThemeCollection()
        
        # 現在の状態を記録してテーマとして保存
        root = project.layerTreeRoot()
        record = QgsMapThemeCollection.createThemeFromCurrentState(root, QgsLayerTreeModel(root))
        theme_collection.insert(theme_name, record)
        
        return True
    except Exception as e:
        print(f"テーマ作成エラー: {e}")
        return False

def get_layer_visibility_info():
    """レイヤーの表示状態詳細情報を取得
    
    Returns:
        dict: レイヤーの詳細表示情報
    """
    project = QgsProject.instance()
    layers = project.mapLayers()
    
    visibility_info = {}
    
    for layer_id, layer in layers.items():
        # レイヤーツリーからの表示状態
        tree_layer = project.layerTreeRoot().findLayer(layer_id)
        
        visibility_info[layer_id] = {
            'name': layer.name(),
            'visible_in_legend': tree_layer.isVisible() if tree_layer else True,
            'opacity': getattr(layer, 'opacity', lambda: 1.0)(),
            'scale_based_visibility': getattr(layer, 'hasScaleBasedVisibility', lambda: False)(),
            'min_scale': getattr(layer, 'minimumScale', lambda: 0)(),
            'max_scale': getattr(layer, 'maximumScale', lambda: 0)(),
        }
        
        # ラスターレイヤーの場合の追加情報
        if hasattr(layer, 'renderer'):
            visibility_info[layer_id]['renderer_type'] = type(layer.renderer()).__name__
            
        # ベクターレイヤーの場合の追加情報
        if hasattr(layer, 'featureCount'):
            visibility_info[layer_id]['feature_count'] = layer.featureCount()
    
    return visibility_info

# テスト実行関数
def test_theme_functionality():
    """テーマ機能のテスト実行"""
    print("=== QGISテーマ機能テスト ===")
    
    # 現在のレイヤー状態を取得
    print("\n1. 現在のレイヤー状態:")
    layer_states = get_current_layer_states()
    for layer_id, state in layer_states.items():
        print(f"  {layer_id}: {state}")
    
    # 利用可能なテーマ一覧
    print("\n2. 利用可能なテーマ:")
    themes = get_map_themes()
    for theme in themes:
        print(f"  - {theme}")
    
    # レイヤー表示詳細情報
    print("\n3. レイヤー表示詳細:")
    visibility_info = get_layer_visibility_info()
    for layer_id, info in visibility_info.items():
        print(f"  {info['name']}: visible={info['visible_in_legend']}, opacity={info['opacity']}")

if __name__ == "__main__":
    # QGISアプリケーション内で実行される場合のテスト
    try:
        test_theme_functionality()
    except Exception as e:
        print(f"テスト実行エラー: {e}")