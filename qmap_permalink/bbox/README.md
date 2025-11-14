# BBOX Server Integration

## 概要

BBOX Server機能をQMapPermalinkプラグイン内に統合しました。

## フォルダ構成

```
qmap_permalink/bbox/
├── __init__.py          # モジュール初期化
├── bbox_manager.py      # 統合マネージャー（メインAPI）
├── bbox_process.py      # プロセス管理（起動・停止）
├── bbox_config.py       # 設定ファイル生成
├── bbox_exporter.py     # データエクスポート
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

### 3. データエクスポートのみ

```python
from qmap_permalink.bbox import BBoxExporter

exporter = BBoxExporter()

# ベクターレイヤーをGeoJSONでエクスポート
files = exporter.export_vector_layers(format="GeoJSON")

# エクスポート可能なレイヤーのサマリー取得
summary = exporter.get_export_summary()
```

## 機能一覧

### BBoxManager（統合マネージャー）
- `is_bbox_available()` - BBOX Server利用可否チェック
- `get_status()` - 全体ステータス取得
- `start_bbox_server(port, auto_export)` - BBOX Server起動
- `stop_bbox_server()` - BBOX Server停止
- `export_and_configure(format)` - データエクスポート＆設定生成
- `sync_to_bbox()` - QGISプロジェクト変更を同期
- `cleanup()` - クリーンアップ

### BBoxProcessManager（プロセス管理）
- `is_available()` - バイナリ存在チェック
- `is_running()` - 実行中チェック
- `start(config_file, port)` - プロセス起動
- `stop()` - プロセス停止
- `get_version()` - バージョン取得

### BBoxConfig（設定管理）
- `set_port(port)` - ポート設定
- `add_tileset(name, source, ...)` - タイルセット追加
- `add_collection(name, source, srs)` - コレクション追加
- `save()` - 設定ファイル保存
- `load()` - 設定ファイル読み込み

### BBoxExporter（データエクスポート）
- `export_vector_layers(format, layer_filter)` - ベクターレイヤーエクスポート
- `export_wmts_cache_to_mbtiles(cache_dir, output_name)` - WMTSキャッシュ変換
- `get_export_summary()` - エクスポートサマリー取得

## 統合アーキテクチャ

```
┌─────────────────────────────────────────────┐
│  QMapPermalink Plugin                       │
│  ┌───────────────────────────────────────┐  │
│  │ qmap_permalink.py                     │  │
│  │ - メインプラグインクラス              │  │
│  │ - UI管理                              │  │
│  └───────────────────────────────────────┘  │
│                    │                         │
│  ┌───────────────────────────────────────┐  │
│  │ bbox/bbox_manager.py                  │  │
│  │ - BBOX統合マネージャー                │  │
│  │ - 全機能の統括                        │  │
│  └───────────────────────────────────────┘  │
│         │              │              │      │
│    ┌────┴────┐   ┌────┴────┐   ┌────┴────┐ │
│    │ Process │   │ Config  │   │ Export  │ │
│    │ Manager │   │ Manager │   │ Manager │ │
│    └─────────┘   └─────────┘   └─────────┘ │
└─────────────────────────────────────────────┘
                     ↓
          ┌──────────────────────┐
          │ BBOX Server Process  │
          │ (External Binary)    │
          └──────────────────────┘
```

## 開発と本番の使い分け

| フェーズ | ツール | ポート | 用途 |
|---------|--------|--------|------|
| **開発** | QMapPermalink | 8089 | リアルタイムプレビュー |
| **本番** | BBOX Server | 8080 | 高速配信 |

## 次のステップ

1. ✅ バイナリダウンロード機能の実装完了
2. ✅ プロセス管理機能の実装完了
3. ✅ データエクスポート機能の実装完了
4. ⬜ UI統合（パネルにBBOX制御ボタン追加）
5. ⬜ 自動同期機能（QGISプロジェクト変更時）
6. ⬜ WMTSキャッシュ→MBTiles変換機能
