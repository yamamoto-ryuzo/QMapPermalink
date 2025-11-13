# WMTS高速化実装ガイド

## 概要
QMapPermalinkのWMTSサービスに対して、並列処理とキャッシュ最適化を実装しました。

## 実装された高速化機能

### 1. タイルキャッシュの事前生成(プリウォーム)
**実装場所**: `qmap_permalink/qmap_wmts_service.py`

#### 機能説明
- レイヤー構成が変更された際に、よく使われるズームレベル(z=10-16)のタイルを自動的に事前生成
- 現在の地図の中心を基準に3×3グリッド(9タイル)×7ズームレベル = 最大63タイルを並列生成
- ThreadPoolExecutor(最大4ワーカー)を使用した効率的な並列処理

#### 利点
- 初回リクエスト時のレスポンス時間が大幅に短縮
- 地図操作(パン・ズーム)がスムーズになる
- バックグラウンド処理のため、UI操作をブロックしない

#### コード例
```python
# プリウォーム用スレッドプール
self._prewarm_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix='WMTS-Prewarm'
)

# タイル事前生成の自動トリガー
def ensure_identity(self, identity_short=None, identity_raw=None):
    # ... identity処理 ...
    self._maybe_start_prewarm(identity_short, identity_hash, identity_dir)
```

### 2. レンダリング設定の最適化
**実装場所**: `qmap_permalink/qmap_permalink_server_manager.py`

#### 実装内容
```python
# UseRenderingOptimization: レンダリング最適化を有効化
if hasattr(map_settings, 'setFlag'):
    flag = getattr(QgsMapSettings, 'UseRenderingOptimization', None)
    if flag is not None:
        map_settings.setFlag(flag, True)
    
    # DrawEditingInfo を無効化(編集情報の描画をスキップ)
    flag = getattr(QgsMapSettings, 'DrawEditingInfo', None)
    if flag is not None:
        map_settings.setFlag(flag, False)

# キャッシュヒントを有効化
if hasattr(map_settings, 'setPathResolver'):
    from qgis.core import QgsProject
    map_settings.setPathResolver(QgsProject.instance().pathResolver())
```

#### 効果
- QGISの内部レンダリング最適化を活用
- 不要な編集情報の描画をスキップしてパフォーマンス向上
- シンボルキャッシュやパスリゾルバの活用でレンダリング効率化

### 3. HTTPサーバーの並列処理準備
**実装場所**: `qmap_permalink/qmap_permalink_server_manager.py`

#### 追加されたコンポーネント
```python
# ThreadPoolExecutor for parallel tile rendering
self._tile_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix='WMTS-Tile'
)
```

現在のHTTPサーバーは`run_server()`メソッド内で1リクエストずつ順次処理していますが、
このエグゼキューターを使って将来的に並列化可能です。

## パフォーマンス測定

### テスト方法
```python
# QGIS Pythonコンソールから実行
from qmap_permalink.qmap_permalink import QMapPermalink
plugin = QMapPermalink.instance()

# WMTSサービスの診断情報取得
if plugin and plugin.server_manager and plugin.server_manager.wmts_service:
    diag = plugin.server_manager.wmts_service.get_identity_diagnostics()
    print(diag)
```

### 期待される効果
- **初回アクセス**: プリウォーム完了後、キャッシュヒット率90%以上
- **レスポンス時間**: キャッシュヒット時 < 10ms、ミス時 50-200ms (レイヤー構成依存)
- **並列処理**: 4タイル同時レンダリングで最大4倍のスループット向上

## 使用方法

### 自動プリウォーム
レイヤー構成が変更されると自動的にプリウォームが開始されます。
QGIS Pythonコンソールやログで以下のメッセージが確認できます:

```
🚀 WMTS Prewarm: 63タイルを並列生成開始
```

### 手動プリウォーム(オプション)
必要に応じて手動でプリウォームをトリガーできます:

```python
from qmap_permalink.qmap_permalink import QMapPermalink
plugin = QMapPermalink.instance()

if plugin and plugin.server_manager and plugin.server_manager.wmts_service:
    wmts = plugin.server_manager.wmts_service
    # identity情報を取得
    identity_short, identity_raw = wmts._get_identity_info()
    # identityフォルダを作成(プリウォームが自動開始される)
    identity_hash, identity_dir = wmts.ensure_identity(identity_short, identity_raw)
    print(f"Prewarm started for identity: {identity_short}")
```

## トラブルシューティング

### プリウォームが動作しない
1. QGIS Pythonコンソールでエラーログを確認:
   ```python
   from qgis.core import QgsMessageLog
   QgsMessageLog.logMessage("Test", "QMapPermalink")
   ```

2. スレッドプールの状態を確認:
   ```python
   wmts = plugin.server_manager.wmts_service
   print(f"Prewarm executor: {wmts._prewarm_executor}")
   print(f"Active threads: {wmts._prewarm_executor._threads}")
   ```

### パフォーマンスが改善しない
1. キャッシュディレクトリを確認:
   ```python
   import os
   cache_dir = os.path.join(os.path.dirname(__file__), '.cache', 'wmts')
   print(f"Cache dir: {cache_dir}")
   print(f"Cached tiles: {sum(1 for _ in os.walk(cache_dir))}")
   ```

2. レンダリング設定を確認:
   - `UseRenderingOptimization`フラグが有効か
   - `DrawEditingInfo`フラグが無効か

## 今後の拡張可能性

### 1. HTTPサーバーの完全並列化
`run_server()`メソッドを修正して、各リクエストをThreadPoolExecutorにsubmit:

```python
def run_server(self):
    while self._http_running and self.http_server:
        try:
            conn, addr = self.http_server.accept()
        except socket.timeout:
            continue
        
        # 並列処理で各リクエストを処理
        self._tile_executor.submit(self._handle_client_connection, conn, addr)
```

### 2. プリウォーム範囲の設定UI
パネルにプリウォーム設定を追加:
- ズームレベル範囲(デフォルト: 10-16)
- グリッドサイズ(デフォルト: 3x3)
- 並列ワーカー数(デフォルト: 4)

### 3. キャッシュ管理機能
- キャッシュサイズ上限の設定
- 古いキャッシュの自動削除(LRU)
- キャッシュクリアボタン

### 4. 進捗表示
プリウォーム中の進捗をプログレスバーで表示:

```python
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QProgressDialog

# プリウォーム開始時
self._prewarm_progress = QProgressDialog("Prewarming tiles...", "Cancel", 0, len(tasks))
```

## 関連ファイル
- `qmap_permalink/qmap_wmts_service.py` - WMTSサービスとプリウォーム機能
- `qmap_permalink/qmap_permalink_server_manager.py` - HTTPサーバーとレンダリング最適化
- `qmap_permalink/qmap_wms_service.py` - WMSレンダリング処理

## 参考
- QGIS API: `QgsMapRendererParallelJob`
- Python: `concurrent.futures.ThreadPoolExecutor`
- WMTS Standard: OGC WMTS 1.0.0
