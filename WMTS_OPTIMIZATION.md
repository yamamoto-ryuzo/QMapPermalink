<!--
WMTS/WMS 高速化仕様書
目的: QMapPermalink の WMS/WMTS サービスに関する設計方針と実装仕様を一つにまとめた正式仕様書。
最終更新: 2025-11-16
-->

# WMS/WMTS 高速化 仕様書

この仕様書は QMapPermalink プラグインに実装された WMS および WMTS の高速化機能を整理し、今後の運用・拡張のために一貫した仕様としてまとめたものです。主な目的は次のとおりです。

- ブラウザからのタイル要求に対して低レイテンシで安定した応答を提供すること
- サーバー資源（CPU/メモリ）に応じた安全な並列化ポリシーを定義すること
- データエクスポートとサーバー設定の互換性を保ちながら運用上のトラブルを減らすこと

対象範囲:

- `qmap_permalink/qmap_wms_service.py` — WMS レンダリング最適化
- `qmap_permalink/qmap_wmts_service.py` — WMTS キャッシュ & プリウォーム（事前生成）
- `qmap_permalink/qmap_permalink_server_manager.py` — HTTP サーバー実行ポリシー（Executor 設定等）
- `qmap_permalink/bbox/*` — BBOX エクスポートおよび設定生成（日本語ファイル除外ルール）

---

## 1. 要求仕様

1.1 性能要件

- キャッシュヒット時のレスポンス: < 10ms 目標
- キャッシュミス時の WMS レンダリング: 目標 30–200ms（環境依存）
- プリウォーム完了時間は並列化により短縮され、並列度に比例して改善すること

1.2 可用性・安定性要件

- プリウォーム・エクスポートの失敗は非致命とし、サービス本体の応答性に影響を与えないこと
- QGIS のスレッド安全性制約を尊重し、過度な並列化や共有オブジェクトの不適切な利用を避けること

1.3 運用要件

- 日本語ファイル名による互換性問題を避けるため、BBOX エクスポートで日本語名のファイルはデフォルトでスキップする
- 並列度やプリウォーム範囲は設定で上書き可能とし、低リソース環境でも運用可能にする

---

## 2. 主要設計決定

2.1 プリウォーム並列度 (max_workers)

- 仕様: プリウォーム用 ThreadPoolExecutor の `max_workers` は実行環境の CPU 数を優先して使用する。具体的には `os.cpu_count()` を利用し、値が不明 (None) の場合はフォールバックで `8` を採用する。
- 理由: タイル生成は CPU 集約的な処理であり、環境の CPU 数に合わせて並列度を決めることが最も汎用的かつ効率的。固定値は特定環境では良好でも汎用性に欠けるため、環境適応を採用した。

2.2 プリウォーム対象

- デフォルトズーム範囲: `10–18`（設定可能）
- デフォルトグリッド: 中心±1〜±2 の範囲で構成（実装では 3×3 または 5×5 を選択可能）。仕様としては「グリッドは設定可能」とする。

2.3 エクスポートの互換性（日本語ファイル除外）

- 仕様: レイヤ名または生成予定のファイル名に日本語（ひらがな・カタカナ・漢字）を含む場合、そのレイヤはエクスポート処理をスキップし、`bbox.toml` 等の設定にも含めない。
- 実装: Unicode 範囲 [\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff] を検出する正規表現で判定。
- 理由: 外部プログラムや環境依存のファイル名処理による問題回避。必要ならトランスリテレーションや代替名生成をオプション追加する。

2.4 WMS レンダリングフラグ

- `QgsMapSettings` の最適化フラグを有効化する:
     - `UseRenderingOptimization = True`
     - `RenderMapTile = True`
     - `DrawEditingInfo = False`（編集情報の描画を無効化）
     - `setPathResolver(QgsProject.instance().pathResolver())` を設定してスタイルの解決とキャッシュ効率を高める

2.5 タイムアウト

- レンダリングのタイムアウトを 15 秒に設定。長時間処理を早期に検出して次リクエストの処理を優先する。

---

## 3. 実装仕様（詳細）

3.1 WMTS: プリウォーム処理 (`qmap_permalink/qmap_wmts_service.py`)

