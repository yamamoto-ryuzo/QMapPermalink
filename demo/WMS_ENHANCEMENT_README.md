# 🗺️ QGIS WMS配信機能拡張

QMapPermalinkプラグインにWMS（Web Map Service）配信機能を追加しました。この機能により、QGISで現在表示している地図情報をWMSプロトコルで外部に配信できます。

## 🚀 新機能

### 1. WMS 1.3.0 対応
標準的なWMSプロトコルに準拠したAPI提供
- **GetCapabilities**: サービス機能とレイヤー情報の取得
- **GetMap**: 指定されたBBOXでの地図画像取得  
- **GetFeatureInfo**: 地物情報の取得

### 2. タイル配信サービス
OpenStreetMapスタイルのタイル配信API
- **XYZ Tiles**: `/tiles/{z}/{x}/{y}.png` 形式
- **256x256ピクセル**: 標準タイルサイズ
- **キャッシュヘッダー**: 効率的な配信

### 3. リアルタイム同期
QGISのマップビュー変更が自動的にWMS配信に反映
- **即座の更新**: QGISでレイヤーやスタイルを変更すると配信内容も更新
- **現在のビュー**: 常に最新のQGISマップビューを配信

## 📡 利用可能なエンドポイント

### WMS エンドポイント

#### GetCapabilities
```
GET /wms?SERVICE=WMS&REQUEST=GetCapabilities
```
サービスの機能と利用可能なレイヤー情報をXML形式で返します。

#### GetMap
```
GET /wms?SERVICE=WMS&REQUEST=GetMap&BBOX=139.5,35.5,139.9,35.9&WIDTH=800&HEIGHT=600&CRS=EPSG:4326&FORMAT=image/png
```

**パラメータ:**
- `BBOX`: 境界ボックス (minx,miny,maxx,maxy)
- `WIDTH`: 画像幅（ピクセル）
- `HEIGHT`: 画像高さ（ピクセル）
- `CRS`: 座標参照系 (EPSG:4326, EPSG:3857)
- `FORMAT`: 出力形式 (image/png, image/jpeg)

#### GetFeatureInfo
```
GET /wms?SERVICE=WMS&REQUEST=GetFeatureInfo&I=200&J=200&INFO_FORMAT=application/json
```

**パラメータ:**
- `I`: ピクセルX座標
- `J`: ピクセルY座標  
- `INFO_FORMAT`: 出力形式 (text/plain, application/json)

### タイル配信エンドポイント

#### XYZ Tiles
```
GET /tiles/{z}/{x}/{y}.png
```

**例:**
- `GET /tiles/10/904/403.png` - ズームレベル10のタイル

### 既存エンドポイント（引き続き利用可能）

#### インタラクティブ地図
```
GET /qgis-map?lat=35.681&lon=139.767&scale=25000
```

#### PNG画像直接配信
```
GET /qgis-png?lat=35.681&lon=139.767&scale=25000&width=800&height=600
```

## 🛠️ セットアップ方法

### 1. 前提条件
- QGIS 3.x
- QMapPermalinkプラグイン
- Python 3.x

### 2. プラグインの設定
1. QGISでQMapPermalinkプラグインを有効化
2. プラグインのHTTPサーバーを起動
3. デフォルトポート8089でサービス開始

### 3. 動作確認
```bash
# テストスクリプトを実行
python test_wms_functionality.py

# または手動でアクセス
curl "http://localhost:8089/wms?SERVICE=WMS&REQUEST=GetCapabilities"
```

## 📋 使用例

### QGISクライアントでの接続
1. QGIS で「レイヤー」→「レイヤーを追加」→「WMSレイヤーを追加...」
2. 新しい接続を作成:
   - **名前**: QGIS Permalink WMS
   - **URL**: `http://localhost:8089/wms`
3. 接続してレイヤーを追加

