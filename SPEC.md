# QMapPermalink — 仕様書

この仕様書は `README.md` と `CHANGELOG.md` の内容に基づき、機能別に整理した正式な仕様を提供します。
対象リポジトリ: `QMapPermalink`（ルートに配置）。

## 目的と範囲
- 目的: QMapPermalink プラグインの機能を明確に仕様化し、実装・運用・テストの基準を定める。
- 範囲: パーマリンク生成、組み込みHTTPサーバー（WMS/OpenLayers/MapLibre/WMTS）、外部連携（Google Maps/Earth）、テーマ適用、回転（ANGLE）処理、External Control の挙動、投影（CRS）ポリシー、セキュリティ/運用上の注意。

---
## 目次
1. 機能概要
2. API / エンドポイント仕様
3. パーマリンク形式とパラメータ
4. Map 表示生成（OpenLayers / MapLibre）
5. WMS / WMTS (タイルプロキシ) の挙動
6. WFS (Web Feature Service) の挙動
7. Google Maps / Google Earth 連携（生成とパース）
8. External Control（外部制御）のパース優先度と挙動
9. テーマ (Theme) サポート
10. 回転（ANGLE）パイプラインとパフォーマンス
11. 投影 (CRS) ポリシー
12. セキュリティ・運用上の注意
13. テスト・QA 手順
14. 実装ファイルと責務マッピング
15. 変更履歴の要約（V2 系ハイライト）

---
## 1. 機能概要
- パーマリンク生成: QGIS の現在表示（中心座標、scale、rotation、theme など）をHTTPパーマリンクとして生成・コピー・開く。
- 組み込み HTTP サーバー: `/qgis-map`, `/wms`, `/maplibre`, `/wmts/{z}/{x}/{y}.png` などのエンドポイントを提供し、ブラウザからインタラクティブ表示・静的画像取得を可能にする。
- Google 連携: Google Maps（@lat,lon,zoom）と Google Earth（@lat,lon,altitudea,distanced,...）のURLを生成。受信したこれらのURLをパースして QGIS 表示に変換可能。
- Theme サポート: `theme` パラメータによりマップテーマを仮想マップビューに適用してPNGを生成。
- External Control: 外部からの `/qgis-map` や `/wms` 含むリクエストを受け、許可された場合に自動で QGIS をナビゲートする。
- 回転処理: クライアントから `ANGLE` を受け取り、`ANGLE=0` は高速パス、非ゼロは拡張レンダリング（大きなレンダ→逆回転→クロップ→リサンプル）を行う。

---
## 2. API / エンドポイント仕様（高水準）
- GET `/qgis-map` — ブラウザ向けインタラクティブ HTML（OpenLayers / MapLibre）。クエリで `x,y,scale,crs,rotation,theme` を受け付ける。
- GET `/wms` — WMS 1.3.0 互換: `SERVICE=WMS&REQUEST=GetCapabilities` および `GetMap` をサポート。追加パラメータ: `ANGLE`。
- GET `/wmts/{z}/{x}/{y}.png` — WMTS 風タイルエンドポイント。内部で WMS レンダリングを利用して PNG を返す（タイル座標→bbox 変換を行う）。
- GET `/maplibre` — MapLibre 用 HTML を返却。可能ならローカル `wmts` タイルテンプレートを優先して埋め込む。
- POST/その他 — 管理用・内部 RPC は将来的に拡張可能（現状は主に GET ベース）。

共通的な振る舞い:
- サーバはデフォルトでポート範囲 8089-8099 を試行してバインドする。
- 外部アクセスを許可する場合はホストを 0.0.0.0 にバインドするが、運用ではファイアウォールで制限推奨。

---
## 3. パーマリンク形式とパラメータ
基本（推奨）
- `x` : 経度（または投影座標系の X）
- `y` : 緯度（または投影座標系の Y）
- `scale` : QGIS の scale（例: 1000.0）
- `crs` : 省略時は `EPSG:4326` として解釈。OpenLayers 出力は常に `EPSG:3857` に変換して表示。
- `rotation` : 表示の回転（度）
- `theme` : マップテーマ名（存在する場合に適用する）

例:
```
http://localhost:8089/qgis-map?x=139.01234&y=35.12345&scale=1000.0&rotation=0.00
```

短縮形式（プレゼン資料向け）
- 小数切り捨て等で `x=139&y=35&scale=1000.0` のように短くできる。

変換ルール:
- `scale` 指定があれば優先して適用。
- `zoom` は内部推定（Google Maps 用の推定）で用いるが、基本は `scale` を優先。

