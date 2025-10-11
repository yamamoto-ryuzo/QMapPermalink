#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QGISプラグインディレクトリパス検出スクリプト
"""

import os
import sys
import platform

def find_qgis_plugin_paths():
    """QGISプラグインディレクトリの可能なパスを検索"""
    username = os.environ.get('USERNAME') or os.environ.get('USER')
    system = platform.system()
    
    possible_paths = []
    
    if system == "Windows":
        base_paths = [
            f"C:\\Users\\{username}\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins",
            f"C:\\Users\\{username}\\AppData\\Local\\QGIS\\QGIS3\\profiles\\default\\python\\plugins",
            f"C:\\Program Files\\QGIS 3.34\\apps\\qgis\\python\\plugins",
            f"C:\\OSGeo4W\\apps\\qgis\\python\\plugins",
            "C:\\Program Files\\QGIS 3.34\\apps\\qgis\\python\\plugins",
            "C:\\Program Files (x86)\\QGIS 3.34\\apps\\qgis\\python\\plugins"
        ]
    elif system == "Darwin":  # macOS
        base_paths = [
            f"/Users/{username}/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins",
            "/Applications/QGIS.app/Contents/MacOS/lib/qgis/python/plugins"
        ]
    else:  # Linux
        base_paths = [
            f"/home/{username}/.local/share/QGIS/QGIS3/profiles/default/python/plugins",
            "/usr/share/qgis/python/plugins"
        ]
    
    existing_paths = []
    for path in base_paths:
        if os.path.exists(path):
            existing_paths.append(path)
            print(f"✅ 存在するパス: {path}")
            
            # QMapPermalinkプラグインがあるかチェック
            qmap_path = os.path.join(path, "qmap_permalink")
            if os.path.exists(qmap_path):
                print(f"   📦 QMapPermalinkプラグイン発見: {qmap_path}")
                
                # metadata.txtからバージョン確認
                metadata_path = os.path.join(qmap_path, "metadata.txt")
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.startswith('version='):
                                    version = line.split('=')[1].strip()
                                    print(f"   📋 現在のバージョン: {version}")
                                    break
                    except Exception as e:
                        print(f"   ❌ metadata.txt読み取りエラー: {e}")
        else:
            print(f"❌ 存在しないパス: {path}")
    
    return existing_paths

if __name__ == "__main__":
    print("🔍 QGISプラグインディレクトリ検索")
    print("=" * 50)
    paths = find_qgis_plugin_paths()
    
    if not paths:
        print("\n❌ QGISプラグインディレクトリが見つかりませんでした")
        print("QGISがインストールされているか確認してください")
    else:
        print(f"\n✅ {len(paths)}個のプラグインディレクトリが見つかりました")