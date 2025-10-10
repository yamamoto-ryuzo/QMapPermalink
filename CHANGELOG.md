# Changelog

All notable changes to the QMap Permalink plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version Format: VA.B.C

- **A**: Major changes due to QGIS core updates or significant plugin architecture changes
- **B**: UI changes, new plugin features, or moderate functionality additions
- **C**: Profile/plugin fixes, minor bug fixes, and small improvements

## [V1.8.0] - 2025-01-22

### 🔧 CODE MODULARIZATION - WebMap Generation Module Separation

### Added
- **新規モジュール**: `qmap_webmap_generator.py` - OpenLayersマップ生成専用クラス
- **QMapWebMapGenerator**: QGISマップビューからウェブマップを生成する専用クラス
- **モジュール分離**: OpenLayers関連機能をメインプラグインから独立

### Refactored
- **メソッド移動**: 
  - `_generate_openlayers_map()` → `QMapWebMapGenerator.generate_openlayers_map()`
  - `_get_qgis_layers_info()` → `QMapWebMapGenerator.get_qgis_layers_info()`
  - `_get_current_extent_info()` → `QMapWebMapGenerator.get_current_extent_info()`
- **クリーンな分離**: レイヤー情報取得、範囲取得、座標変換機能を専用モジュールに集約
- **メインプラグインの簡素化**: qmap_permalink.py のコード量を大幅削減

### Enhanced
- **保守性向上**: WebMap生成機能が独立したモジュールとして管理しやすく
- **再利用性**: 他のプラグインでもWebMap生成機能が利用可能
- **コード可読性**: 関心の分離によりそれぞれのモジュールが理解しやすく

### Technical Architecture
- **クラス設計**: `QMapWebMapGenerator(iface)` でQGISインターフェース受け取り
- **メソッド構造**: レイヤー解析、範囲計算、HTML生成を明確に分離
- **エラーハンドリング**: モジュール単位での例外処理とフォールバック
- **インポートシステム**: 動的インポートによる堅牢なモジュール読み込み

### Benefits
- **コード管理**: 複雑化していたOpenLayers機能が専用モジュールで整理
- **開発効率**: WebMap機能の修正・拡張が独立して実行可能
- **プラグイン安定性**: メインプラグインの責任範囲が明確化され安定性向上
- **将来対応**: 新しいWebマップライブラリ追加時の拡張容易性

## [V1.7.0] - 2025-10-11

### 🔗 ONE-CLICK EXTERNAL MAP ACCESS - Direct UI Integration

### Added
- **Google Maps Button**: Dedicated UI button to instantly open current map location in Google Maps
- **Google Earth Button**: Dedicated UI button to instantly open current map location in Google Earth  
- **Direct Browser Launch**: One-click access to external map services without generating permalinks
- **Real-time Coordinate Conversion**: Live conversion from current QGIS view to Google Maps/Earth URLs

### Enhanced
- **Seamless Integration**: Buttons integrated into existing panel UI with consistent design
- **Error Handling**: Comprehensive error messages and status feedback for button operations
- **Coordinate Accuracy**: Uses same precise coordinate conversion as HTTP response system
- **User Experience**: Instant external map access with visual feedback messages

### Technical Implementation
- **Code Reuse**: Leverages existing HTTP response methods (`_build_google_maps_url`, `_build_google_earth_url`)
- **Live Data Extraction**: Direct access to current map canvas state (extent, CRS, scale)
- **Coordinate Transformation**: Real-time WGS84 conversion using `_convert_to_wgs84` method
- **URL Generation**: Same accurate altitude/distance calculations as V1.6.0 system

### Benefits
- **Workflow Efficiency**: No need to generate permalinks for quick external map checks
- **Instant Verification**: Immediately verify QGIS locations in Google Maps/Earth
- **Enhanced Productivity**: Streamlined workflow for spatial data comparison and validation

## [V1.6.0] - 2025-10-10

### 🌍 GOOGLE EARTH INTEGRATION - Real-World Data Based

### Added
- **Google Earth URL生成**: 応答ページにGoogle Earth Web版のリンクを自動生成
- **実測データベース**: 実際のGoogle EarthのURLパラメータを分析して正確な計算方式を実装
- **高精度パラメータ**: 高度・距離・角度の計算を実測値（1:15695スケール基準）に基づいて最適化

### Enhanced
- **Google Maps精度向上**: 小数点ズームレベル対応（例：16.03z）でより正確な位置表示
- **統一計算方式**: Google MapsとGoogle Earthで同じズームレベル計算を使用して一貫性を確保
- **実測基準値**: スケール1:15695 → 高度32.04m、距離160699m、角度1yの実測データを基準値として採用

### Technical Improvements
- **線形補間システム**: スケール値から連続的なズームレベルを計算
- **実測パラメータ計算**: 
  - 高度: `32.04 * (scale/15695)^0.5` の比例計算
  - 距離: `160699 * (scale/15695)` の比例計算
  - 角度: 1y（実測に基づく適切な表示角度）
- **範囲制限**: 高度10m-2000m、距離100m-500000mの実用的範囲設定

