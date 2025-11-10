# 変更履歴（Changelog）

このファイルでは QMapPermalink プラグインの主な変更点を記録します。

記法は [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/) に基づき、
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) に準拠します。

## バージョン形式: VA.B.C

- **A**: QGIS コア更新やプラグインアーキテクチャ大幅変更などのメジャー変更
- **B**: UI 変更・新機能追加・中規模な機能拡張
- **C**: 軽微な不具合修正・小改善・プロファイル/プラグインの微修正

## メジャー節目（Major Milestones）

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

