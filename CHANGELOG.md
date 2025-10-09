# Changelog

All notable changes to the QMap Permalink plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version Format: VA.B.C

- **A**: Major changes due to QGIS core updates or significant plugin architecture changes
- **B**: UI changes, new plugin features, or moderate functionality additions
- **C**: Profile/plugin fixes, minor bug fixes, and small improvements

## [V1.4.0] - 2025-10-09

### 🎨 NEW FEATURE - Theme Support in Permalinks

### Added
- **テーマ機能サポート**: パーマリンクにマップテーマとレイヤー状態情報を含める機能
- **レイヤー状態の保存・復元**: レイヤーの表示/非表示、透明度、スタイル情報をパーマリンクに含める
- **パネルUIにテーマオプション**: 「Include current theme/layer states」チェックボックスを追加
- **自動テーマ検出**: 現在のレイヤー状態から該当するマップテーマを検出する機能
- **テーマ復元機能**: パーマリンクからナビゲーション時にテーマとレイヤー状態を自動復元

### Enhanced
- **パーマリンクURL拡張**: 新しい`theme`パラメータでテーマ情報をJSON形式で含める
- **HTTPサーバー機能強化**: テーマパラメータの解析とナビゲーション処理を追加
- **UI改善**: パネルでテーマ情報を含めるかどうかを選択可能
- **メッセージ表示強化**: テーマ復元の成功/失敗を詳細にフィードバック

### Technical Features
- **QgsMapThemeCollection API**: QGISの標準マップテーマ機能と完全統合
- **レイヤーツリー操作**: QgsLayerTreeの状態を詳細に取得・復元
- **JSON形式のテーマデータ**: 構造化されたテーマ情報の保存形式
- **後方互換性**: 既存のパーマリンクは引き続き動作（テーマなし）

### Usage Examples
テーマ情報を含むパーマリンクの例：
```
http://localhost:8089/qgis-map?x=139.01234&y=35.12345&scale=1000.0&crs=EPSG:4326&rotation=0.00&theme=%7B%22version%22%3A%221.0%22%2C%22current_theme%22%3A%22StandardMap%22%2C%22layer_states%22%3A%7B...%7D%7D
```

### Benefits
- **完全な地図状態の共有**: 位置情報だけでなく、表示設定も含めた完全な地図状態を外部文書で共有
- **チーム作業の効率化**: 複雑なレイヤー設定を含む地図ビューを瞬時に共有・復元
- **テーマベースの資料作成**: マップテーマを活用した専門的な資料作成のサポート
- **プロジェクト管理強化**: 異なる表示設定の地図ビューを効率的に管理・切り替え

### Migration Notes
- テーマ機能はオプションです。既存のワークフローに影響はありません
- デフォルトでテーマ情報が含まれますが、パネルのチェックボックスで無効化可能
- テーマ情報が含まれたパーマリンクは若干長くなりますが、機能は大幅に向上します

## [V1.3.0] - 2025-10-08

### ⚠️ BREAKING CHANGES - Major Plugin Architecture Redesign

### Removed
- ダイアログ形式のUI（従来のポップアップウィンドウ）を完全に削除
- `qmap_permalink_dialog.py` と `qmap_permalink_dialog_base.ui` を廃止
- ダイアログ版のイベントハンドラを削除

### Added
- **パネル形式UI**: QGISの左側ドックエリアに常駐するパネルインターフェース
- **自動タブ化機能**: 既存の左側パネル（レイヤーパネル、ブラウザパネルなど）と自動的にタブ統合
- **完全多言語対応**: プラグインメッセージとパネルUIの両方を翻訳対応
- **インテリジェントパネル配置**: 優先度に基づいて最適なパネルとのタブ化を実行
- **フォールバック機能**: UIファイル読み込み失敗時の簡易パネル（`qmap_permalink_panel_simple.py`）

### Changed
- **UI形式**: ダイアログからドッキング可能パネルへの完全移行
- **ワークフロー**: 常時アクセス可能なパネルによる効率的な操作
- **翻訳システム**: 全メッセージを`tr()`関数で翻訳可能に変更
- **パネルサイズ**: 左側パネルに最適化されたサイズ（幅250-400px）
- **ユーザーフィードバック**: 操作結果の詳細なメッセージ表示