### OpenLayersでの表示
```javascript
// WMSレイヤーの作成
const wmsLayer = new ol.layer.Image({
    source: new ol.source.ImageWMS({
        url: 'http://localhost:8089/wms',
        params: {
            'SERVICE': 'WMS',
            'REQUEST': 'GetMap',
            'LAYERS': 'QGIS_Map',  
            'FORMAT': 'image/png',
            'CRS': 'EPSG:3857'
        }
    })
});

// マップに追加
map.addLayer(wmsLayer);
```

### Leafletでタイル表示
```javascript
// XYZタイルレイヤーの作成
const qgisTileLayer = L.tileLayer('http://localhost:8089/tiles/{z}/{x}/{y}.png', {
    attribution: 'QGIS Permalink',
    maxZoom: 18
});

// マップに追加
map.addLayer(qgisTileLayer);
```

## 🧪 テスト機能

### 自動テストスクリプト
```bash
python test_wms_functionality.py
```

以下の機能をテストします:
- サーバー接続
- GetCapabilities レスポンス
- GetMap 画像生成
- GetFeatureInfo 情報取得
- タイル配信
- 既存エンドポイントの互換性

### ブラウザでのテスト
`qgis_wms_demo.html` を開いて、以下を確認できます:
- WMS機能のインタラクティブテスト
- OpenLayersを使った地図表示
- 各エンドポイントの動作状況

## ⚙️ 技術仕様

### 対応プロトコル
- **WMS 1.3.0**: OGC標準準拠
- **XYZ Tiles**: OpenStreetMapスタイル

### 対応座標系
- **EPSG:4326**: WGS84（経度緯度）
- **EPSG:3857**: Web Mercator

### 対応フォーマット
- **画像**: PNG, JPEG
- **情報**: XML, JSON, Plain Text

### パフォーマンス
- **画像生成**: PyQGISを使用したリアルタイム生成
- **キャッシュ**: タイル配信でHTTPキャッシュヘッダー対応
- **同時接続**: 最大10並行リクエスト処理

## 🔧 カスタマイズ

### ポート番号の変更
```python
# qmap_permalink_http_server.py
self.server_port = 8089  # お好みのポートに変更
```

### 画像サイズ制限
```python
# 最大サイズ制限
width = min(width, 1920)   # 最大幅
height = min(height, 1080) # 最大高さ
```

### タイルキャッシュ設定
```python
headers = {
    'Cache-Control': 'public, max-age=3600',  # 1時間キャッシュ
    'Content-Type': content_type,
    'Access-Control-Allow-Origin': '*'
}
```

## 📚 活用シーン

### 1. 社内地図配信
- 社内システムでのQGIS地図の共有
- ダッシュボードでの地図表示
- モバイルアプリでの地図配信

### 2. プロトタイプ開発
- WMS対応アプリケーションの開発テスト
- 地図タイル配信サービスの検証
- 空間データの可視化実験

### 3. 教育・デモンストレーション
- GIS教育での実習用サーバー
- 顧客向けデモンストレーション
- 地図配信の仕組み学習

## 🐛 トラブルシューティング

### サーバーが起動しない
- ポート8089が使用中でないか確認
- QGISプラグインが正常に有効化されているか確認
- ファイアウォール設定を確認

### 画像が表示されない
- QGISにレイヤーが読み込まれているか確認
- マップキャンバスに地図が表示されているか確認
- BBOX パラメータが有効な範囲内か確認

### 座標系エラー
- 対応座標系（EPSG:4326, EPSG:3857）を使用
- QGISプロジェクトの座標系設定を確認

## 📈 今後の改善予定

- [ ] レイヤー別WMS配信対応
- [ ] SLD (Styled Layer Descriptor) 対応
- [ ] WFS (Web Feature Service) 配信
- [ ] Vector Tiles 配信
- [ ] アクセス制御機能
- [ ] ログ機能の拡充

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します。改善提案やバグ報告は[GitHub Issues](https://github.com/yamamoto-ryuzo/QMapPermalink/issues)でお願いします。

## 📄 ライセンス

GNU General Public License v2.0

---

🌟 **QGISの地図を世界に配信しましょう！** 🌟