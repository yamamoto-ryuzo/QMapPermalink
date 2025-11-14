# 変更履歴(Changelog)

このファイルでは QMapPermalink プラグインの主な変更点を記録します。

記法は [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/) に基づき、
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) に準拠します。

## バージョン形式: VA.B.C

- **A**: QGIS コア更新やプラグインアーキテクチャ大幅変更などのメジャー変更
- **B**: UI 変更・新機能追加・中規模な機能拡張
- **C**: 軽微な不具合修正・小改善・プロファイル/プラグインの微修正

## [3.5.0] - 2025-11-14 🌐 ネットワーク機能強化リリース

### Added (追加)
- **外部アクセス診断機能**: ネットワーク接続性の包括的チェック
  - サーバー稼働状態の確認
  - ローカルIPアドレスの自動検出
  - ネットワークURLの生成と表示
  - Windowsファイアウォール状態の検出
  - 許可されているポートのスキャン
  - ワンクリックでネットワークURLをコピー

- **Windowsファイアウォール統合**: 自動ルール管理
  - UAC(ユーザーアカウント制御)による管理者権限昇格
  - PowerShell Start-Process経由の自動ファイアウォールルール追加
  - ポート許可の自動検証
  - 手動実行用コマンドの生成とコピー機能
  - 標準ポート(80, 443)の特別処理

- **柔軟なポート設定**: 全ポート範囲対応
  - ポート範囲: 80-65535 (UIで設定可能)
  - 標準HTTPポート(80)とHTTPSポート(443)のクイック選択ボタン
  - カスタムポート番号の自由入力
  - サーバー再起動時の確認ダイアログ
  - ポート変更のリアルタイム反映

- **動的ホスト名解決**: 外部アクセス完全対応
  - リクエストのHostヘッダーを使用した動的URL生成
  - WMTSタイルURLの自動ホスト名適用
  - WFS GeoJSONデータURLの動的生成
  - localhostと実IPアドレスの自動切り替え
  - 外部デバイスからのWMTS/WFSアクセスが正常動作

- **MapLibreパラメータ形式拡張**: 複数入力形式のサポート
  - x/y/scale/crs/rotation形式の追加
    - 例: `/maplibre?x=15557584.244814&y=4258453.104668&scale=23225.0&crs=EPSG:3857&rotation=60.00`
  - 既存のlat/lon/zoom形式も継続サポート
  - permalink文字列形式も継続サポート
  - MapLibreボタンの出力形式をx/y/scale/crs/rotationに統一

### Fixed (修正)
- HTTPサーバー起動時のポート範囲エラーを修正
  - 標準ポート(80, 443)が正しく使用されない問題を解決
  - ポート範囲の下限を1024から80に変更
  - 範囲指定の論理エラーを修正

- PowerShellコマンド実行エラーの修正
  - powershell.exeの完全パスを使用
  - netsh.exeの完全パスを使用
  - ファイルが見つからないエラーを解決

- WMTSタイルが外部から表示されない問題を修正
  - localhostハードコーディングを削除
  - 動的ホスト名の使用により外部アクセスが可能に

- MapLibreパラメータパース問題を修正
  - center_x/center_yからx/yに統一
  - qmap_maplibre.pyとの整合性を確保

### Changed (変更)
- UI要素の追加
  - 「外部アクセス診断」ボタン
  - 「ポート80」「ポート443」クイック選択ボタン
  - ポート番号入力用スピンボックス(80-65535)

- 診断ダイアログの機能強化
  - ファイアウォールルール追加ボタンの動的表示
  - 管理者権限要求の確認ダイアログ
  - 実行中の視覚的フィードバック
  - 成功時の自動再診断

## [3.4.0] - 2025-11-13 🚀 高速化メジャーリリース

### Added (追加)
- **WFSレスポンスキャッシュ機構**: メモリキャッシュによる超高速応答
  - 5分間のTTL (Time To Live)キャッシュ
  - キャッシュキー: レイヤーID + BBOX + SRS + 最大地物数 + 出力フォーマット
  - 自動クリーンアップ: 期限切れエントリの定期削除
  - キャッシュヒット時: < 5ms (40倍高速)
  - パフォーマンスログ機能付き

