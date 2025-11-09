#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMap Permalink Plugin ZIP Distribution Creator

このスクリプトは、QMapPermalinkプラグインの配布用ZIPファイルを作成します。
- metadata.txtからバージョン情報を読み取り
- バージョンを+0.0.1して更新
- 必要最小限のファイルのみをZIPに含める
- 前のバージョンのZIPをごみ箱に移動
"""

import os
import sys
import zipfile
import configparser
import re
import shutil
from pathlib import Path
from datetime import datetime


class QMapPermalinkZipCreator:
    """QMapPermalinkプラグインのZIP配布ファイル作成クラス"""
    
    def __init__(self):
        """初期化処理"""
        self.script_dir = Path(__file__).parent
        self.plugin_dir = self.script_dir / "qmap_permalink"
        self.metadata_file = self.plugin_dir / "metadata.txt"
        self.dist_dir = self.script_dir / "dist"
        
        # 配布に含めるファイル/ディレクトリのリスト
        self.include_files = [
            "__init__.py",
            "qmap_permalink.py", 
            "qmap_permalink_server_manager.py",  # 新しく分離したHTTPサーバーマネージャー
            "qmap_wms_service.py",  # WMSサービスクラス（新規追加）
            "professional_wms_server.py",  # 本格的WMSサーバー
            "qmap_permalink_panel.py",
            "qmap_permalink_panel_base.ui",
            "qmap_maplibre_generator.py",
            "qmap_permalink_panel_simple.py",
            "qmap_permalink_dialog.py",  # ダイアログファイル
            "qmap_permalink_dialog_base.ui",  # ダイアログUIファイル
            "qmap_webmap_generator.py",  # WebMap生成器
            "http_server.py",  # 共通HTTPユーティリティ（新規追加）
            "metadata.txt",
            "icon.png",
            "LICENSE",
            "i18n/"  # ディレクトリ全体
        ]

        # 最低限必須とみなすファイル（存在しない場合は警告／失敗の対象）
        self.required_files = [
            "__init__.py",
            "qmap_permalink.py",
            "metadata.txt",
        ]
        
        # 配布から除外するファイル/パターン
        self.exclude_patterns = [
            "__pycache__",
            "*.pyc",
            "*.pyo", 
            "*_original.py",  # バックアップファイル
            "*_http_server.py",  # 古いHTTPサーバーファイル
            "icon_org.png",  # オリジナルアイコン
            ".DS_Store",
            "Thumbs.db",
            "*.tmp"
        ]
        
    def read_metadata(self):
        """metadata.txtから現在のバージョン情報を読み取り
        
        Returns:
            tuple: (current_version, config_parser)
        """
        if not self.metadata_file.exists():
            raise FileNotFoundError(f"metadata.txt が見つかりません: {self.metadata_file}")

        # Preserve original case of option names (ConfigParser lowercases by default)
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(self.metadata_file, encoding='utf-8')

        if 'general' not in config:
            raise ValueError("metadata.txtに[general]セクションが見つかりません")
            
        current_version = config['general'].get('version', '1.0.0')
        return current_version, config
        
    def increment_version(self, version_str):
        """バージョン文字列を+0.0.1する
        
        Args:
            version_str (str): 現在のバージョン文字列 (例: "1.2.3")
            
        Returns:
            str: インクリメントされたバージョン文字列 (例: "1.2.4")
        """
        # VA.B.C形式のバージョンパターンをマッチ
        version_pattern = r'^V?(\d+)\.(\d+)\.(\d+)$'
        match = re.match(version_pattern, version_str)
        
        if not match:
            # フォールバック: 単純な数値分割を試行
            try:
                parts = version_str.replace('V', '').split('.')
                if len(parts) == 3:
                    major, minor, patch = map(int, parts)
                else:
                    raise ValueError
            except ValueError:
                raise ValueError(f"無効なバージョン形式: {version_str}")
        else:
            major, minor, patch = map(int, match.groups())
            
        # パッチバージョンをインクリメント
        new_patch = patch + 1
        new_version = f"{major}.{minor}.{new_patch}"
        
        return new_version
        
    def update_metadata(self, new_version, config):
        """metadata.txtのバージョンを更新
        
        Args:
            new_version (str): 新しいバージョン文字列
            config: ConfigParserオブジェクト
        """
        config['general']['version'] = new_version
        
        # ファイルに書き戻し
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            config.write(f)
            
        print(f"metadata.txtのバージョンを {new_version} に更新しました")
        
    def cleanup_old_zips(self, current_version):
        """古いバージョンのZIPファイルをバックアップフォルダに移動
        
        Args:
            current_version (str): 現在のバージョン
        """
        if not self.dist_dir.exists():
            return

        zip_pattern = "qmap_permalink_*.zip"
        old_zips = list(self.dist_dir.glob(zip_pattern))

        if not old_zips:
            return

        # try send2trash first (cross-platform)
        try:
            from send2trash import send2trash
        except Exception:
            send2trash = None

        for zip_file in old_zips:
            try:
                moved = False
                if send2trash is not None:
                    try:
                        send2trash(str(zip_file))
                        print(f"古いZIPファイルをごみ箱に移動: {zip_file.name} (send2trash)")
                        moved = True
                    except Exception as e:
                        print(f"send2trash でごみ箱移動に失敗: {zip_file.name}: {e}")

                # If not moved and on Windows, try SHFileOperationW
                if not moved and os.name == 'nt':
                    try:
                        import ctypes
                        from ctypes import wintypes

                        class SHFILEOPSTRUCTW(ctypes.Structure):
                            _fields_ = [
                                ('hwnd', wintypes.HWND),
                                ('wFunc', wintypes.UINT),
                                ('pFrom', wintypes.LPCWSTR),
                                ('pTo', wintypes.LPCWSTR),
                                ('fFlags', ctypes.c_uint16),
                                ('fAnyOperationsAborted', wintypes.BOOL),
                                ('hNameMappings', wintypes.LPVOID),
                                ('lpszProgressTitle', wintypes.LPCWSTR),
                            ]

                        FO_DELETE = 3
                        FOF_ALLOWUNDO = 0x0040
                        FOF_NOCONFIRMATION = 0x0010

                        shell32 = ctypes.windll.shell32

                        path_w = str(zip_file) + '\x00\x00'
                        op = SHFILEOPSTRUCTW()
                        op.hwnd = None
                        op.wFunc = FO_DELETE
                        op.pFrom = path_w
                        op.pTo = None
                        op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION
                        res = shell32.SHFileOperationW(ctypes.byref(op))
                        if res == 0:
                            print(f"古いZIPファイルをごみ箱に移動: {zip_file.name} (SHFileOperationW)")
                            moved = True
                        else:
                            print(f"SHFileOperationW が失敗しました: {zip_file.name} (戻り値 {res})")
                    except Exception as e:
                        print(f"Windows ごみ箱移動エラー {zip_file.name}: {e}")

                # 最終手段: 削除（注意：恒久的に削除されます）
                if not moved:
                    try:
                        os.remove(str(zip_file))
                        print(f"古いZIPファイルを削除しました（ごみ箱へ移動不可だったため）: {zip_file.name}")
                    except Exception as e:
                        print(f"ファイル削除に失敗しました: {zip_file.name}: {e}")
            except Exception as e:
                print(f"ファイル移動/ごみ箱移動エラー {zip_file.name}: {e}")
                
    def should_exclude(self, file_path):
        """ファイルが除外対象かどうかをチェック
        
        Args:
            file_path (Path): チェック対象のファイルパス
            
        Returns:
            bool: 除外対象の場合True
        """
        import fnmatch
        
        file_name = file_path.name
        file_str = str(file_path)
        # Exclude any file that is inside a __pycache__ directory explicitly
        if '__pycache__' in file_path.parts:
            return True

        # Exclude any file that is inside a .cache directory (e.g. generated tile cache)
        if '.cache' in file_path.parts:
            return True

        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(file_name, pattern) or fnmatch.fnmatch(file_str, pattern):
                return True
        return False

    def create_zip(self, version):
        """配布用ZIPファイルを作成
        
        Args:
            version (str): バージョン文字列
        """
        # distディレクトリを作成
        self.dist_dir.mkdir(exist_ok=True)
        
        # ZIPファイル名
        zip_filename = f"qmap_permalink_{version}.zip"
        zip_path = self.dist_dir / zip_filename
        
        print(f"ZIPファイルを作成中: {zip_filename}")

        # Include everything under the plugin directory except excluded patterns.
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.plugin_dir.rglob('*'):
                if not file_path.is_file():
                    continue
                if self.should_exclude(file_path):
                    rel_path = file_path.relative_to(self.plugin_dir)
                    print(f"  除外: {rel_path}")
                    continue
                rel_path = file_path.relative_to(self.plugin_dir)
                arcname = f"qmap_permalink/{rel_path}"
                zipf.write(file_path, arcname)
                print(f"  追加: {rel_path}")
                    
        print(f"ZIPファイルを作成しました: {zip_path}")
        return zip_path
        
    def validate_files(self):
        """必要なファイルがすべて存在するかを検証"""
        missing_files = []
        
        for item in self.include_files:
            item_path = self.plugin_dir / item
            if not item_path.exists():
                missing_files.append(item)
        
        if missing_files:
            print("警告: 以下のファイルが見つかりません:")
            for file in missing_files:
                print(f"  - {file}")
            
        return len(missing_files) == 0

    def create_distribution(self):
        """配布パッケージ作成のメイン処理"""
        try:
            print("=== QMap Permalink 配布用ZIP作成 ===")
            print(f"作業ディレクトリ: {self.script_dir}")
            print(f"プラグインディレクトリ: {self.plugin_dir}")
            
            # ファイル存在チェック
            print("\n--- ファイル存在チェック ---")
            if not self.validate_files():
                print("いくつかのファイルが見つかりませんが、続行します...")
            
            # 現在のバージョンを読み取り
            current_version, config = self.read_metadata()
            print(f"現在のバージョン: {current_version}")

            # バージョンの決定: インクリメントまたは外部指定
            new_version = self.increment_version(current_version)
            print(f"新しいバージョン: {new_version}")
            
            # 古いZIPファイルをクリーンアップ
            self.cleanup_old_zips(current_version)
            
            # metadata.txtを更新
            self.update_metadata(new_version, config)
            
            # ZIPファイルを作成
            zip_path = self.create_zip(new_version)
            
            print("\n=== 作成完了 ===")
            print(f"配布用ZIPファイル: {zip_path}")
            print(f"ファイルサイズ: {zip_path.stat().st_size / 1024:.1f} KB")
            
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            sys.exit(1)


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description='Create distribution ZIP for QMapPermalink')
    parser.add_argument('--set-version', help='Set the version explicitly (do not increment)')
    parser.add_argument('--no-increment', action='store_true', help='Do not auto-increment the version')
    args = parser.parse_args()

    creator = QMapPermalinkZipCreator()

    # Read current metadata
    current_version, config = creator.read_metadata()

    # Determine version to use
    if args.set_version:
        target_version = args.set_version
    elif args.no_increment:
        target_version = current_version
    else:
        target_version = creator.increment_version(current_version)

    try:
        print(f"Using version: {target_version}")

        # cleanup old zip files from previous runs (restore old behavior)
        try:
            creator.cleanup_old_zips(current_version)
        except Exception as _:
            # non-fatal: continue even if cleanup fails
            pass

        zip_path = creator.create_zip(target_version)

        # Update metadata only after successful ZIP creation
        if target_version != current_version:
            try:
                creator.update_metadata(target_version, config)
            except Exception as e:
                print(f"metadata.txt の更新に失敗しました: {e}")

        print('\n=== 作成完了 ===')
        print(f"配布用ZIPファイル: {zip_path}")
        print(f"ファイルサイズ: {zip_path.stat().st_size / 1024:.1f} KB")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()