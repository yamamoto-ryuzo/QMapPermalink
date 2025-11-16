# BBOX Server Integration

> **ステータス: 導入中** — 本ドキュメントおよび実装は現在導入作業中です。運用前にローカル検証・設定確認を必ず行ってください。

## 概要

BBOX Server機能をQMapPermalinkプラグイン内に統合しました。

## フォルダ構成

```
qmap_permalink/bbox/
├── __init__.py          # モジュール初期化
├── bbox_manager.py      # 統合マネージャー（メインAPI）
├── bbox_process.py      # プロセス管理（起動・停止）
├── bbox_config.py       # 設定ファイル生成
├── bbox_downloader.py   # バイナリダウンロード
├── bin/                 # BBOX Serverバイナリ（.gitignore）
├── config/              # 設定ファイル
└── data/                # エクスポートデータ（.gitignore）
```

## 使用方法

### 1. QGISプラグインから使用

```python
from qmap_permalink.bbox import BBoxManager

# マネージャー初期化
bbox_manager = BBoxManager()

# BBOX Serverが利用可能かチェック
if bbox_manager.is_bbox_available():
    # データエクスポート＆設定生成
    bbox_manager.export_and_configure()
    
    # BBOX Server起動（ポート8080）
    bbox_manager.start_bbox_server(port=8080)
    
    # ステータス確認
    status = bbox_manager.get_status()
    print(status)
    
    # 停止
    bbox_manager.stop_bbox_server()
```

### 2. バイナリダウンロード

```python
from qmap_permalink.bbox.bbox_downloader import download_bbox_server

# 最新版をダウンロード（バックグラウンドタスク）
task = download_bbox_server(version="v0.6.2")
```

### 3. データの準備について

自動エクスポート（プラグイン内部で QGIS レイヤーを自動的にエクスポートしてコピーする機能）は廃止されました。
データの二重化やサイロ化を避けるため、開発者/運用者はプロジェクトルート以下に GeoJSON/GPKG/MBTiles 等の
BBOX 互換フォーマットのファイルを手動で用意してください。

その上で、`BBoxManager.export_and_configure()` を呼ぶと、プロジェクトルートおよびプラグインの `data/` を探索して
見つかったファイルをもとに `bbox.toml` を生成します。

## 機能一覧

### BBoxManager（統合マネージャー）
- `is_bbox_available()` - BBOX Server利用可否チェック
- `get_status()` - 全体ステータス取得
- `start_bbox_server(port, auto_export)` - BBOX Server起動
- `stop_bbox_server()` - BBOX Server停止
- `export_and_configure(format)` - データエクスポート＆設定生成
- `sync_to_bbox()` - QGISプロジェクト変更を同期
````markdown
# BBOX（BBOX Server） - 統合ドキュメント

> **ステータス: 導入中** — 本ドキュメントおよび実装は現在導入作業中です。運用前にローカル検証・設定確認を必ず行ってください。

このドキュメントは `qmap_permalink` プラグイン内の BBOX 統合機能（`qmap_permalink/bbox`）の動作環境、セットアップ、実行手順、および今後の改修候補をまとめたもの。リポジトリ直下の `bbox.md` の内容を統合し、`qmap_permalink/bbox/README.md` を単一の参照先としました。

---

## 概要
- **目的**: QGIS プラグイン `QMapPermalink` から外部の BBOX Server を利用し、ローカル／開発／本番環境でタイルやコレクションを高速に配信する。
- **主要機能**:
  - プラグイン内での BBOX バイナリ検出・起動・停止
  - TOML 設定ファイル生成（`bbox.toml`）
  - BBOX バイナリのダウンロード機能（GitHub Releases を利用）

## フォルダ構成

```
qmap_permalink/bbox/
├── __init__.py          # モジュール初期化
├── bbox_manager.py      # 統合マネージャー（メインAPI）
├── bbox_process.py      # プロセス管理（起動・停止）
├── bbox_config.py       # 設定ファイル生成
├── # bbox_exporter.py     # (エクスポーターは廃止／手動運用を推奨)
├── bbox_downloader.py   # バイナリダウンロード
├── bin/                 # BBOX Serverバイナリ（.gitignore）
├── config/              # 設定ファイル
└── data/                # エクスポートデータ（.gitignore）
```

## 動作環境（現状・推奨）
- **Python**: QGIS にバンドルされる Python 実行環境（プラグインなので通常は QGIS の Python、一般に Python 3.7+ / QGIS バージョンに依存）。
- **QGIS**: QGIS 3 系（プラグイン API と `qgis.core` を使用）。実行は QGIS のプラグインコンテキスト内で行うことを想定。
- **OS**: Windows / Linux / macOS をサポート（ダウンロード時にプラットフォーム別バイナリを取得）。
- **外部バイナリ**: `bbox-server`（Windows は `bbox-server.exe`）。

## バイナリ検出順序（`bbox_process.py`）
1. `qmap_permalink/bbox/bin/<binary>`（プラグイン内の `bin/`）
2. プラグインの親ディレクトリにある別プラグイン `bbox/bin/`
3. システム `PATH` 上の `bbox-server`（`shutil.which`）

見つからない場合、`bbox_downloader` により GitHub Releases からダウンロードして `bbox/bin/` に配置する設計です。