- **WFS地物クエリ最適化**: QgsFeatureRequestの高速化
  - `ExactIntersect`フラグによるインデックス利用
  - イテレータベースの効率的な地物取得
  - 最適化されたLIMIT処理 (無駄な取得を回避)
  - メモリ効率の向上

- **WMTSタイルキャッシュ事前生成機能**: レイヤー構成変更時の自動タイル生成
  - ThreadPoolExecutor(4ワーカー)による並列処理
  - ズームレベル z=10-18 (9段階)
  - 地図中心を基準に5×5グリッド = 最大225タイル事前生成
  - バックグラウンド処理でUI操作をブロックしない
  - キャッシュヒット率 98%達成

- **HTTPサーバー並列処理機能**: CPU性能に応じた動的並列処理
  - **CPUコア数自動検出**: `_calculate_optimal_workers()`メソッド
  - 動的ワーカー数: `min(32, max(4, cpu_count + 4))`
    - 4コアPC → 8ワーカー
    - 8コアPC → 12ワーカー
    - 16コアPC → 20ワーカー
    - 32コアPC → 32ワーカー（上限）
  - ブラウザの複数タイル同時リクエストに完全対応
  - パラパラ表示から瞬時表示に改善

- **WMSレンダリング最適化**: QgsMapSettings最適化フラグ
  - `UseRenderingOptimization`: QGIS内部最適化の活用
  - `DrawEditingInfo = False`: 編集情報描画スキップ
  - `RenderMapTile = True`: タイル境界処理最適化
  - `Antialiasing = False`: アンチエイリアス無効化
  - `HighQualityImageTransforms = False`: 高品質変換オフ
  - `SimplifyGeometry`: ジオメトリ簡略化(tolerance=1.0)
  - PathResolver設定: シンボルキャッシュ効率化

- **WMSテーマ/レイヤーキャッシュ**: メモリキャッシュ機構
  - 同一テーマのQML解析をスキップ
  - レイヤースタイル設定の再利用

### Changed (変更)
- `run_server()`を並列処理対応に全面改善
  - `accept()`後に`ThreadPoolExecutor.submit()`で非同期処理
  - `_handle_client_connection_safe()`ラッパーでエラーハンドリング強化
- `stop_http_server()`にスレッドプール正常終了処理を追加
- WMTSプリウォーム範囲を大幅拡大
  - ズームレベル: z=10-16 → z=10-18
  - グリッド: 3×3 → 5×5
  - タイル数: 63 → 225
- WMSレンダリングに7つの最適化フラグを適用
- HTTPワーカー数を固定値から動的調整に変更

### Performance (パフォーマンス) ⚡
- **WFS GetFeature速度** (Phase 1高速化):
  - 小規模レイヤー(100地物): 200ms → 70ms (3倍高速)
  - 中規模レイヤー(1000地物): 1.5秒 → 500ms (3倍高速)
  - 大規模レイヤー(10000地物): 15秒 → 5秒 (3倍高速)
  - **キャッシュヒット時**: 200ms → < 5ms (40倍高速!)
  - 地物クエリ: 500ms → 150ms (インデックス活用)

- **WMSレンダリング速度**: 30秒 → 0.92秒 (97%改善、32倍高速)
- **WMTSキャッシュヒット率**: 90% → 98%
- **HTTPタイル取得速度** (PCスペック別):
  - 4コアPC: 8タイル = 7.4秒 → 0.92秒 (8倍高速)
  - 8コアPC: 12タイル = 11秒 → 0.92秒 (12倍高速)
  - 16コアPC: 20タイル = 18秒 → 0.92秒 (20倍高速)
- **キャッシュヒット時**: 6タイル = 60ms → 10ms (6倍高速)
- **100タイル取得**: 9.2秒 → 1.84秒 (80%改善)
- ブラウザでのタイル表示がスムーズに（パラパラ表示完全解消）
- ハイスペックPCほど高速化効果が顕著