---
## 4. Map 表示生成（OpenLayers / MapLibre）
OpenLayers（`/qgis-map`）
- サーバは地図 HTML を生成し、WMS エンドポイントを相対パス `/wms` として参照する。クライアントは `view.rotation` を使って回転表示を行う。
- 右下の座標・スケール表示を埋め込み、埋め込み時に可能ならプロジェクトの投影定義と軸順情報を入れる（`qgis` から取得可能な場合）。

MapLibre（`/maplibre`）
- MapLibre 用の HTML を生成。V2.13.0 では pitch（傾き）を使った擬似3Dをサポートし、ツールバーに「斜め禁止」トグルを追加。
- WMTS タイルテンプレート（`/wmts/{z}/{x}/{y}.png`）を優先して埋め込める（ローカル実行時）。
- 生成されるスタイルで `maxzoom` のハードクランプは廃止（サーバが対応できるかは別途）。

テンプレート注意点:
- JavaScript オブジェクト中の波括弧はテンプレートで適切にエスケープすること（過去に f-string の不具合があったため）。

---
## 5. WMS / WMTS (タイルプロキシ) の挙動
WMS (`/wms`):
- GetCapabilities を返す（WMS 1.3.0 準拠）
- GetMap の必須パラメータ: `CRS`（または `SRS`）、`BBOX`、`WIDTH`、`HEIGHT`、`FORMAT`。
- `ANGLE` パラメータを受け付ける（デフォルト 0）。
- `BBOX` が無い、またはパース失敗の場合はエラー（MissingParameterValue 等）を返す。暗黙のフォールバックは行わない。

ANGLE パイプライン（詳細は §10）
- `ANGLE=0` : 高速パス — 指定の BBOX をそのまま map extent に設定して直接レンダリング。
- `ANGLE!=0` : 拡張パス — 外接 BBOX を計算して大きめにレンダ→画像空間で逆回転→中心クロップ→要求サイズにリサンプル。
- レンダリング最大サイズは内部でクランプ（デフォルト 4096 px 等）してメモリ暴走を防ぐ。

WMTS-like タイル (`/wmts/{z}/{x}/{y}.png`):
- タイル座標を BBOX に変換し、内部の WMS レンダラーを呼んで PNG を作成して返す。
- キャッシュは軽量実装では未実装だが、運用向けにはキャッシュ層（ファイル/メモリ/外部 CDN など）追加を推奨。

---

## 6. WFS (Web Feature Service) の挙動

### 日本語・多言語対応について

- QMapPermalink の WFS 機能および MapLibre クライアントは、日本語を含む多言語のレイヤ名・属性名・UI表示に完全対応しています。
- `/wfs-layers` エンドポイントの `title` フィールドや、`TYPENAME` には日本語（全角文字・記号含む）を利用可能です。
- クライアント側（MapLibre等）でIDやHTML要素属性として利用する場合は、`encodeURIComponent` などで一意かつ安全なIDに変換してください。
- JSON/HTML出力時はUTF-8エンコーディングを強制し、`ensure_ascii=False` で日本語がそのまま出力されます。
- 仕様上、レイヤ名・属性名・UIテキスト等に日本語・多言語を利用しても動作・表示・選択・検索に支障はありません。


### 概要
- QMapPermalink の WFS は QGIS プロジェクトのベクターレイヤーを外部アプリケーションに提供します。
- `/wfs-layers` エンドポイントはプロジェクトの `WFSLayers` エントリを読み、公開対象レイヤの JSON リストを返します。
- `GetCapabilities` は `/wfs-layers` と同じロジックを参照して FeatureTypeList を生成します（すなわち、プロジェクトの `WFSLayers` に登録されたレイヤのみが公開されます）。

### GetCapabilities
- 挙動: `WFSLayers` に列挙されたレイヤのみを `<FeatureTypeList>` として返す。`WFSLayers` が未定義または空の場合は空の `<FeatureTypeList>` を返す。
- レスポンス: `WFS_Capabilities` XML（version=2.0.0）を返す。
- 注意: 実装変更後は実行中の HTTP サーバ（QGIS プラグイン）を再起動する必要がある（実行中のプロセスはディスク上の変更を自動で読み込まないため）。

### GetFeature
- 入力パラメータ: `TYPENAME`（必須）、`OUTPUTFORMAT`（任意）、`BBOX`、`MAXFEATURES`、`SRSNAME` など。
- OUTPUTFORMAT 判定ロジック: 受け取った値に `gml` を含む文字列があれば GML を返却し、それ以外は GeoJSON を返却する（例: `application/gml+xml` → GML、`application/json` → GeoJSON）。
- GeoJSON: `QgsJsonExporter` 等を利用して GeoJSON を返す。
- GML: 簡易 GML を生成する実装を持つ。Point, LineString, Polygon に加え、簡易的な MultiPoint/MultiLineString/MultiPolygon の出力をサポートする（ポリゴンは外郭リングのみを扱う等の制限あり）。フルスキーマの互換性を要求するクライアントは事前に検証すること。

