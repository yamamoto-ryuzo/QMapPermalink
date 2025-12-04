# geo_webview — QGIS を即座に OGC サーバー化するプラグイン

> **[geo_suite](https://github.com/yamamoto-ryuzo/geo_suite)** の一部として開発  
> QGIS プロジェクトを WMS/WMTS/WFS の OGC 準拠サーバーに変換し、クライアントアプリと一緒に配布できる軽量プラグイン

## 概要

geo_webview は QGIS を **OGC 標準準拠の地図配信サーバー**に即座に変換します。複雑なサーバー構築不要で、QGIS を起動するだけで WMS、WMTS、WFS サービスが利用可能になります。

**主な用途:**
- 社内 LAN での地図データ共有
- フィールド調査用モバイルアプリへのデータ配信
- 緊急時の臨時地図サーバー構築
- QGIS プロジェクトをそのまま配布可能な地図サービス化

![パネル画面](images/image01.png)

## geo_suite との連携

本プラグインは [geo_suite](https://github.com/yamamoto-ryuzo/geo_suite) プロジェクトの一部として開発されています。

**geo_suite との組み合わせ:**
- **geo_webview**: QGIS を OGC サーバーとして起動（本プラグイン）
- **geo_suite**: クライアントアプリケーション（地図表示・編集）
- **シナリオ**: QGIS + geo_webview でデータ配信、geo_suite でモバイル/デスクトップから利用

両方を組み合わせることで、QGIS プロジェクトをそのままエンドユーザーに配布できるシステムを構築できます。

## 動作環境

- QGIS 3.x（Qt5 / Qt6 両対応）
- Windows / macOS / Linux
- ネットワーク環境: LAN またはローカルホスト
- Python 3.7 以上

## 主要機能

### 🌐 OGC 標準サービス

#### WMS (Web Map Service)
- QGIS プロジェクトをそのまま WMS として配信
- GetCapabilities / GetMap / GetFeatureInfo 対応
- カスタムスタイル（SLD）サポート
- 高解像度画像出力（最大 4096px）

#### WMTS (Web Map Tile Service)  
- タイル形式での高速地図配信
- XYZ タイル形式対応
- キャッシュ機能（将来実装予定）

#### WFS (Web Feature Service) 2.0
- ベクターデータを GeoJSON / GML で配信
- GetCapabilities / GetFeature / DescribeFeatureType 対応
- SLD スタイル情報の取得
- **高速キャッシュ機構**: 2回目以降のリクエストが40倍高速化

### 🚀 パフォーマンス最適化

**WFS レスポンスキャッシュ (v3.4.0):**
```
初回リクエスト: 200ms → 70ms (3倍高速)
2回目以降:     200ms → <5ms (40倍高速!)
1000地物:     1.5秒 → 500ms
10000地物:    15秒 → 5秒
```

### 📡 ネットワーク機能 (v3.5.0)

- **外部アクセス診断**: 接続性チェック、ファイアウォール検出
- **自動ポート設定**: Windows ファイアウォールへの自動ルール追加
- **柔軟なポート設定**: 80-65535 の全範囲対応
- **動的ホスト名解決**: 外部デバイスからのアクセスに自動対応

### 🗺️ クライアント連携

#### OpenLayers 対応
- `/qgis-map` エンドポイントで即座に Web 地図化
- WMS/WMTS との自然な統合

![OpenLayers表示](images/openlayers.png)

#### MapLibre GL 対応
- ベクトルタイル風のモダン表示
- QGIS スタイルを MapLibre スタイルに自動変換
- テーマ・ブックマーク機能 (v3.6.0)

![MapLibre表示](images/maplibre2.png)

#### Google Maps / Google Earth 連携
- 座標の相互変換
- 外部共有リンクから QGIS へのインポート

### 🔄 パーマリンク機能

- 現在の地図ビュー（座標・ズーム・レイヤ状態）を URL で共有
- Office ドキュメント（Excel / PowerPoint）への埋め込み
- 高解像度 PNG エクスポート

## クイックスタート

### 1. インストール

```bash
# QGIS プラグインディレクトリに配置
# Windows: %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\geo_webview
# macOS: ~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/geo_webview
# Linux: ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/geo_webview
```

または QGIS プラグインマネージャーからインストール可能です。

### 2. 基本的な使い方

1. QGIS でプロジェクト（.qgs/.qgz）を開く
2. メニューから「Web > geo_webview」を選択
3. パネルが表示され、自動的に HTTP サーバーが起動
4. 表示される URL（例: `http://localhost:8089`）でサービスにアクセス

### 3. OGC サービスの利用

**WMS サービス:**
```bash
# GetCapabilities
http://localhost:8089/wms?SERVICE=WMS&REQUEST=GetCapabilities

# GetMap
http://localhost:8089/wms?SERVICE=WMS&REQUEST=GetMap&LAYERS=mylayer&WIDTH=800&HEIGHT=600&BBOX=...
```

**WMTS サービス:**
```bash
# XYZ タイル
http://localhost:8089/wmts/{z}/{x}/{y}.png

# GetCapabilities
http://localhost:8089/wmts?SERVICE=WMTS&REQUEST=GetCapabilities
```

**WFS サービス:**
```bash
# GetCapabilities
http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetCapabilities

# GetFeature (GeoJSON)
http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetFeature&TYPENAME=mylayer&OUTPUTFORMAT=application/json
```

## 主なユースケース

### 1. フィールド調査支援

QGIS で作成した地図データを、調査員のモバイル端末（geo_suite アプリ）にリアルタイム配信。

```
[本部 PC]
 └─ QGIS + geo_webview (WMS/WFS 配信)
      ↓
[フィールド]
 └─ モバイル端末 + geo_suite (データ受信・編集)
```

### 2. 社内地図ポータル

部署内の地図データを QGIS から配信し、各メンバーがブラウザで閲覧。

```bash
# 部署内 LAN で配信
http://192.168.1.100:8089/qgis-map
```

### 3. 緊急時の臨時地図サーバー

災害対応時、既存の QGIS プロジェクトを即座にサーバー化して情報共有。

### 4. プロジェクト配布パッケージ

QGIS Portable + geo_webview + データを USB メモリで配布し、受け取った人が即座にサーバーとして起動。

## WFS 詳細仕様

### 対応オペレーション

| オペレーション | 説明 | 出力形式 |
|--------------|------|---------|
| GetCapabilities | サービス情報・レイヤー一覧 | XML |
| GetFeature | 地物データ取得 | GeoJSON / GML |
| DescribeFeatureType | スキーマ情報 | XML |
| GetStyles | スタイル情報（SLD） | XML |

### パラメータ

```bash
# 基本パラメータ
SERVICE=WFS          # 必須: "WFS"
REQUEST=GetFeature   # 必須: オペレーション名
VERSION=2.0.0        # オプション: デフォルト 2.0.0
TYPENAME=layer_name  # 必須: レイヤー名
OUTPUTFORMAT=application/json  # オプション: GeoJSON/GML

# フィルタリング
MAXFEATURES=100      # 最大地物数
BBOX=minx,miny,maxx,maxy  # 空間フィルタ
SRSNAME=EPSG:4326    # 座標系
```

### 使用例

```bash
# レイヤー一覧を取得
curl "http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetCapabilities"

# GeoJSON で地物を取得
curl "http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetFeature&TYPENAME=roads&OUTPUTFORMAT=application/json"

# 範囲指定で取得
curl "http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetFeature&TYPENAME=buildings&BBOX=130,30,140,40"

# スタイル情報を取得
curl "http://localhost:8089/wfs?SERVICE=WFS&REQUEST=GetStyles&TYPENAME=roads"
```

## MapLibre 連携

### スタイル自動変換

QGIS のレンダラ設定を MapLibre スタイルに自動変換:

- シンボルレンダラ → circle/line/fill レイヤ
- カテゴリ値レンダラ → データ駆動スタイル
- ルールベースレンダラ → フィルタ式変換

### エンドポイント

```bash
# ベーススタイル（WMTS のみ）
http://localhost:8089/maplibre-style

# レイヤー別スタイル（WFS + スタイル）
http://localhost:8089/maplibre-style?typename=layer_name

# MapLibre ビューア
http://localhost:8089/maplibre
```

### カスタマイズ

```javascript
// カスタム MapLibre スタイルの適用
map.setStyle('http://localhost:8089/maplibre-style?typename=roads');
```

## Office 連携

### Excel へのリンク埋め込み

1. geo_webview でパーマリンク生成
2. Excel セルにハイパーリンクとして設定
3. クリックで QGIS が該当箇所にジャンプ

### PowerPoint での活用

1. 高解像度 PNG をエクスポート
2. スライドに画像を挿入
3. 画像にパーマリンクを設定
4. プレゼン中にクリックで詳細表示

## 開発・カスタマイズ

### アーキテクチャ

```
geo_webview/
├── plugin.py              # メインプラグイン
├── panel.py               # UI パネル
├── server_manager.py      # HTTP サーバー管理
├── wms_service.py         # WMS 実装
├── wmts_service.py        # WMTS 実装
├── wfs_service.py         # WFS 実装
├── maplibre_generator.py  # MapLibre 変換
└── webmap_generator.py    # OpenLayers 生成
```

### 詳細仕様

技術仕様の詳細は [`SPEC.md`](./SPEC.md) を参照してください。

### 開発手順

1. [`SPEC.md`](./SPEC.md) で仕様を確認
2. 主要ファイルを把握
3. QGIS で動作確認
4. 変更 → テスト → コミットのサイクル

### 翻訳対応

10言語対応（英語、フランス語、ドイツ語、スペイン語、イタリア語、ポルトガル語、日本語、中国語、ロシア語、ヒンディー語）

```bash
# 翻訳ファイル更新
python update_translations.py
```

## セキュリティ注意事項

⚠️ **重要**: 本プラグインは社内 LAN での利用を前提としています。

- 機密データを含む場合は外部公開を避けてください
- 外部公開が必要な場合は認証・アクセス制御を実装してください
- ファイアウォール設定を適切に行ってください
- 最小限のデータのみを公開してください

## 今後の開発方針

- ✅ WMS/WMTS/WFS の基本機能実装
- ✅ キャッシュ機構による高速化
- ✅ MapLibre スタイル自動変換
- ⏳ タイルキャッシュ機能（検討中）
- ❌ ベクトルタイルサーバー（他サービス利用を推奨）

## バージョン履歴

- **v3.x**: geo_suite統合、OGC準拠サーバー化、10言語対応
- **v2.x**: WMTS/MapLibre対応
- **v1.x**: 基本機能（WMS/OpenLayers）

詳細: [`CHANGELOG.md`](./CHANGELOG.md)

## ライセンス

GNU General Public License version 3 (GPLv3)  
詳細: [LICENSE](./LICENSE)

## 免責事項

本システムは個人のPCで作成・テストされたものです。  
ご利用によるいかなる損害も責任を負いません。

<p align="center">
  <a href="https://giphy.com/explore/free-gif" target="_blank">
    <img src="https://github.com/yamamoto-ryuzo/QGIS_portable_3x/raw/master/imgs/giphy.gif" width="500" title="avvio QGIS">
  </a>
</p>