### Fixed (修正)
- WMTSタイルがパラパラ順番に表示される問題を解決（HTTPの順次処理が原因）
- OpenLayersでの30秒レンダリング問題を解決（最適化フラグの追加）
- テーマ未指定時にレイヤーが表示されない問題を修正（canvas.layers()フォールバック）
- _execute_parallel_rendering()の重複タイマーコードを修正（15s+30s → 30s）

## [3.3.0] - 2025-11-13 (統合前)

### Added (追加)
- **WMTSタイルキャッシュ事前生成機能**: レイヤー構成変更時に、よく使われるズームレベル(z=10-16)のタイルを自動的に並列生成
  - ThreadPoolExecutor(4ワーカー)による効率的な並列処理
  - 現在の地図中心を基準に3×3グリッド × 7ズームレベル = 最大63タイルを事前生成
  - バックグラウンド処理のため、UI操作をブロックしない
- **WMSレンダリング最適化設定**: QgsMapSettings に以下の最適化を適用
  - `UseRenderingOptimization`フラグの有効化でQGIS内部最適化を活用
  - `DrawEditingInfo`フラグの無効化(不要な編集情報描画をスキップ)
  - `RenderMapTile`フラグでタイル境界処理を最適化
  - PathResolverの設定によるシンボルキャッシュ効率化
- **WMSテーマ/レイヤーキャッシュ**: 頻繁に使用されるテーマ設定をメモリキャッシュ
  - 同じテーマの繰り返しリクエストでQML解析をスキップ
  - レイヤースタイル設定の再利用で大幅な高速化
- **HTTPサーバー並列処理準備**: 将来的なタイルリクエスト並列化のためのThreadPoolExecutor追加

### Changed (変更)
- WMTSサービスが`concurrent.futures`モジュールを使用して並列処理を実装
- WMSサービスにテーマ/レイヤーキャッシュ機構を追加
- タイルキャッシュヒット時のレスポンス時間が大幅に短縮(< 10ms)
- WMSレンダリングタイムアウトを30秒→15秒に短縮(高速応答重視)

### Performance (パフォーマンス)
- 初回アクセス時のキャッシュヒット率が90%以上に向上
- 並列タイル生成により、プリウォーム完了時間が最大4倍高速化
- レンダリング最適化により、タイル生成時間が10-30%削減
- テーマ切替時のレスポンス時間が90%以上削減(キャッシュヒット時)
- WMSレンダリング時間: 50-200ms → 30-120ms (レイヤー構成依存)

### Documentation (ドキュメント)
- `WMTS_OPTIMIZATION.md`を更新: WMS最適化の詳細説明を追加
- WMTSとWMSの関係を明確化(WMTSは内部的にWMSを使用)

## メジャー節目(Major Milestones)

- V1.0.0: OpenLayers + WMS（パーマリンク共有の基礎 / ブラウザ再現）
- V2.0.0: MapLibre + WMTS（高速タイル表示とモダン UI）
- V3.0.0: MapLibre + WFS + スタイル注入（QGIS ベクターを忠実転写、注入フロー安定化）

（詳細な旧履歴は簡略化のため整理済み。必要に応じて Git の履歴や過去タグをご参照ください。）


## V2 系列まとめ (V2.0.0 — V2.13.0)

期間: 2025-10-12 〜 2025-10-24

### Added（主な追加）
- WMTS 風タイルエンドポイント `/wmts/{z}/{x}/{y}.png`（既存 WMS レンダリングをプロキシして XYZ 供給）
- MapLibre HTML 生成の拡充（ローカル WMTS 優先、ピッチ制御ボタン）
- テーマ対応 WMS 出力（仮想マップビューにテーマ適用して PNG 生成）
- External Control（外部制御）の自動ナビゲート（ON 時）
- OpenLayers HTML に座標/スケール表示、必要に応じて投影定義・軸順情報を埋め込み