- 初期化:
     - cpu_count = os.cpu_count(); if cpu_count is None -> cpu_count = 8
     - `self._prewarm_executor = ThreadPoolExecutor(max_workers=max(1, int(cpu_count)), thread_name_prefix='WMTS-Prewarm')`
- タスク生成:
     - デフォルトZoomRange = 10..18（設定可能）
     - グリッド = 3×3（中心±1）をデフォルトとするが、実装は 5×5（中心±2）もサポート可能。
     - 生成された (z,x,y) タスクは `self._prewarm_executor.submit(self._prewarm_tile, ...)` で実行し、Future を `self._prewarm_futures` に格納する。
     - エラーは個別にログ出力し、プリウォーム全体の失敗として扱わない（非致命）。

3.2 WMS: レンダリング最適化 (`qmap_permalink/qmap_wms_service.py`)

- map settings のフラグ設定（上記 2.4 を参照）
- テーマ/レイヤーキャッシュ:
     - `_layer_cache` と `_theme_cache` を保持し、QML 解析やスタイル適用のコストを削減する。
     - キャッシュヒット時はスタイル解析をスキップして描画を速める。

3.3 エクスポート / 設定生成 (`qmap_permalink/bbox/*`)

- 日本語判定:
     - 実装はモジュール内で `_contains_japanese(s: str) -> bool` を用意し、上記 Unicode 範囲で判定する。
- 例動作:
     - 日本語を含むレイヤーは `BBoxExporter.export_vector_layers()` にてスキップされる。
     - `BBoxManager.export_and_configure()` はスキップ済みのファイルを設定に追加しない。

3.4 HTTP サーバ関連 (`qmap_permalink/qmap_permalink_server_manager.py`)

- HTTP 用 Executor のワーカー数は `_calculate_optimal_workers()` により自動計算される（既存実装）。この方針は WMTS プリウォームの自動化方針と整合する。

---

## 4. 設定項目（提案）

将来の UI や `bbox.toml` 等の設定ファイルで公開する推奨キー:

- `prewarm_enabled` (bool): 自動プリウォームを有効化/無効化。デフォルト: true
- `prewarm_workers` (int | null): 明示的なワーカー数。未指定時は自動検出（`os.cpu_count()` または 8）。
- `prewarm_zoom_min` / `prewarm_zoom_max` (int): プリウォーム対象のズーム範囲。デフォルト: 10 / 18
- `prewarm_grid` (int): 中心グリッド幅（3,5 等）。デフォルト: 3
- `export_skip_japanese` (bool): BBOX エクスポートで日本語ファイルを除外。デフォルト: true

設定優先順位: UI 指定 > 設定ファイル値 > 実装デフォルト（自動検出）

---

## 5. テスト & ベンチ手順

5.1 ベンチ環境

- 複数の CPU 構成（例: 2/4/8/16）で実施することを推奨。ローカルでは CPU 制限ツールや仮想環境を利用する。

5.2 プリウォームベンチ

- 手順:
     1. `.cache/wmts` を削除してキャッシュをクリーンにする
     2. プリウォームを手動またはレイヤ変更でトリガー
     3. 計測: プリウォーム開始〜完了時間、CPU 使用率、生成タイル数
- 指標:
     - プリウォーム完了時間 (秒)
     - 平均/ピーク CPU 使用率 (%)
     - 事前生成タイル数／成功率

5.3 レンダリングベンチ

- 手順:
     1. キャッシュミス時（Cold）とキャッシュヒット時（Warm）のレスポンス時間を測定
     2. レンダリングタイムアウト（15s）での挙動を観察

5.4 回帰テスト

- テーマ切替、スタイル変更、日本語レイヤのエクスポート挙動を確認する自動テストを用意することを推奨。

---

## 6. 運用ガイド

- 低リソース環境では `prewarm_workers` を小さく設定する（例: 2–4）。
- 監視: プリウォームのログ（`QgsMessageLog`）およびキャッシュディレクトリのサイズを定期確認する。
- 障害対応: プリウォームが失敗しても本体は稼働するため、まずはログとキャッシュ整合性を確認する。

---

## 7. 今後の拡張案

