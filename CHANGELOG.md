# Changelog

All notable changes to the QMap Permalink plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version Format: VA.B.C

- **A**: Major changes due to QGIS core updates or significant plugin architecture changes
- **B**: UI changes, new plugin features, or moderate functionality additions
- **C**: Profile/plugin fixes, minor bug fixes, and small improvements

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