### DescribeFeatureType
- 挙動: 指定レイヤの属性スキーマを XML 形式で返す（既存の実装に準拠）。

### エラー応答
- WFS のエラーは OWS スタイルの ExceptionReport（XML）で返却する。基本形式:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExceptionReport version="1.3.0" xmlns="http://www.opengis.net/ows/1.1">
  <Exception exceptionCode="InvalidParameterValue" locator="TYPENAME">
    <ExceptionText>指定されたレイヤが見つかりません</ExceptionText>
  </Exception>
</ExceptionReport>
```

### 運用上の注意
- `GetCapabilities` と `/wfs-layers` が同じ `WFSLayers` を参照するため、公開設定はプロジェクト側で一元的に管理すること。
- 実装は簡易的な GML 出力を行うため、GML の厳密な互換性が必要なワークフローでは注意して検証すること。

## 7. Google Maps / Google Earth 連携（生成とパース）
生成
- Google Maps: `https://www.google.co.jp/maps/@{lat},{lon},{zoom}z` を生成。`zoom` は scale→zoom の推定を使う（小数点ズームを許容）。
- Google Earth: `https://earth.google.com/web/@{lat},{lon},{alt}a,{distance}d,{y}y,{heading}h,{tilt}t,{roll}r` を生成。実測データ（例: scale 15695 -> altitude 32.04m, distance 160699m, 1y）を基準に比例計算して `altitude` と `distance` を決定。

パース（受信）
- 優先度(高→低): Google Earth の `@...a,...d,1y` の `y` トークン → Google Maps の `@...,...m` / `...z` → 内部クエリパラメータ (`x,y,scale`) → 旧カスタムスキーム。
- Google Earth の `y`（m/px）があれば、画面 DPI を用いてスケールをより正確に逆算する。
- Google Maps の `m`（地表幅）トークンがあれば、キャンバス幅（ピクセル）に基づき scale を推定する。`zoom` のみなら `_estimate_scale_from_zoom` を使う。

注意:
- DPI / OS スケーリングの差異により微小な差が出るため、必要なら環境依存パラメータで補正可能。

---
## 8. External Control（外部制御）のパース優先度と挙動
- 機能: パネルの `External Control` が有効なら、外部から受信した URL を自動適用して QGIS をナビゲートする。
- パース優先度は上記 §6 に準じる。
- 動作:
  - 受信 URL をパースして `navigate_from_http` ルートを使い QGIS の表示を更新する。
  - パネル起動時に既に受信済みの URL がある場合は自動ナビゲートを実行（設定に依存）。
- セキュリティ: 自動ナビゲートは UX を上書きするため、明確な ON/OFF トグルを持ち、ログに受信元・実行時刻を記録することを推奨。

---
## 9. テーマ (Theme) サポート
- `theme` パラメータに指定されたマップテーマ名を仮想マップビューに適用して PNG を生成する。プロジェクト自体の状態を変更しない（仮想ビューを使用）。
- `theme` 値はプロジェクト内の既存マップテーマ名のみサポート。未存在の場合はエラーまたはフォールバック動作（No Theme として位置のみ適用）。
- スタイルのエクスポートでは QGIS バージョン差に備えて `exportNamedStyle` 等の呼び出しにフォールバックを用意。

---
## 10. 回転（ANGLE）パイプラインとパフォーマンス
契約（contract）:
- 入力: `BBOX`, `WIDTH`, `HEIGHT`, `ANGLE`（度）
- 出力: north-up PNG（クライアントは view.rotation を使って回転表示）
- 成功条件: `ANGLE=0` では高速にレンダリングされ、`ANGLE!=0` では見た目が正しい north-up PNG を返す。

パイプライン詳細:
1. 要求BBOX（A）を受け取る。
2. ANGLE が 0 の場合:
   - map_settings.extent = A; 直接レンダリング → PNG を返す。
3. ANGLE != 0 の場合:
   - A の外接回転対応 BBOX（B）を計算する（回転補正余白を含む）。
   - B を map_settings.extent に設定して大きな画像をレンダ（メモリ上でクランプ）。
   - 画像空間で -ANGLE の逆回転を適用。
   - 逆回転画像の中心から A に対応するピクセル矩形を中心クロップ。
   - クロップ結果を要求の WIDTH/HEIGHT にリサンプルして PNG を返す。

性能上の注意:
- 非ゼロ ANGLE は追加メモリと CPU を要する。大きなサイズや高倍率でのリクエストは上限（ピクセル数や幅・高さの上限）を設ける。
- デフォルトクランプ値（例: 4096 px 等）を推奨。ログで大きなリクエストを計測して運用で調整。