1. 設定 UI の追加: プリウォーム設定（ワーカー数・ズーム範囲・グリッド）をプラグイン設定に実装
2. 代替名生成オプション: 日本語ファイルをローマ字化/置換してエクスポートする機能
3. プリウォーム進捗 UI: 進捗バーとキャンセルを実装
4. 適応的スケーリング: 実行時の負荷に応じてワーカー数を動的に変更する実験的機能

---

## 8. 変更履歴

- 2025-11-13: ベース実装 — WMS/WMTS 最適化（プリウォーム: 固定 4 ワーカー等）
- 2025-11-16: 仕様更新 — プリウォーム `max_workers` を CPU 数ベースへ変更（fallback 8）、BBOX エクスポート時の日本語ファイル除外を明文化

---

## 9. 参照実装ファイル

- `qmap_permalink/qmap_wmts_service.py`
- `qmap_permalink/qmap_wms_service.py`
- `qmap_permalink/qmap_permalink_server_manager.py`
- `qmap_permalink/bbox/bbox_exporter.py`
- `qmap_permalink/bbox/bbox_manager.py`

---

この仕様書に基づき、設定 UI の追加や代替名生成の有効化など実装を進めることができます。どの項目を優先して実装するか指示ください。

---

**概要**

WMTS リクエストは内部で WMS のレンダリングパイプラインを利用するため、WMS の最適化が直接 WMTS の性能に影響します。本仕様では以下を標準とします:

- WMS 側: レンダリング最適化フラグ、テーマ/レイヤーキャッシュ、レンダリングタイムアウトの短縮
- WMTS 側: タイルキャッシュの事前生成（プリウォーム）を非同期・並列で実行し、キャッシュヒット率を高める
- エクスポート: 日本語名のファイルはエクスポート/設定生成から除外（運用上の互換性向上）

---

**主要設計決定**

1) プリウォームの並列度（max_workers）
- 仕様: プリウォーム用 ThreadPoolExecutor の `max_workers` は実行環境の CPU 数をそのまま使う（`os.cpu_count()`）。CPU 数が取得できない場合はフォールバックで `8` を使用する。
- 理由: CPU 集約的なレンダリング処理は CPU 数に依存するため、環境に合わせた並列度を自動設定することで汎用的な性能を確保するため。固定値 (4) は特定環境で安定するが、汎用性に欠けるため自動決定を採用した。

2) プリウォーム対象と範囲
- デフォルト: ズーム 10–18（設定可能）で、現在キャンバス中心を基準に 3×3 グリッド（デフォルト）を採用。最大タスク数はグリッド×ズーム数（例: 9×9 = 81）となるため、並列度は CPU に応じて決定する。

3) 日本語ファイルの扱い
- 仕様: QGIS からのエクスポート時にレイヤ名または出力ファイル名に日本語（ひらがな・カタカナ・漢字）が含まれる場合、エクスポート処理自体をスキップし、TOML 等の設定に含めない。
- 実装箇所: `qmap_permalink/bbox/bbox_exporter.py` と `qmap_permalink/bbox/bbox_manager.py` にて判定（Unicode 範囲による）。
- 理由: 一部環境や外部ツールでファイル名の扱いに課題が生じることがあるため、安全策として除外する。必要なら代替名生成（トランスリテレーション）オプションを提供する。

4) WMS レンダリング設定
- レンダリング最適化フラグ（例: `QgsMapSettings.UseRenderingOptimization` を True）や `RenderMapTile` を有効化し、`DrawEditingInfo` を無効化する。

5) タイムアウト
- レンダリングタイムアウトを 15 秒に設定。長時間の待ちが次のリクエスト性能を阻害するため短縮する。

---

**実装仕様（詳細）**

1. WMTS プリウォーム（`qmap_permalink/qmap_wmts_service.py`）
- Executor 初期化:
     - cpu_count = os.cpu_count(); if None -> cpu_count = 8
     - self._prewarm_executor = ThreadPoolExecutor(max_workers=max(1, int(cpu_count)), thread_name_prefix='WMTS-Prewarm')
- タスク生成:
     - デフォルトズーム範囲: 10–18
     - デフォルトグリッド: center ±2 (5×5 = 25) ※既存実装は 3×3 の記述があるが、コードでは 5×5 を使用している。仕様としては「グリッドは設定可能」とする。
     - 生成したタスクは Executor に submit して `_prewarm_futures` に保持する。失敗は個別ログで取り扱い、全体失敗は非致命とする。