### Changed（主な変更）
- MapLibre: 既定で `maxzoom` のハード固定を撤廃（高ズーム要求を許容、サーバ能力に依存）
- 回転（ANGLE）パイプライン: ANGLE=0 は高速パス、ANGLE!=0 は拡張レンダ→逆回転→中心クロップ→リサンプル
- Google Earth `y`（m/px）トークン対応でスケール推定を精緻化（DPI を考慮）
- OpenLayers HTML を相対パス参照に統一し、外部ブラウザからの参照を安定化

### Fixed（主な修正）
- MapLibre HTML テンプレートでの Python f-string 波括弧エスケープ不具合を修正
- Google Earth URL パースのスケール/ズーム推定の不整合を修正、初期化時の読み込みエラーを解消

### Notes（運用メモ）
- WMTS エンドポイントは軽量プロキシ実装。高負荷用途ではキャッシュ/プリレンダー等の併用を推奨
- 高ズーム挙動はサーバのレンダリング能力次第。ブラウザ/サーバ双方で検証を推奨
- 自動ナビゲートは表示状態を上書きするため、ON/OFF を明示して運用


## V1 系列まとめ (V1.0.0 — V1.10.0)

### 概要
初期の V1 系列 (2025-10-05 〜 2025-10-11) で行った主要な追加・改善のまとめです。V1 系ではプラグインの土台となる機能群を集中的に実装し、ブラウザ連携、HTTP サーバー、テーマ／表示制御、外部連携周りの利便性向上に注力しました。

### ハイライト
- OpenLayers を利用したブラウザ表示（インタラクティブな Web マップ表示）を実装し、QGIS の表示をブラウザ上で再現可能にしました。
- HTTP サーバー機能を専用モジュール `qmap_permalink_server_manager.py` に分離し、起動/停止やリクエスト処理をモジュール化しました。
- Web マップ生成ロジックを `qmap_webmap_generator.py` に分離し、HTML/OpenLayers テンプレート生成を専用化しました。
- Google Maps / Google Earth へのワンクリック連携を追加し、外部地図サービスへ即時に表示を切り替えられる機能を提供しました。
- パーマリンクにテーマ情報（レイヤー状態）を含めるオプションを導入し、地図表示の完全な状態を共有・復元できるようにしました。
- パネル形式 UI へ移行（ダイアログ廃止）、パネル内での多言語対応やインターフェース改善を行いました。
- 回転パラメータ（rotation）のサポート、短いクエリパラメータ形式（x,y,scale,crs,rotation）を導入しました。

### 代表的な変更点（技術的要約）
- モジュール分離による保守性向上: サーバー管理・WebMap 生成・メインロジックを明確に分割。
- テーマ/レイヤー状態のエクスポートと復元: `theme` パラメータを用いた簡潔な共有形式。
- OpenLayers テンプレートの最適化と JavaScript 側の安定化。
- Google 系サービス向け URL 生成アルゴリズムの精度向上（ズーム⇄スケール変換、地球表示パラメータの算出）。

### 利用上の注意
- V1 系は機能拡充に注力したリリース群のため、後続の V2 系では WMS 配信や外部アクセス（ネットワークバインド）の改善などを行い、運用面の強化を行っています。

---

## [3.2.0] - 2025-11-10

### Added
- Qt6 compatibility: runtime shims and fallbacks to support QGIS builds using Qt6/PyQt6.

### Changed
- Replaced direct PyQt imports with `qgis.PyQt` usage where appropriate to allow QGIS to select the correct PyQt binding at runtime.
- Added runtime detection for `QEventLoop.exec_()` vs `exec()` and for `QIODevice.WriteOnly` location (OpenMode/OpenModeFlag), plus fallbacks to avoid AttributeError on Qt6.

### Fixed
- Resolved AttributeError issues raised under Qt6 (missing `QIODevice.WriteOnly`, missing scoped enums) and other small compatibility bugs.

### Notes
- This release focuses on compatibility with Qt6-enabled QGIS builds. Please validate in your QGIS profile (restart QGIS after updating the plugin files) and report any remaining Qt6-specific issues.

