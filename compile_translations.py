#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMap Permalink Plugin Translation Compiler

このスクリプトは、QMapPermalinkプラグインの翻訳ファイル(.ts)を
バイナリファイル(.qm)にコンパイルします。
"""

import os
import sys
import subprocess
from pathlib import Path


class TranslationCompiler:
    """翻訳ファイルコンパイラークラス"""
    
    def __init__(self):
        """初期化処理"""
        self.script_dir = Path(__file__).parent
        self.i18n_dir = self.script_dir / "qmap_permalink" / "i18n"
        self.lrelease_exe = Path(r"C:\Qt\linguist_6.9.1\lrelease.exe")
        
    def check_lrelease(self):
        """lrelease.exeの存在確認
        
        Returns:
            bool: lrelease.exeが存在するかどうか
        """
        if not self.lrelease_exe.exists():
            print(f"エラー: lrelease.exe が見つかりません: {self.lrelease_exe}")
            print("Qt Linguistがインストールされているか確認してください。")
            return False
        return True
        
    def find_ts_files(self):
        """翻訳ソースファイル(.ts)を検索
        
        Returns:
            list: .tsファイルのパスリスト
        """
        if not self.i18n_dir.exists():
            print(f"警告: i18nディレクトリが見つかりません: {self.i18n_dir}")
            return []
            
        ts_files = list(self.i18n_dir.glob("*.ts"))
        return sorted(ts_files)
        
    def compile_translation(self, ts_file):
        """単一の翻訳ファイルをコンパイル
        
        Args:
            ts_file (Path): .tsファイルのパス
            
        Returns:
            bool: コンパイル成功かどうか
        """
        qm_file = ts_file.with_suffix('.qm')
        
        try:
            # lreleaseコマンドを実行
            cmd = [str(self.lrelease_exe), str(ts_file), "-qm", str(qm_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                print(f"✓ コンパイル成功: {ts_file.name} -> {qm_file.name}")
                return True
            else:
                print(f"✗ コンパイル失敗: {ts_file.name}")
                if result.stderr:
                    print(f"  エラー: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ コンパイル中に例外が発生: {ts_file.name}")
            print(f"  例外: {e}")
            return False
            
    def compile_all(self):
        """全ての翻訳ファイルをコンパイル
        
        Returns:
            bool: 全てのコンパイルが成功したかどうか
        """
        print("=== QMap Permalink 翻訳ファイル コンパイル ===")
        
        # lrelease.exeの確認
        if not self.check_lrelease():
            return False
            
        # .tsファイルを検索
        ts_files = self.find_ts_files()
        if not ts_files:
            print("コンパイルする.tsファイルが見つかりませんでした。")
            return False
            
        print(f"見つかった翻訳ファイル数: {len(ts_files)}")
        print(f"i18nディレクトリ: {self.i18n_dir}")
        print()
        
        # 各ファイルをコンパイル
        success_count = 0
        for ts_file in ts_files:
            if self.compile_translation(ts_file):
                success_count += 1
                
        print()
        print(f"=== コンパイル結果 ===")
        print(f"成功: {success_count}/{len(ts_files)}")
        
        if success_count == len(ts_files):
            print("全ての翻訳ファイルのコンパイルが完了しました！")
            return True
        else:
            print("一部の翻訳ファイルでコンパイルエラーが発生しました。")
            return False


def main():
    """メイン実行関数"""
    compiler = TranslationCompiler()
    success = compiler.compile_all()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()