# BBOX Server統合 - プラグイン内配置完了

## 📦 新しい構造

BBOX Server機能を **`qmap_permalink/bbox/`** 配下に統合しました。

```
qmap_permalink/
├── bbox/                       ← BBOX統合モジュール
│   ├── __init__.py            # モジュールエントリーポイント
│   ├── bbox_manager.py        # 統合マネージャー
│   ├── bbox_process.py        # プロセス管理
│   ├── bbox_config.py         # 設定管理
│   ├── bbox_exporter.py       # データエクスポート
│   ├── bbox_downloader.py     # バイナリダウンロード
│   ├── README.md              # 詳細ドキュメント
│   ├── bin/                   # バイナリ（.gitignore）
│   ├── config/                # 設定ファイル
│   └── data/                  # データ（.gitignore）
├── qmap_permalink.py          # メインプラグイン
├── qmap_permalink_panel.py    # UIパネル
└── ... (その他の既存ファイル)
```

## 🎯 統合の利点

### 1. 単一のプラグインとして配布
- ✅ QGISプラグインマネージャーで一括インストール
- ✅ 依存関係の明確化
- ✅ バージョン管理の統一

### 2. シームレスな統合
- ✅ QGIS UIから直接BBOX Serverを制御
- ✅ プロジェクト変更時の自動同期
- ✅ 開発→本番へのスムーズな移行

### 3. 保守性の向上
- ✅ コードベースが一元化
- ✅ 設定ファイルの共有
- ✅ エラー処理の統一

## 🚀 使い方

### プラグインから使用

```python
# QGISプラグイン内で
from qgis.utils import plugins

# プラグイン取得
permalink_plugin = plugins['QMapPermalink']

# BBOX Managerにアクセス
if hasattr(permalink_plugin, 'bbox_manager'):
    bbox_manager = permalink_plugin.bbox_manager
    
    # BBOX Server起動
    bbox_manager.start_bbox_server(port=8080)
    
    # データを同期
    bbox_manager.sync_to_bbox()
    
    # 停止
    bbox_manager.stop_bbox_server()
```

### Pythonコンソールから直接使用

```python
from qmap_permalink.bbox import BBoxManager

# マネージャー作成
manager = BBoxManager()

# ステータス確認
print(manager.get_status())

# エクスポート＆起動
manager.start_bbox_server(port=8080, auto_export=True)
```

## 🔄 ワークフロー

```
1. QGIS起動 + QMapPermalinkプラグイン有効化
   ↓
2. QGISでプロジェクト編集
   ├─ QMapPermalink: リアルタイムプレビュー (port 8089)
   └─ BBOX Manager: バックグラウンドで待機
   ↓
3. 本番配信が必要になったら
   ├─ manager.export_and_configure()
   │  └─ レイヤーをGeoJSON/GeoPackageにエクスポート
   │  └─ bbox.toml設定ファイル生成
   ├─ manager.start_bbox_server(port=8080)
   │  └─ BBOX Serverプロセス起動
   └─ 高性能配信開始 (http://localhost:8080/)
   ↓
4. プロジェクト変更時
   └─ manager.sync_to_bbox()
      └─ 自動でエクスポート→再起動
```

## 📝 次のステップ

### 実装済み ✅
- [x] BBOX統合モジュール作成 (`qmap_permalink/bbox/`)
- [x] プロセス管理機能
- [x] 設定ファイル生成機能
- [x] データエクスポート機能
- [x] ダウンロード機能（タスク形式）

### 今後の実装 ⬜
- [ ] UIパネルにBBOX制御ボタン追加
- [ ] プロジェクト変更の自動検知＆同期
- [ ] WMTSキャッシュ→MBTiles変換機能
- [ ] ステータス表示ウィジェット
- [ ] ログビューアー

## 🔧 開発者向け情報

### モジュール構成

```python
# モジュールインポート
from qmap_permalink.bbox import (
    BBoxManager,      # 統合マネージャー
    BBoxExporter,     # データエクスポート
    BBoxConfig,       # 設定管理
    BBoxProcessManager # プロセス管理
)

# 使用例
manager = BBoxManager()
status = manager.get_status()
```

### プラグインへの統合

`qmap_permalink.py` のinitGui()に追加:

```python
def initGui(self):
    # ... 既存のコード ...
    
    # BBOX Manager初期化
    try:
        from .bbox import BBoxManager
        self.bbox_manager = BBoxManager()
        
        if self.bbox_manager.is_bbox_available():
            QgsMessageLog.logMessage(
                "✅ BBOX Server integration available",
                "QMapPermalink", Qgis.Info
            )
    except Exception as e:
        self.bbox_manager = None
        QgsMessageLog.logMessage(
            f"⚠️ BBOX integration failed: {e}",
            "QMapPermalink", Qgis.Warning
        )
```

### クリーンアップ

`qmap_permalink.py` のunload()に追加:

```python
def unload(self):
    # ... 既存のコード ...
    
    # BBOX Manager クリーンアップ
    if hasattr(self, 'bbox_manager') and self.bbox_manager:
        self.bbox_manager.cleanup()
```

## 📚 関連ドキュメント

- **qmap_permalink/bbox/README.md** - 詳細API仕様
- **BBOX公式**: https://www.bbox.earth/
- **GitHub**: https://github.com/bbox-services/bbox

## 🎉 移行完了

ルートレベルの `bbox/` ディレクトリは非推奨となり、
すべての機能が `qmap_permalink/bbox/` に統合されました。