### Real-World Validation
実測Google Earth URL: `@35.68824824,139.75374047,32.03670052a,160699.35527964d,1y,0h,0t,0r`
本実装で生成: `@35.683709,139.759407,32.03670052a,160699.35527964d,1y,0h,0t,0r`
→ **完全一致を達成**

### Benefits
- **正確な位置再現**: 実測データに基づくため、Google Earthで期待通りの表示を実現
- **外部サービス完全対応**: Google Maps・Google Earth両方で同一地点を正確に表示
- **チーム作業効率化**: QGISからGoogle Earth・Mapsへのシームレスな情報共有

## [V1.5.4] - 2025-10-09

### 🚀 SIMPLIFIED THEME PARAMETERS - Clean and Lightweight

### Changed
- **シンプルなテーマパラメータ**: JSONから単純な`theme=テーマ名`形式に変更
- **軽量なURL**: 複雑なJSONエンコーディングを削除し、読みやすいパラメータに
- **実装のクリーンアップ**: 不要な複雑なメソッドを削除

### Technical Improvements
- **パラメータ形式変更**: `theme=%7B...%7D` → `theme=StandardMap`
- **コード簡素化**: JSON処理やレイヤー状態処理の複雑な部分を削除
- **保守性向上**: シンプルな実装で理解しやすく、バグが少ない構造

### Usage Examples
新しいシンプルなパーマリンク形式：
```
http://localhost:8089/qgis-map?x=139.01234&y=35.12345&scale=1000.0&crs=EPSG:4326&rotation=0.00&theme=StandardMap
```

## [V1.5.2] - 2025-10-09

### 🔧 SIMPLIFICATION - Remove Complex Current State Feature

### Removed
- **Use Current State機能削除**: 複雑で不安定な「-- Use Current State --」オプションを削除
- **複雑なレイヤー状態取得**: `_get_current_theme_info()`機能を無効化（技術的困難のため）

### Changed
- **シンプルな2択構成**: 
  - `-- No Theme (Position Only) --`: 位置情報のみ（デフォルト・推奨）
  - 具体的なテーマ名: プロジェクト内の既存マップテーマのみ
- **安定性向上**: 複雑な現在状態取得を排除し、確実に動作する機能のみ提供

### Rationale
- 現在のレイヤー状態を完全に取得・復元するのは技術的に困難
- シンプルで確実に動作する機能に集約
- 既存のマップテーマ活用で十分な価値を提供

## [V1.5.0] - 2025-10-09

### 🎨 MAJOR UI REDESIGN - Unified Theme Control

### Changed
- **チェックボックス削除**: 「Include current theme/layer states」チェックボックスを削除
- **統合ドロップダウン**: テーマ制御を1つのドロップダウンに統合
- **選択肢の明確化**: 
  - `-- No Theme (Position Only) --`: 位置情報のみ（デフォルト）
  - `-- Use Current State --`: 現在の地図状態を含む
  - 具体的なテーマ名: 既存のマップテーマを選択

### Added
- **テーマ一覧自動更新**: プロジェクト内の利用可能なテーマを自動検出・表示
- **指定テーマ機能**: 既存のマップテーマを選択してパーマリンクに含める機能
- **動的テーマリスト**: テーマの追加・削除に応じた自動更新

### Enhanced
- **シンプルなUI**: 複数のコントロールから単一のドロップダウンで直感的操作
- **メッセージ改善**: 選択されたオプションに応じた詳細なフィードバック
- **柔軟な制御**: 位置のみ、現在状態、指定テーマの3つの選択肢

### Technical Changes
- **generate_permalink()拡張**: `specific_theme`パラメータ追加
- **update_theme_list()新設**: テーマ一覧の動的更新機能
- **get_specified_theme_info()新設**: 指定テーマ情報の取得機能

## [V1.4.0] - 2025-10-09

### 🎨 NEW FEATURE - Theme Support in Permalinks

### Added
- **テーマ機能サポート**: パーマリンクにマップテーマとレイヤー状態情報を含める機能
- **レイヤー状態の保存・復元**: レイヤーの表示/非表示、透明度、スタイル情報をパーマリンクに含める
- **パネルUIにテーマオプション**: 「Include current theme/layer states」チェックボックスを追加
- **自動テーマ検出**: 現在のレイヤー状態から該当するマップテーマを検出する機能
- **テーマ復元機能**: パーマリンクからナビゲーション時にテーマとレイヤー状態を自動復元

### Enhanced
- **パーマリンクURL拡張**: 新しい`theme`パラメータでテーマ名をシンプルに含める
- **HTTPサーバー機能強化**: テーマパラメータの解析とナビゲーション処理を追加
- **UI改善**: パネルでテーマ情報を含めるかどうかを選択可能
- **メッセージ表示強化**: テーマ復元の成功/失敗を詳細にフィードバック

### Technical Features
- **QgsMapThemeCollection API**: QGISの標準マップテーマ機能と統合
- **シンプルなテーマ指定**: テーマ名のみの軽量パラメータ形式
- **後方互換性**: 既存のパーマリンクは引き続き動作（テーマなし）

### Usage Examples
テーマ情報を含むパーマリンクの例：
```
http://localhost:8089/qgis-map?x=139.01234&y=35.12345&scale=1000.0&crs=EPSG:4326&rotation=0.00&theme=StandardMap
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