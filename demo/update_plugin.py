#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMapPermalinkプラグインの更新確認・修正スクリプト

現在のプラグインファイルの状態を確認し、必要に応じて更新します。
"""

import os
import shutil
import sys
from pathlib import Path
import filecmp

def find_qgis_plugin_path():
    """QGISプラグインのインストールパスを探す"""
    possible_paths = [
        Path.home() / "AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/qmap_permalink",
        Path.home() / ".local/share/QGIS/QGIS3/profiles/default/python/plugins/qmap_permalink",
        Path.home() / ".qgis2/python/plugins/qmap_permalink",
        # 追加の可能性のあるパス
        Path("C:/Program Files/QGIS 3.28/apps/qgis/python/plugins/qmap_permalink"),
        Path("C:/Program Files/QGIS 3.30/apps/qgis/python/plugins/qmap_permalink"),
        Path("C:/Program Files/QGIS 3.32/apps/qgis/python/plugins/qmap_permalink"),
    ]
    
    for path in possible_paths:
        if path.exists() and (path / "__init__.py").exists():
            return path
    
    return None

def check_file_differences(source_dir, target_dir):
    """ソースディレクトリとターゲットディレクトリのファイル差分をチェック"""
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    if not target_path.exists():
        return False, "ターゲットディレクトリが存在しません"
    
    differences = []
    
    # 重要なファイルをチェック
    important_files = [
        "qmap_permalink_http_server.py",
        "qmap_permalink.py",
        "qmap_webmap_generator.py",
        "__init__.py",
        "metadata.txt"
    ]
    
    for file_name in important_files:
        source_file = source_path / file_name
        target_file = target_path / file_name
        
        if not source_file.exists():
            differences.append(f"❌ ソースファイルが存在しません: {file_name}")
            continue
            
        if not target_file.exists():
            differences.append(f"❌ ターゲットファイルが存在しません: {file_name}")
            continue
        
        # ファイルサイズとタイムスタンプを比較
        source_stat = source_file.stat()
        target_stat = target_file.stat()
        
        if source_stat.st_size != target_stat.st_size:
            differences.append(f"📏 サイズ差異: {file_name} (ソース: {source_stat.st_size}, ターゲット: {target_stat.st_size})")
        
        if source_stat.st_mtime > target_stat.st_mtime:
            differences.append(f"🕐 ソースの方が新しい: {file_name}")
        elif target_stat.st_mtime > source_stat.st_mtime:
            differences.append(f"🕐 ターゲットの方が新しい: {file_name}")
    
    return len(differences) == 0, differences

def update_plugin_files(source_dir, target_dir, force=False):
    """プラグインファイルを更新"""
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    if not source_path.exists():
        return False, "ソースディレクトリが存在しません"
    
    if not target_path.exists():
        print(f"ターゲットディレクトリを作成: {target_path}")
        target_path.mkdir(parents=True, exist_ok=True)
    
    updated_files = []
    errors = []
    
    # 更新するファイル一覧
    files_to_update = [
        "qmap_permalink_http_server.py",  # WMS機能が含まれる重要ファイル
        "qmap_permalink.py",
        "qmap_webmap_generator.py",
        "__init__.py",
        "metadata.txt"
    ]
    
    for file_name in files_to_update:
        source_file = source_path / file_name
        target_file = target_path / file_name
        
        if not source_file.exists():
            errors.append(f"ソースファイルが存在しません: {file_name}")
            continue
        
        try:
            # ファイルをコピー（バックアップを作成）
            if target_file.exists():
                backup_file = target_path / f"{file_name}.backup"
                shutil.copy2(target_file, backup_file)
                print(f"📋 バックアップ作成: {backup_file}")
            
            shutil.copy2(source_file, target_file)
            updated_files.append(file_name)
            print(f"✅ 更新完了: {file_name}")
            
        except Exception as e:
            errors.append(f"更新失敗 {file_name}: {str(e)}")
    
    return len(errors) == 0, updated_files, errors

def main():
    """メイン処理"""
    print("🔧 QMapPermalink プラグイン更新ツール")
    print("=" * 50)
    
    # 現在のディレクトリからソースパスを特定
    current_dir = Path.cwd()
    source_plugin_dir = current_dir / "qmap_permalink"
    
    if not source_plugin_dir.exists():
        print("❌ エラー: qmap_permalinkディレクトリが見つかりません")
        print(f"   現在のディレクトリ: {current_dir}")
        print("   このスクリプトはQMapPermalinkプロジェクトのルートで実行してください")
        return 1
    
    print(f"📁 ソースディレクトリ: {source_plugin_dir}")
    
    # QGISプラグインパスを探す
    plugin_path = find_qgis_plugin_path()
    
    if not plugin_path:
        print("❌ QGISプラグインディレクトリが見つかりませんでした")
        print("\n可能性のある場所:")
        print("  - %APPDATA%\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\qmap_permalink")
        print("  - ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/qmap_permalink")
        print("\n手動でパスを指定してください:")
        print(f"  python {sys.argv[0]} <プラグインディレクトリのパス>")
        return 1
    
    print(f"📁 ターゲットディレクトリ: {plugin_path}")
    
    # コマンドライン引数でパスが指定された場合
    if len(sys.argv) > 1:
        plugin_path = Path(sys.argv[1])
        print(f"📁 指定されたターゲットディレクトリ: {plugin_path}")
    
    # ファイルの差分をチェック
    print("\n📊 ファイル差分チェック中...")
    is_same, differences = check_file_differences(source_plugin_dir, plugin_path)
    
    if is_same:
        print("✅ ファイルは最新の状態です")
        return 0
    
    print("⚠️ ファイルに差分が見つかりました:")
    for diff in differences:
        print(f"   {diff}")
    
    # 更新の確認
    print(f"\n❓ プラグインファイルを更新しますか？ (y/N): ", end="")
    
    # 自動実行モードまたはユーザー確認
    if len(sys.argv) > 2 and sys.argv[2] == "--auto":
        confirm = "y"
        print("y (自動実行)")
    else:
        confirm = input().strip().lower()
    
    if confirm != 'y':
        print("❌ 更新をキャンセルしました")
        return 0
    
    # ファイルを更新
    print("\n🔄 ファイルを更新中...")
    success, updated_files, errors = update_plugin_files(source_plugin_dir, plugin_path)
    
    if success:
        print(f"\n✅ 更新完了！ {len(updated_files)} ファイルを更新しました:")
        for file_name in updated_files:
            print(f"   - {file_name}")
        
        print("\n📋 次の手順:")
        print("   1. QGISでQMapPermalinkプラグインを無効化→有効化")
        print("   2. または、QGISを再起動")
        print("   3. demo/diagnose_server.py でWMS機能を確認")
        
        return 0
    else:
        print(f"\n❌ 更新中にエラーが発生しました:")
        for error in errors:
            print(f"   - {error}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)