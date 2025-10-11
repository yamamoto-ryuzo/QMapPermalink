# 🔧 QMapPermalink WMS機能の有効化手順

現在のQGISプラグインは、WMS機能が実装される前のバージョンを実行しています。
以下の手順でプラグインを更新し、WMS機能を有効化してください。

## 📋 現在の状況確認

診断結果：
- ✅ 基本機能（`/qgis-map`）は動作中
- ❌ WMS機能（`/wms`）は未実装
- ❌ タイル配信（`/tiles`）は未実装
- ❌ PNG直接配信（`/qgis-png`）は未実装

## 🚀 WMS機能有効化手順

### 方法1: プラグインの再読み込み（推奨）

1. **QGISを開く**
2. **プラグインメニューから操作**：
   - `プラグイン` → `プラグインを管理とインストール...`
   - `インストール済み` タブを選択
   - `QMapPermalink` を探す
   - **プラグインを無効化** （チェックを外す）
   - 数秒待つ
   - **プラグインを有効化** （チェックを入れる）

3. **確認**：
   - プラグインパネルが再表示されることを確認
   - HTTPサーバーが再起動されることを確認

### 方法2: QGIS完全再起動

1. **QGISを完全に終了**
2. **QGIS を再起動**
3. **QMapPermalinkプラグインを有効化**
4. **HTTPサーバーの自動起動を確認**

### 方法3: 開発者向けリロード（PyQGIS経験者向け）

QGISのPythonコンソールで以下を実行：

```python
# プラグインのリロード
import importlib
import qmap_permalink
importlib.reload(qmap_permalink)

# または、プラグインマネージャーからリロード
import qgis.utils
qgis.utils.reloadPlugin('qmap_permalink')
```

## ✅ 機能確認方法

### 1. QGISログでサーバー起動を確認

**View → Panels → Log Messages** でQGISのログパネルを開き、以下のメッセージを確認：

```
QMap Permalink HTTPサーバーが起動しました: http://localhost:8089
```

### 2. 新機能の動作確認

#### デモページでテスト
```bash
# ブラウザでデモページを開く
start demo/qgis_wms_demo.html
```

#### コマンドラインでテスト
```bash
# 診断スクリプトで全機能をテスト
python demo/diagnose_server.py

# 簡易テスト
python demo/test_wms_simple.py
```

#### 手動でWMS確認
ブラウザで以下のURLにアクセス：
```
http://localhost:8089/wms?SERVICE=WMS&REQUEST=GetCapabilities
```

### 3. 期待される結果

✅ **成功した場合**：
- WMS GetCapabilities: XMLレスポンス
- WMS GetMap: PNG画像
- タイル配信: 256x256のPNG画像
- 診断スクリプト: 4-5個の機能が成功

❌ **まだ失敗する場合**：
- 404エラーが継続
- "Available: /qgis-map, /qgis-image" メッセージ

## 🚨 トラブルシューティング

### 問題: プラグイン再読み込み後も404エラー

**考えられる原因**：
1. プラグインファイルが正しく更新されていない
2. QGISが古いファイルをキャッシュしている
3. ファイルアクセス権限の問題

**解決策**：
```bash
# 1. プラグインファイルの更新確認
# プラグインのインストール場所を確認
# 通常: C:\Users\{ユーザー名}\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\qmap_permalink\

# 2. 手動でファイルコピー
copy /Y qmap_permalink\qmap_permalink_http_server.py "%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\qmap_permalink\"

# 3. QGIS完全再起動
```

### 問題: サーバーが起動しない

**症状**：ログに起動メッセージが表示されない

**解決策**：
1. ポート8089が使用されていないか確認：
   ```bash
   netstat -an | findstr :8089
   ```
2. 他のアプリケーションがポートを使用している場合は、そのアプリケーションを終了
3. QGISを管理者権限で実行

### 問題: 一部の機能のみ動作

**症状**：既存機能は動作するが、WMS機能のみ失敗

**考えられる原因**：コードの一部のみが更新された

**解決策**：
1. 全プラグインファイルを確認：
   ```bash
   dir qmap_permalink\*.py
   ```
2. 特に `qmap_permalink_http_server.py` の更新日時を確認
3. 必要に応じて手動でファイルをコピー

## 📞 サポート

問題が解決しない場合は、以下の情報と合わせてお知らせください：

1. **診断結果**：
   ```bash
   python demo/diagnose_server.py > diagnosis_result.txt
   ```

2. **QGISログ**：
   - View → Panels → Log Messages の内容

3. **環境情報**：
   - QGISバージョン
   - Windowsバージョン
   - プラグインファイルの更新日時

---

🎯 **これらの手順により、QGISでフルWMS配信機能が利用できるようになります！**