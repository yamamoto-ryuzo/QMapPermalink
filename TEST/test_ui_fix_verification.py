#!/usr/bin/env python3
"""
UI修正の検証テスト
generate_permalinkメソッドが正しくWMS形式を生成するか確認
"""

import sys
import os
import re

def verify_generate_permalink_fix():
    """generate_permalinkメソッドの修正を検証"""
    
    print("🔍 UI修正検証テスト")
    print("="*50)
    
    # メインプラグインファイルを読み込み
    plugin_file = os.path.join(os.path.dirname(__file__), '..', 'qmap_permalink', 'qmap_permalink.py')
    
    try:
        with open(plugin_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ ファイル読み込みエラー: {e}")
        return False
    
    print(f"📁 検証ファイル: {plugin_file}")
    
    # generate_permalinkメソッドを抽出
    method_pattern = r'def generate_permalink\(self.*?\n(.*?)(?=\n    def|\nclass|\Z)'
    match = re.search(method_pattern, content, re.DOTALL)
    
    if not match:
        print("❌ generate_permalinkメソッドが見つかりません")
        return False
    
    method_content = match.group(1)
    print("✅ generate_permalinkメソッドを発見")
    
    # 重要な修正点を確認
    checks = [
        {
            'name': 'WMSエンドポイント',
            'pattern': r'/wms\?',
            'description': '新しいWMSエンドポイントを使用'
        },
        {
            'name': 'width/heightパラメータ',
            'pattern': r'width=.*height=',
            'description': 'キャンバスサイズパラメータの追加'
        },
        {
            'name': '古いエンドポイント除去',
            'pattern': r'/qgis-map\?',
            'description': '古いエンドポイントが残っていないか',
            'should_not_exist': True
        }
    ]
    
    print(f"\n📋 修正内容の検証:")
    all_passed = True
    
    for check in checks:
        found = re.search(check['pattern'], method_content)
        should_not_exist = check.get('should_not_exist', False)
        
        if should_not_exist:
            if found:
                print(f"   ❌ {check['name']}: {check['description']} (まだ存在)")
                all_passed = False
            else:
                print(f"   ✅ {check['name']}: {check['description']} (正常に除去)")
        else:
            if found:
                print(f"   ✅ {check['name']}: {check['description']} (確認)")
            else:
                print(f"   ❌ {check['name']}: {check['description']} (見つからない)")
                all_passed = False
    
    # navigate_to_permalinkメソッドも確認
    nav_pattern = r'def navigate_to_permalink\(self.*?\n(.*?)(?=\n    def|\nclass|\Z)'
    nav_match = re.search(nav_pattern, content, re.DOTALL)
    
    if nav_match:
        nav_content = nav_match.group(1)
        wms_support = re.search(r'/wms.*?in.*?permalink_url', nav_content)
        if wms_support:
            print(f"   ✅ ナビゲーション: WMS形式のURL対応 (確認)")
        else:
            print(f"   ⚠️ ナビゲーション: WMS形式のURL対応 (要確認)")
    
    print(f"\n📊 総合結果:")
    if all_passed:
        print("   ✅ すべての修正が適用されています")
        print("   🎯 UIは新しいWMS形式のパーマリンクを生成します")
    else:
        print("   ❌ 一部の修正が不完全です")
    
    return all_passed

def show_expected_behavior():
    """期待される動作を表示"""
    print(f"\n🎯 期待される動作")
    print("="*40)
    
    print("1️⃣ プラグイン更新後:")
    print("   📌 QGISでプラグインを無効化/有効化、またはQGIS再起動")
    print("   📌 新しいバージョン1.10.21が読み込まれる")
    
    print("\n2️⃣ パーマリンク生成時:")
    print("   📌 Generate Permalinkボタンをクリック")
    print("   📌 生成されるURL形式:")
    print("      ✅ 新: http://localhost:8089/wms?x=...&y=...&scale=...&width=...&height=...")
    print("      ❌ 旧: http://localhost:8089/qgis-map?x=...&y=...&scale=...")
    
    print("\n3️⃣ ブラウザでの表示:")
    print("   📌 新しいパーマリンクURLを開くと直接PNG画像が表示される")
    print("   📌 HTMLページではなく、画像そのものが表示される")

def provide_troubleshooting():
    """トラブルシューティング情報"""
    print(f"\n🔧 トラブルシューティング")
    print("="*40)
    
    print("❗ まだ古い形式が生成される場合:")
    print("   1️⃣ QGISを完全に終了")
    print("   2️⃣ 古いプラグインファイルを手動削除:")
    print("      📁 %APPDATA%\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\qmap_permalink")
    print("   3️⃣ 新しいZIPファイルを手動インストール:")
    print("      📦 dist/qmap_permalink_1.10.21.zip")
    print("   4️⃣ QGISを再起動してプラグインを有効化")
    
    print("\n❗ プラグインキャッシュをクリア:")
    print("   📌 プラグイン → 開発 → プラグインリローダー（あれば）")
    print("   📌 またはPythonコンソールで:")
    print("      import sys")
    print("      if 'qmap_permalink' in sys.modules:")
    print("          del sys.modules['qmap_permalink']")

if __name__ == "__main__":
    print("🚀 UI修正検証テスト開始")
    
    try:
        # 修正の検証
        success = verify_generate_permalink_fix()
        
        # 期待される動作の表示
        show_expected_behavior()
        
        # トラブルシューティング情報
        provide_troubleshooting()
        
        print(f"\n📋 まとめ:")
        if success:
            print("✅ コード修正完了 - プラグインを更新してテストしてください")
        else:
            print("⚠️ 修正に問題があります - コードを再確認してください")
            
        print(f"📦 最新バージョン: 1.10.21")
        print(f"📁 インストールファイル: dist/qmap_permalink_1.10.21.zip")
        
    except KeyboardInterrupt:
        print("\n⏹️ テスト中断")
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()