### Enhanced
- **日本語翻訳**: パネルUI要素を含む完全な日本語対応
- **エラーハンドリング**: より詳細なエラーメッセージと対処法の提示
- **デバッグ情報**: パネル作成・タブ化プロセスの可視化

### Technical Changes
- **アーキテクチャ**: `QDialog` から `QDockWidget` ベースに変更
- **パネルクラス**: `QMapPermalinkPanel` による統合UI管理
- **条件付きインポート**: パネル機能の可用性チェックとフォールバック
- **翻訳ファイル**: `QMapPermalinkPanelBase` コンテキストの追加

### Migration Notes
- 既存のダイアログベースのワークフローは自動的にパネル形式に移行
- 設定や機能に互換性はありますが、UI操作方法が変更されています
- パネルは手動で位置を調整可能（ドラッグ&ドロップ、フローティング対応）

## [V1.2.0] - 2025-10-05

### Added
- パーマリンクに回転 (rotation) パラメータを追加し、QGIS のキャンバスに回転を反映できるようにしました。
- 短いクエリパラメータ形式（x, y, scale, crs, rotation）でのパーマリンク生成と解析を導入しました。

### Changed
- パーマリンクの基準を「スケール (scale)」に統一しました（ズームは主に Google Maps 互換の補助情報として扱います）。
- Google Maps へのリンク生成時のズーム推定ロジックを改善しました（ユーザー提供のズーム⇄スケール表に基づくスナップ／外挿を実装）。
- パッケージ作成スクリプトを修正して、`metadata.txt` のメタデータキーの大文字小文字を保持するようにし、配布に `LICENSE` を含めるようにしました。
- README を更新し、スケールを標準とする旨と回転パラメータの使用例を追加しました。

### Fixed
- QGIS が `qgisMinimumVersion` を認識しない原因となっていたメタデータキーの取り扱いを修正しました。

## [V1.1.1] - 2025-10-05

### Changed
- プラグインのツールバー／メニューアイコンを新しいデザインに差し替え

## [V1.1.0] - 2025-10-05

### Added
- Google Maps連携: HTTPレスポンス内にクリック可能なGoogle Mapsリンクを自動生成
- パーマリンクJSONへ中心座標・ズーム情報を格納し、外部共有や他アプリ連携を強化

### Changed
- ズームレベル計算をWeb Mercator解像度ベースに刷新し、Google Mapsと精度を揃えました
- クリップボードコピー処理を安定化し、環境依存で空白になる問題を解消

### Fixed
- locationパラメータ使用時の座標解釈を改善し、Googleリンク生成失敗を防止

## [V1.0.0] - 2025-10-05

### Added
- Initial release of QMap Permalink plugin
- Generate permalinks for current map view (position, zoom level, CRS)
- Navigate to map view using permalink URLs
- Copy permalink URLs to clipboard
- Multi-language support (English, Japanese, French, German, Spanish, Italian, Portuguese, Chinese, Russian, Hindi)
- Qt5 compatibility with QGIS 3.44+
- Custom protocol support (qgis-permalink://)
- JSON-based permalink encoding
- External document integration capability (Excel, PDF, etc.)

### Features
- **Permalink Generation**: Create fixed links for specific map states
- **External Navigation**: Jump to map views from external documents
- **Multi-language UI**: Automatic language detection based on QGIS settings
- **Clipboard Integration**: Easy copying and sharing of permalink URLs
- **Cross-platform Support**: Compatible with Windows, macOS, and Linux

### Technical Specifications
- QGIS Minimum Version: 3.44
- QGIS Maximum Version: 3.999
- Required Qt Version: 5
- Programming Language: Python
- UI Framework: Qt Designer (.ui files)
- Translation System: Qt Linguist (.ts/.qm files)

### Directory Structure
```
qmap_permalink/
├── __init__.py
├── qmap_permalink.py
├── qmap_permalink_dialog.py
├── qmap_permalink_dialog_base.ui
├── metadata.txt
├── icon.png
└── i18n/
    ├── QMapPermalink_ja.ts
    ├── QMapPermalink_fr.ts
    └── [other language files]
```

### Known Limitations
- Requires active QGIS project for permalink generation
- Permalink URLs are specific to the coordinate reference system (CRS)
- External navigation requires QGIS to be running

### Dependencies
- Python standard modules
- QGIS API (qgis.core, qgis.gui, qgis.PyQt)
- Qt5 framework

---

**Note**: This is the initial release. Future updates will be documented here following the version format VA.B.C.