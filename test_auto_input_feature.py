# -*- coding: utf-8 -*-
"""
QMapPermalink 自動入力機能のテストスクリプト

このスクリプトは、パーマリンク生成時にナビゲート欄への自動入力機能をテストします。
"""

import sys
import os

# プラグインのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'qmap_permalink'))

def test_auto_input_functionality():
    """自動入力機能のテスト"""
    print("QMapPermalink 自動入力機能テスト")
    print("=" * 50)
    
    # コードの修正内容を確認
    qmap_permalink_path = os.path.join(os.path.dirname(__file__), 'qmap_permalink', 'qmap_permalink.py')
    
    if not os.path.exists(qmap_permalink_path):
        print("❌ エラー: qmap_permalink.py が見つかりません")
        return False
    
    # ファイル内容を読み取って修正が適用されているか確認
    with open(qmap_permalink_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 自動入力のコードが含まれているかチェック
    expected_code = "self.panel.lineEdit_navigate.setText(permalink)"
    
    if expected_code in content:
        print("✅ 自動入力コードが正しく追加されています")
        
        # on_generate_clicked_panel メソッド内に含まれているかより詳細にチェック
        lines = content.split('\n')
        in_method = False
        auto_input_found = False
        
        for i, line in enumerate(lines):
            if 'def on_generate_clicked_panel(self):' in line:
                in_method = True
                continue
            
            if in_method and line.strip().startswith('def ') and 'on_generate_clicked_panel' not in line:
                # 次のメソッドに到達したら終了
                break
                
            if in_method and expected_code in line:
                auto_input_found = True
                print(f"✅ 自動入力コードがon_generate_clicked_panelメソッド内の{i+1}行目に見つかりました")
                print(f"   コード: {line.strip()}")
                break
        
        if auto_input_found:
            print("✅ 実装が正しく配置されています")
            
            # 実装の位置もチェック
            permalink_set_line = -1
            navigate_set_line = -1
            
            for i, line in enumerate(lines):
                if 'self.panel.lineEdit_permalink.setText(permalink)' in line:
                    permalink_set_line = i
                elif 'self.panel.lineEdit_navigate.setText(permalink)' in line:
                    navigate_set_line = i
            
            if permalink_set_line > 0 and navigate_set_line > 0:
                if navigate_set_line > permalink_set_line:
                    print("✅ 自動入力コードがパーマリンク設定の後に正しく配置されています")
                else:
                    print("⚠️  警告: 自動入力コードの配置順序を確認してください")
            
            return True
        else:
            print("❌ エラー: 自動入力コードがon_generate_clicked_panelメソッド内に見つかりません")
            return False
    else:
        print("❌ エラー: 自動入力コードが見つかりません")
        return False

def print_implementation_summary():
    """実装内容の要約を表示"""
    print("\n実装内容の要約:")
    print("-" * 30)
    print("📋 修正されたメソッド: on_generate_clicked_panel()")
    print("📋 追加されたコード: self.panel.lineEdit_navigate.setText(permalink)")
    print("📋 動作: パーマリンク生成時にナビゲート用の入力欄にも同じURLを自動設定")
    print("📋 効果: ユーザーは生成したパーマリンクをすぐにナビゲートに使用可能")

def main():
    """メイン関数"""
    print("QMapPermalink 自動入力機能テスト開始")
    print("現在の日時:", os.popen('date /t & time /t').read().strip() if os.name == 'nt' else os.popen('date').read().strip())
    print()
    
    success = test_auto_input_functionality()
    
    if success:
        print("\n🎉 テスト結果: 成功")
        print("自動入力機能が正しく実装されています。")
    else:
        print("\n❌ テスト結果: 失敗")
        print("実装に問題があります。")
    
    print_implementation_summary()
    
    print("\n使用方法:")
    print("1. QGISでQMapPermalinkプラグインを開く")
    print("2. パネルの「Generate Permalink」ボタンをクリック")
    print("3. 生成されたパーマリンクが「Current Permalink」欄と「Navigate to Location」欄の両方に自動入力される")
    print("4. 必要に応じて「Navigate」ボタンをクリックして移動")

if __name__ == "__main__":
    main()