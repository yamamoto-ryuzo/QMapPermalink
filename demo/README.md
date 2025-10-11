# 🧪 QMapPermalink WMS配信機能 デモンストレーション

このフォルダには、QMapPermalinkプラグインのWMS（Web Map Service）配信機能のデモンストレーションファイルが含まれています。

## 📁 ファイル構成

### 🌐 デモページ

#### **基本機能デモ**（現在利用可能）
- **`qgis_basic_demo.html`** - 既存パーマリンク機能のデモページ
  - `/qgis-map`, `/qgis-image` エンドポイントのテスト
  - サーバー状態の確認
  - 基本機能の動作確認

#### **WMS機能デモ**（要プラグイン更新）
- **`qgis_wms_demo.html`** - WMS配信機能のインタラクティブデモページ
  - WMS 1.3.0標準機能の動作確認
  - OpenLayersを使った地図表示
  - 各WMSエンドポイントのテスト機能

### 🧪 テストスクリプト

#### **基本機能テスト**
- **`test_basic_functionality.py`** - 既存機能の自動テストスクリプト

#### **WMS機能テスト**（要プラグイン更新）
- **`test_wms_simple.py`** - 標準ライブラリのみを使用した軽量テストスクリプト
- **`test_wms_functionality.py`** - requestsライブラリを使用した高機能テストスクリプト

### 📚 参考資料
- **`WMS_ENHANCEMENT_README.md`** - WMS機能の詳細説明とセットアップガイド
- **`wms_like_service_enhancement.py`** - WMS機能の独立クラス実装（参考用）

## 🚀 使用方法

### 1. 前提条件
1. QGISが起動していること
2. QMapPermalinkプラグインが有効化されていること
3. HTTPサーバーが起動していること（通常はポート8089）

### 2. デモページの使用

#### **基本機能デモ**（現在利用可能）
```bash
# 既存のパーマリンク機能をテスト
start demo/qgis_basic_demo.html
```

#### **WMS機能デモ**（要プラグイン更新）
```bash
# WMS配信機能をテスト（QGISの再起動が必要）
start demo/qgis_wms_demo.html
```

### ⚠️ **重要：WMS機能について**
WMS機能を利用するには、以下の手順が必要です：
1. **QGISを完全に終了**
2. **QGISを再起動**
3. **QMapPermalinkプラグインを有効化**
4. **HTTPサーバーを起動**

現在は既存のパーマリンク機能（`/qgis-map`, `/qgis-image`）のみが利用可能です。

### 3. テストスクリプトの実行

#### **基本機能テスト**（現在利用可能）
```bash
# 既存パーマリンク機能のテスト
python demo/test_basic_functionality.py
```

#### **WMS機能テスト**（要プラグイン更新）
```bash
# 標準ライブラリ版（推奨）
python demo/test_wms_simple.py

# requests版（requestsライブラリが必要）
python demo/test_wms_functionality.py
```

## 🌐 利用可能なエンドポイント

### WMS 1.3.0 標準エンドポイント
```
# GetCapabilities - サービス情報取得
http://localhost:8089/wms?SERVICE=WMS&REQUEST=GetCapabilities

# GetMap - 地図画像取得
http://localhost:8089/wms?SERVICE=WMS&REQUEST=GetMap&BBOX=139.5,35.5,139.9,35.9&WIDTH=400&HEIGHT=400&CRS=EPSG:4326&FORMAT=image/png

# GetFeatureInfo - 地物情報取得
http://localhost:8089/wms?SERVICE=WMS&REQUEST=GetFeatureInfo&I=200&J=200&INFO_FORMAT=application/json
```

### タイル配信エンドポイント
```
# XYZ Tiles
http://localhost:8089/tiles/{z}/{x}/{y}.png

# 例：ズームレベル10のタイル
http://localhost:8089/tiles/10/904/403.png
```

### 既存エンドポイント（継続利用可能）
```
# インタラクティブ地図
http://localhost:8089/qgis-map?lat=35.681&lon=139.767&scale=25000

# PNG画像直接配信
http://localhost:8089/qgis-png?lat=35.681&lon=139.767&scale=25000&width=800&height=600
```

## 🔧 トラブルシューティング

### デモページが動作しない場合
1. QGISでQMapPermalinkプラグインが起動していることを確認
2. HTTPサーバーが起動していることを確認（QGISのメッセージログを確認）
3. ブラウザのコンソールでエラーメッセージを確認

### テストスクリプトが失敗する場合
1. サーバーが起動しているか確認
   ```bash
   netstat -an | findstr :8089
   ```
2. プラグインが最新バージョンに更新されているか確認
3. QGISを再起動してプラグインを再読み込み

### WMS機能が認識されない場合
- QGISでプラグインを無効化→有効化
- または、QGISを完全に再起動

## 📊 デモンストレーション内容

### 1. WMS標準機能テスト
- GetCapabilities XMLの生成と表示
- GetMapでの地図画像生成
- GetFeatureInfoでの地物情報取得

### 2. タイル配信テスト
- XYZ形式タイルの生成
- 各ズームレベルでの動作確認

### 3. OpenLayersとの統合
- WMSレイヤーとしての表示
- インタラクティブなマップ操作
- GetFeatureInfoの動的実行

### 4. パフォーマンステスト
- 複数同時リクエストの処理
- 画像生成速度の測定
- エラーハンドリングの確認

## 🌟 応用例

### QGISクライアントでの利用
1. QGIS で「レイヤー」→「レイヤーを追加」→「WMSレイヤーを追加...」
2. 新しい接続を作成：
   - **名前**: QGIS Permalink WMS
   - **URL**: `http://localhost:8089/wms`
3. 接続してレイヤーを追加

### Web地図での利用
```javascript
// Leafletでのタイル表示
const qgisTileLayer = L.tileLayer('http://localhost:8089/tiles/{z}/{x}/{y}.png', {
    attribution: 'QGIS Permalink',
    maxZoom: 18
});

// OpenLayersでのWMS表示
const wmsLayer = new ol.layer.Image({
    source: new ol.source.ImageWMS({
        url: 'http://localhost:8089/wms',
        params: {
            'SERVICE': 'WMS',
            'REQUEST': 'GetMap',
            'LAYERS': 'QGIS_Map',
            'FORMAT': 'image/png'
        }
    })
});
```

## 📈 今後の拡張予定

- [ ] レイヤー別WMS配信
- [ ] SLD（Styled Layer Descriptor）対応
- [ ] Vector Tiles配信
- [ ] WFS（Web Feature Service）配信
- [ ] 認証機能
- [ ] ログ機能の拡充

---

🎯 **QGISの地図を世界に配信しましょう！** 🎯

ご質問やフィードバックは、[GitHub Issues](https://github.com/yamamoto-ryuzo/QMapPermalink/issues) でお気軽にお寄せください。