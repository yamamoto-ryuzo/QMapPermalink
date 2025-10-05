# Changelog

All notable changes to the QMap Permalink plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version Format: VA.B.C

- **A**: Major changes due to QGIS core updates or significant plugin architecture changes
- **B**: UI changes, new plugin features, or moderate functionality additions
- **C**: Profile/plugin fixes, minor bug fixes, and small improvements

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