## 設定ファイル & データ配置
- 設定ファイル: `qmap_permalink/bbox/config/bbox.toml`（`BBoxConfig` が生成・保存）
- データ出力先: `qmap_permalink/bbox/data` またはプロジェクトルート以下（推奨）。自動エクスポートは廃止されているため、GeoJSON/GPKG/MBTiles 等のファイルはプロジェクト内に手動で配置してください。
- 設定内容: webserver（bind, port, threads）、cors、tilesets、collections（各エントリは TOML で出力）

## 使用方法（要点）

### 1. QGISプラグインから使用（簡易）

```python
from qmap_permalink.bbox import BBoxManager

# マネージャー初期化
bbox_manager = BBoxManager()

# BBOX Serverが利用可能かチェック
if bbox_manager.is_bbox_available():
    # プロジェクト配下に用意したファイルを元に設定を生成
    bbox_manager.export_and_configure()
    
    # BBOX Server起動（ポート8080）
    bbox_manager.start_bbox_server(port=8080)
    
    # ステータス確認
    status = bbox_manager.get_status()
    print(status)
    
    # 停止
    bbox_manager.stop_bbox_server()
```

### 2. バイナリダウンロード

```python
from qmap_permalink.bbox.bbox_downloader import download_bbox_server

# 最新版をダウンロード（バックグラウンドタスク）
task = download_bbox_server(version="v0.6.2")
```

### 3. データの準備について（重要）

自動エクスポート（プラグイン内部で QGIS レイヤーを自動的にエクスポートしてコピーする機能）は廃止されました。
データの二重化やサイロ化を避けるため、開発者/運用者はプロジェクトルート以下に GeoJSON/GPKG/MBTiles 等の
BBOX 互換フォーマットのファイルを手動で用意してください。

その上で、`BBoxManager.export_and_configure()` を呼ぶと、プロジェクトルートおよびプラグインの `data/` を探索して
見つかったファイルをもとに `bbox.toml` を生成します。

## 機能一覧

### BBoxManager（統合マネージャー）
- `is_bbox_available()` - BBOX Server利用可否チェック
- `get_status()` - 全体ステータス取得
- `start_bbox_server(port, auto_export)` - BBOX Server起動
- `stop_bbox_server()` - BBOX Server停止
- `export_and_configure(format)` - 設定ファイル生成（自動エクスポートは行わない）
- `sync_to_bbox()` - QGISプロジェクト変更を同期
- `cleanup()` - クリーンアップ

### BBoxProcessManager（プロセス管理）
- `is_available()` - バイナリ存在チェック
- `is_running()` - 実行中チェック
- `start(config_file, port, cwd=None)` - プロセス起動（`cwd` で起動作業ディレクトリを指定可能）
- `stop()` - プロセス停止
- `get_version()` - バージョン取得

### BBoxConfig（設定管理）
- `set_port(port)` - ポート設定
- `add_tileset(name, source, ...)` - タイルセット追加
- `add_collection(name, source, srs)` - コレクション追加
- `save()` - 設定ファイル保存
- `load()` - 設定ファイル読み込み

## 実装メモ
- `BBoxConfig.generate_toml()` は簡易的な TOML 文字列生成を使用しています。必要なら `toml` ライブラリ導入を検討してください。
- `BBoxManager` はプロジェクトディレクトリ（`project_basedir`）を `BBoxConfig` に設定し、`process.start()` に `cwd` を渡すことで相対パスが正しく解決されるようにしています。

## ダウンロード仕様（`bbox_downloader.py`）
- URL パターン: `https://github.com/bbox-services/bbox/releases/download/{version}/{file_name}`
- デフォルト version: `v0.6.2`
- OS 判定によりファイル名を切替（Windows: zip、Linux/macOS: tar.gz）
- ダウンロードは `QgsTask` として非同期に実行し、`bin/` に展開

## 手動検証手順（開発者向け、pwsh）
1. バイナリ検出確認（PATH 上のバイナリ確認）
```
Get-Command bbox-server -ErrorAction SilentlyContinue
```
2. 既存バイナリのバージョン確認
```
& 'C:\\path\\to\\bbox-server.exe' --version
```
3. 手動で起動確認（config を使う場合）
```
& 'C:\\path\\to\\bbox-server.exe' -c "C:\\path\\to\\bbox\\config\\bbox.toml" serve
```
4. ポート疎通確認（起動後）
```
curl http://localhost:8080/health
```

## チェックリスト（導入時）
- [ ] プラグイン内 `bbox/bin` に対応バイナリがあるか
- [ ] `qmap_permalink/bbox/config/bbox.toml` が生成され正しいパスを参照しているか
- [ ] プロジェクトルートに GeoJSON/GPKG が配置されているか
- [ ] BBOX サーバが起動し、期待するエンドポイントで応答するか

## 開発上の注意点 / 改善案（今後の改修候補）
- `toml` ライブラリを導入して設定の読み書きを堅牢化する。
- WMTS キャッシュ→MBTiles 変換処理の実装。
- バイナリ検出のロギング強化とバージョン互換性チェック。
- 自動同期（QGIS プロジェクト変更時のトリガ）を UI から有効化できるようにする。
- 単体テスト（エクスポーター、設定生成、プロセス管理）の追加。

---

必要であればこの README をさらに拡張して、自動デプロイ／CI 手順やテスト手順を追加します。レビューポイントや追加したい情報を教えてください。
``` 