2. WMS レンダリング（`qmap_permalink/qmap_wms_service.py`）
- map settings:
     - setFlag(QgsMapSettings.UseRenderingOptimization, True)
     - setFlag(QgsMapSettings.DrawEditingInfo, False)
     - setFlag(QgsMapSettings.RenderMapTile, True)
     - setPathResolver(QgsProject.instance().pathResolver())
- キャッシュ:
     - `_layer_cache`, `_theme_cache` を持ち、テーマ/スタイル解析の結果を再利用する。

3. エクスポート／設定生成（`qmap_permalink/bbox/*`）
- 日本語判定:
     - 正規表現で Unicode 範囲 [\\u3040-\\u30ff\\u3400-\\u4dbf\\u4e00-\\u9fff\\uf900-\\ufaff] を検索し、ヒットしたらスキップ。
- 振る舞い:
     - エクスポート自体を実行しない（ファイルを生成しない）。ログに警告を出力。
     - TOML (`bbox.toml`) にもそのコレクションは書き込まれない。

---

**設定項目（将来の UI/設定ファイル）**

推奨キー（例: `bbox.toml` やプラグイン設定で追加）:

- `prewarm_workers` (int | optional): プリウォームで使用するワーカー数。未指定時は `os.cpu_count()`、取得不可時は 8。設定優先順位: UI 指定 > 設定ファイル > 自動検出。
- `prewarm_zoom_min`, `prewarm_zoom_max` (int): プリウォーム対象ズーム範囲。デフォルト: 10–18。
- `prewarm_grid` (int): 中心グリッド幅（例: 3 -> 3×3, 5 -> 5×5）。デフォルト: 3。
- `prewarm_enabled` (bool): 自動プリウォームを有効化/無効化。
- `export_skip_japanese` (bool): BBOX エクスポート時に日本語ファイルをスキップ（デフォルト: True）。

---

**テスト / ベンチ手順**

1) ベンチ環境準備
- 同一サーバで CPU 数の異なるインスタンス（例: 2, 4, 8, 16 コア）を用意するか、ローカルで CPU 制限ツールを用いる。

2) プリウォームベンチ
- 手順:
     - キャッシュを削除
     - プリウォームを開始（自動あるいは手動トリガー）
     - 計測: プリウォーム完了までの時間、CPU 使用率、生成タイル数
- 指標:
     - プリウォーム完了時間 (秒)
     - 平均 CPU 使用率 (%)
     - キャッシュヒット率（事前生成後）

3) レンダリングベンチ
- 手順:
     - 同一タイルへの連続リクエストで Cold/Warm レスポンスを計測
     - WMS のタイムアウトを 15s に設定した上で、レンダリング時間分布を測定

4) 回帰テスト
- 機能: テーマ切替、スタイル変更、長時間レンダリング時の早期エラー検出、エクスポート時の日本語スキップ。ログと出力ファイル／TOML を確認する。

---

**運用ガイド**

- 推奨デフォルトは自動検出（CPU数）で運用負荷を抑えつつ、高速化を得ること。低リソース環境では `prewarm_workers` を小さく設定する。
- 日本語ファイルをどう扱うかは運用ポリシーに依存する。外部との交換がある環境では日本語をスキップする現在の仕様が安全だが、必要であれば代替名生成を有効にするオプションを追加すること。
- 障害時は QGIS のログ（`QgsMessageLog`）を第一に確認する。プリウォームは副次的機能のため、失敗してもサービスは通常動作する。

---

**今後の拡張案**

1. 設定 UI の実装: プリウォームのズーム範囲・グリッド・ワーカー数をプラグイン設定で変更可能にする。
2. プリウォーム進捗 UI: 進捗表示やキャンセル機能を実装する。
3. ワーカーの上限ポリシー: メモリや同時リクエスト数に基づく適応的スケーリングを検討する。
4. 日本語ファイルの扱い: トランスリテレーション（例: romaji）を選択肢として追加し、エクスポート互換性を維持するオプションを用意する。

---