---
## 11. 投影 (CRS) ポリシー
- OpenLayers（ブラウザ表示）は常に `EPSG:3857` で提供する。
- WMS は複数 CRS を受け付け、要求 CRS に従ってレンダリングする。クライアント向けに変換が必要な場合はサーバ側で `EPSG:3857` に変換して返す（OpenLayers の一貫性のため）。
- `crs` を指定しないパーマリンクは `EPSG:4326` として解釈される。
- 座標変換は `QgsCoordinateTransform` を利用。プロジェクトによっては外部の proj 定義が必要となる場合がある。

---
## 12. セキュリティ・運用上の注意
- デフォルトで外部アクセスを許す設計だが、公開環境ではファイアウォールやプロキシでアクセス制御を厳格に行うこと。
- `External Control` を有効にしていると任意の外部URLで QGIS の表示が書き換わるため、信頼できるネットワーク内または追加の承認フローを用いることを強く推奨。
- WMS の `GetMap` で大きなレンダ要求が可能なため、認証・リクエストレート制限・サイズ上限を検討する。特に `ANGLE!=0` のリクエストは重い。
- ログを適切に出力し、受信元IP・タイムスタンプ・実行アクションを残す運用を推奨。

---
## 13. テスト・QA 手順
自動テスト候補:
- `qmap_permalink_server_manager.py` のユニットテスト: ポート選定・バインド挙動のモックテスト。
- URL パーサ（Google Maps/Earth/内部形式）の単体テスト（複数フォーマットのケース）。
- `wmts` タイル座標→BBOX 変換のユニットテスト。

手動テスト手順（QGIS 実環境）:
1. QGIS を起動しプラグインをインストール。
2. `External Control` を ON にして、別ホスト（または同一ホスト）から `/qgis-map?x=...&y=...&scale=...` にアクセスして QGIS がジャンプすることを確認。
3. `/wms?SERVICE=WMS&REQUEST=GetMap&...&ANGLE=0` と `ANGLE=30` を試し、期待する north-up PNG を得られることを確認。
4. MapLibre ページでピッチを切り替え、「斜め禁止」ボタンが効くことを確認。
5. Google Earth URL を生成してブラウザで開き、期待する表示（高度/距離/角度）が得られるか目視確認。

テスト注意:
- CI 環境では `qgis.core` や `PyQt5` が無いため、これらをモックするかローカルでの手動確認が必要。

---
## 14. 実装ファイルと責務マッピング
- `qmap_permalink.py` — メインプラグインロジック、ユーティリティ関数。
- `qmap_permalink_panel.py` — パネル UI 実装（ナビゲート、生成、外部制御トグル等）。
- `qmap_permalink_panel_base.ui` — Qt Designer の UI 定義。
- `qmap_permalink_server_manager.py` — 組み込み HTTP サーバーの起動/停止・ルーティング（WMS/Map endpoints）。
- `qmap_webmap_generator.py` — OpenLayers / MapLibre HTML テンプレートの生成ロジック。
- `qmap_wmts_service.py` / `qmap_wms_service.py` — WMS/WMTS 関連のヘルパー（タイル変換、BBOX 計算など）。
- `qmap_permalink_panel.py` から `navigate_from_http` / `navigate_to_coordinates` を呼び出す流れ。

---
## 15. 変更履歴の要約（V2 系ハイライト）
- V2.0.0: WMS サポートと外部アクセス（0.0.0.0 バインド）を追加。
- V2.6.0: 投影定義と軸順情報を生成 HTML に埋め込み、座標表示の精度向上。
- V2.8.0: External Control の自動ナビゲート追加。
- V2.10.0: Google Earth `y` トークン対応とスケール推定の改善。
- V2.12.0: テーマ対応 WMS 出力（仮想マップビュー）。
- V2.13.0: WMTS タイルエンドポイント、MapLibre 改善（pitch トグル、zoom clamp 解除）。

---
## 付録: 代表的なサンプル URL
- OpenLayers（位置）:
  `http://localhost:8089/qgis-map?x=139.7594&y=35.6837&scale=1000.0`
- WMS GetMap（ANGLE=0）:
  `http://127.0.0.1:8089/wms?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&CRS=EPSG:3857&BBOX=<minx,miny,maxx,maxy>&WIDTH=800&HEIGHT=600&FORMAT=image/png&ANGLE=0`
- WMTS タイル:
  `http://localhost:8089/wmts/15/17500/10600.png`
- Google Earth 例:
  `https://earth.google.com/web/@35.683709,139.759407,32.0367a,160699.3553d,1y,0h,0t,0r`

---
## 完了条件 / 次のステップ
- この `SPEC.md` をレビューして承認を得る。
- 承認後、必要に応じて `qmap_permalink` の各モジュールに単体テストを追加する（特に URL パーサと WMTS タイル計算）。
