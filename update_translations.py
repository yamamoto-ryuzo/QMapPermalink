#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
geo_webview 翻訳ファイル更新スクリプト

このスクリプトは以下の処理を行います:
1. pylupdate5を使用してPythonソースとUIファイルから翻訳可能な文字列を抽出
2. 10言語（英語、フランス語、ドイツ語、スペイン語、イタリア語、ポルトガル語、日本語、中国語、ロシア語、ヒンディー語）の.tsファイルを生成/更新
3. lreleaseを使用して.tsファイルから.qmファイルをコンパイル
"""

import os
import sys
import subprocess
from pathlib import Path


# 対応言語リスト
LANGUAGES = {
    'en': 'English',
    'fr': 'French',
    'de': 'German',
    'es': 'Spanish',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ja': 'Japanese',
    'zh': 'Chinese',
    'ru': 'Russian',
    'hi': 'Hindi'
}


def find_pylupdate():
    """pylupdate5/pylupdate6/lupdateの実行ファイルを検索"""
    # 優先順位: ユーザー指定 -> lupdate -> pylupdate6 -> pylupdate5 -> pylupdate
    candidates = [
        r'C:\Qt\linguist_6.9.1\lupdate.exe',  # ユーザー指定のパス
        'lupdate',
        'pylupdate6', 
        'pylupdate5', 
        'pylupdate'
    ]
    
    for cmd in candidates:
        try:
            result = subprocess.run([cmd, '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                print(f"{cmd} が見つかりました")
                print(f"  バージョン: {result.stdout.strip()}")
                return cmd
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    return None


def update_ts_files(plugin_dir, i18n_dir):
    """ソースコードから翻訳ファイル(.ts)を更新
    
    Args:
        plugin_dir: プラグインディレクトリ
        i18n_dir: 翻訳ファイルディレクトリ
    """
    pylupdate = find_pylupdate()
    
    if not pylupdate:
        print("エラー: pylupdate5/pylupdate6 が見つかりません")
        print("Qt開発ツールをインストールしてください")
        return False
    
    # 翻訳対象のファイルを収集
    py_files = list(plugin_dir.glob('*.py'))
    ui_files = list(plugin_dir.glob('*.ui'))
    
    print(f"\n翻訳対象ファイル:")
    print(f"  Pythonファイル: {len(py_files)}個")
    print(f"  UIファイル: {len(ui_files)}個")
    
    # 各言語の.tsファイルを生成/更新
    for lang_code, lang_name in LANGUAGES.items():
        ts_file = i18n_dir / f'geo_webview_{lang_code}.ts'
        
        print(f"\n{lang_name} ({lang_code}) の翻訳ファイルを更新中...")
        
        # pylupdateコマンドを構築
        cmd = [pylupdate]
        
        # ソースファイルを追加
        for py_file in py_files:
            cmd.append(str(py_file))
        for ui_file in ui_files:
            cmd.append(str(ui_file))
        
        # 出力ファイルを指定
        cmd.extend(['-ts', str(ts_file)])
        
        try:
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  cwd=str(plugin_dir),
                                  timeout=30)
            
            if result.returncode == 0:
                print(f"  ✓ {ts_file.name} を更新しました")
            else:
                print(f"  ✗ エラー: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"  ✗ タイムアウト")
        except Exception as e:
            print(f"  ✗ エラー: {e}")
    
    return True


def compile_qm_files(i18n_dir, lrelease_path=None):
    """翻訳ファイル(.ts)をコンパイルして.qmファイルを生成
    
    Args:
        i18n_dir: 翻訳ファイルディレクトリ
        lrelease_path: lrelease.exeのパス（Noneの場合は自動検索）
    """
    # lreleaseコマンドを検索
    if lrelease_path and os.path.exists(lrelease_path):
        lrelease = lrelease_path
    else:
        # 標準的な場所を検索
        candidates = [
            'lrelease',
            'lrelease-qt5',
            'lrelease-qt6',
            r'C:\Qt\linguist_6.9.1\lrelease.exe',  # ユーザー指定のパス
        ]
        
        lrelease = None
        for cmd in candidates:
            try:
                result = subprocess.run([cmd, '-version'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode == 0:
                    lrelease = cmd
                    print(f"\n{cmd} が見つかりました")
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
    
    if not lrelease:
        print("\nエラー: lrelease が見つかりません")
        print("Qt Linguist ツールをインストールするか、パスを指定してください")
        return False
    
    # 各.tsファイルをコンパイル
    ts_files = list(i18n_dir.glob('geo_webview_*.ts'))
    
    print(f"\n.qmファイルをコンパイル中...")
    
    for ts_file in ts_files:
        qm_file = ts_file.with_suffix('.qm')
        
        try:
            result = subprocess.run([lrelease, str(ts_file), '-qm', str(qm_file)],
                                  capture_output=True,
                                  text=True,
                                  timeout=30)
            
            if result.returncode == 0:
                print(f"  ✓ {qm_file.name} を生成しました")
            else:
                print(f"  ✗ {ts_file.name} のコンパイルエラー: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"  ✗ {ts_file.name} のコンパイルがタイムアウト")
        except Exception as e:
            print(f"  ✗ {ts_file.name} のコンパイルエラー: {e}")
    
    return True


def main():
    """メイン処理"""
    # スクリプトのディレクトリ
    script_dir = Path(__file__).parent
    
    # プラグインディレクトリ
    plugin_dir = script_dir / 'geo_webview'
    
    # 翻訳ファイルディレクトリ
    i18n_dir = plugin_dir / 'i18n'
    
    # ディレクトリ存在確認
    if not plugin_dir.exists():
        print(f"エラー: プラグインディレクトリが見つかりません: {plugin_dir}")
        sys.exit(1)
    
    # i18nディレクトリを作成（存在しない場合）
    i18n_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("geo_webview 翻訳ファイル更新")
    print("=" * 60)
    
    # .tsファイルを更新
    if not update_ts_files(plugin_dir, i18n_dir):
        print("\n翻訳ファイルの更新に失敗しました")
        sys.exit(1)
    
    # .qmファイルをコンパイル
    lrelease_path = r'C:\Qt\linguist_6.9.1\lrelease.exe'
    if not compile_qm_files(i18n_dir, lrelease_path):
        print("\n.qmファイルのコンパイルに失敗しました")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("翻訳ファイルの更新が完了しました")
    print("=" * 60)
    print(f"\n翻訳ファイル: {i18n_dir}")
    print("\n次のステップ:")
    print("1. Qt Linguist で .ts ファイルを開いて翻訳を追加/編集")
    print("2. 翻訳完了後、このスクリプトを再実行して .qm ファイルを再生成")


if __name__ == '__main__':
    main()