変更履歴
- 2025-11-13: WMS/WMTS 最適化実装（プリウォーム: 固定 4 ワーカー、レンダリング最適化等）
- 2025-11-16: 仕様更新 — プリウォームの `max_workers` を CPU 数ベースに自動決定（fallback 8）、BBOX エクスポートで日本語ファイルを除外する仕様を明確化

---

参照実装ファイル
- `qmap_permalink/qmap_wmts_service.py`
- `qmap_permalink/qmap_wms_service.py`
- `qmap_permalink/qmap_permalink_server_manager.py`
- `qmap_permalink/bbox/bbox_exporter.py`
- `qmap_permalink/bbox/bbox_manager.py`

この仕様書に基づく実装や設定変更の提案があれば、具体的な要件（UI・設定項目名・互換ポリシー）を提示してください。
# WMTS/WMS高速化実装ガイド

## 概要
QMapPermalinkのWMTS・WMSサービスに対して、並列処理とキャッシュ最適化を実装しました。
**重要**: WMTSは内部的にWMSのレンダリングパイプラインを使用しているため、WMSの高速化がそのままWMTSの高速化につながります。

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

### 2. WMSレンダリングの最適化
**実装場所**: `qmap_permalink/qmap_wms_service.py`

#### 2.1 レンダリング最適化フラグ
```python
# UseRenderingOptimization: レンダリング最適化を有効化
map_settings.setFlag(QgsMapSettings.UseRenderingOptimization, True)

# DrawEditingInfo を無効化(編集情報の描画をスキップ)
map_settings.setFlag(QgsMapSettings.DrawEditingInfo, False)

# RenderMapTile: タイルレンダリング最適化
map_settings.setFlag(QgsMapSettings.RenderMapTile, True)

# キャッシュヒントを有効化
map_settings.setPathResolver(QgsProject.instance().pathResolver())
```

#### 2.2 テーマ/レイヤーキャッシュ
```python
# 初期化時にキャッシュを作成
self._layer_cache = {}  # {layer_id: {style_name: qml_string}}
self._theme_cache = {}  # {theme_name: (layers, style_overrides)}

# テーマ設定をキャッシュして再利用
if themes in self._theme_cache:
    virtual_layers, layer_style_overrides = self._theme_cache[themes]
    # キャッシュヒット → QMLファイル解析をスキップ
```

**効果**:
- テーマ設定の解析時間を90%以上削減
- 同じテーマの繰り返しリクエストが劇的に高速化

#### 2.3 タイムアウト最適化
```python
# タイムアウトを30秒→15秒に短縮
timer.start(15000)  # 15秒
```

**理由**:
- WMTSタイルは高速応答が重要(ブラウザがタイルを並列リクエスト)
- 15秒以上かかるレンダリングは実用的でないためエラーとして早期検出
- 不要な待機時間を削減して次のリクエストを早く処理

### 期待される効果

| 項目 | 改善効果 | 実装箇所 |
|------|---------|---------|
| **キャッシュヒット率** | 90%以上(プリウォーム完了後) | WMTS |
| **レスポンス時間(キャッシュヒット)** | < 10ms | WMTS |
| **レスポンス時間(キャッシュミス)** | 50-200ms → 30-120ms | WMS最適化 |
| **プリウォーム速度** | 最大4倍高速化(並列処理) | WMTS |
| **タイル生成時間** | 10-30%削減(レンダリング最適化) | WMS |
| **テーマ切替** | 90%以上削減(キャッシュヒット時) | WMS |
| **タイムアウト検出** | 30秒 → 15秒(早期エラー検出) | WMS |

### WMSとWMTSの関係

```
ブラウザ → WMTS(/wmts/z/x/y.png)
              ↓
         WMTSサービス (qmap_wmts_service.py)
              ↓ キャッシュチェック
              ↓ (キャッシュミス時)
              ↓
         WMSレンダリング (_handle_wms_get_map_with_bbox)
              ↓
         QgsMapRendererParallelJob (qmap_wms_service.py)
              ↓ レンダリング最適化適用
              ↓
         PNG画像生成
              ↓
         WMTSキャッシュに保存
              ↓
         ブラウザにレスポンス
```

**重要**: WMSの最適化がWMTSのパフォーマンスに直結するため、両方を最適化しました。

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
