# geo_webview — 仕様書

この仕様書は `README.md` と `CHANGELOG.md` の内容に基づき、機能別に整理した正式な仕様を提供します。
対象リポジトリ: `geo_webview`（ルートに配置）。

## 目的と範囲
- 目的: geo_webview プラグインの機能を明確に仕様化し、実装・運用・テストの基準を定める。
- 範囲: パーマリンク生成、組み込みHTTPサーバー（WMS/OpenLayers/MapLibre/WMTS）、外部連携（Google Maps/Earth）、テーマ適用、回転（ANGLE）処理、External Control の挙動、投影（CRS）ポリシー、セキュリティ/運用上の注意。

---
## 目次
1. 機能概要
2. API / エンドポイント仕様
3. パーマリンク形式とパラメータ
4. Map 表示生成（OpenLayers / MapLibre）
5. WMS の挙動
6. WMTS (タイルプロキシ) の挙動
7. WMS/WMTS の並列処理と高速化
8. WFS (Web Feature Service) の挙動
9. Google Maps / Google Earth 連携（生成とパース）
10. External Control（外部制御）のパース優先度と挙動
11. テーマ (Theme) サポート
12. 回転（ANGLE）パイプラインとパフォーマンス
13. 投影 (CRS) ポリシー
14. セキュリティ・運用上の注意
15. テスト・QA 手順
16. 実装ファイルと責務マッピング
17. 変更履歴の要約（V2/V3 ハイライト）

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
 - 初期 HTML は常に相対パス `/maplibre-style`（typename なし）を style URL に設定し、WMTS ラスタのみのベーススタイル（sources:`qmap`, layers:`qmap`）をロードする。
 - 公開 WFS レイヤはクライアント側 `qmap_postload.js` が `/wfs?SERVICE=WFS&REQUEST=GetCapabilities` を取得後、各レイヤ毎に `/maplibre-style?typename=<QGIS layer.id()>` をフェッチして QGIS 由来スタイルを“注入”する。
 - スタイル注入成功時: QGIS シンボルを変換した MapLibre レイヤ群（fill/line/circle/symbol）が追加される。ポリゴンは fill α=0（ブラシなし）なら fill レイヤを生成せず line レイヤのみ。線幅・ポイントサイズは mm/pt/px を px に正規化（mm→×3.78, pt→×1.333...）。
 - 失敗時（404, タイムアウト等）: GetFeature で GeoJSON を取得し最小限の中立フォールバック表示（Point: 白円+灰枠, Line: 細灰線, Polygon: 灰線のみ）。フォールバックは QGIS スタイル再現を意図せず “データ存在” の指標。
 - GeoJSON にはスタイル情報を含めない（データ/スタイル分離）。常に `/maplibre-style` エンドポイント経由で動的取得することで QGIS 側スタイル変更の即時反映とキャッシュ効率を確保。
 - レイヤ ID は `<sourceId>_<type>_<index>` の決定的命名で衝突回避。`layout.visibility` は明示的に `'visible'`。
 - ベーススタイルは相対 URL 利用によりサーバ起動ポート可変（8089〜8099）でも透過的に利用可能。
 - Pitch（傾き）操作は UI ボタン「斜め許可/斜め禁止」で切替。初期状態は禁止（pitch=0 を強制）。
 - `maxzoom` のハードクランプは撤廃。高ズーム要求の可否はサーバ側レンダリング能力に依存。
 テンプレート注意点:
 - 生成処理内で f-string エスケープ起因の二重波括弧を単一波括弧へ正規化済み。
 - スタイル URL は絶対パス固定を避け相対パスを使用。

---
## 5. WMS の挙動
WMS (`/wms`):
- GetCapabilities を返す（WMS 1.3.0 準拠）
- GetMap の必須パラメータ: `CRS`（または `SRS`）、`BBOX`、`WIDTH`、`HEIGHT`、`FORMAT`。
- エラー応答: WMS のエラーは OWS スタイルの `ExceptionReport`（XML）で返却するよう改善しました。これにより多くの OGC クライアントが期待する形式で詳細なエラー情報を受け取れます。
- `ANGLE` パラメータを受け付ける（デフォルト 0）。
- `BBOX` が無い、またはパース失敗の場合はエラー（MissingParameterValue 等）を返す。暗黙のフォールバックは行わない。

ANGLE パイプライン（詳細は 回転（ANGLE）パイプライン節 を参照）
- `ANGLE=0` : 高速パス — 指定の BBOX をそのまま map extent に設定して直接レンダリング。
- `ANGLE!=0` : 拡張パス — 外接 BBOX を計算して大きめにレンダ→画像空間で逆回転→中心クロップ→要求サイズにリサンプル。
- レンダリング最大サイズは内部でクランプ（デフォルト 4096 px 等）してメモリ暴走を防ぐ。

### ラベリングと QML 式のサーバ側評価（`is_layer_visible()` サポート）

- 概要: サーバ側レンダリングでは QGIS GUI 上の表現（QML 内の条件式）とサーバ実行時の評価コンテキストが異なるため、クライアント要求に合わせて `is_layer_visible('レイヤ名')` のような式をサーバ側で評価できる仕組みを実装しています。これは GetMap リクエストの `LAYERS` 指定やキャンバスの表示状態に基づき、式内の `is_layer_visible('...')` をリテラル `1`/`0` に書き換えて評価させることで、QGIS 側でのラベル付与/非表示ロジックを WMS 出力に反映します。
- 実装: 現状は正規表現ベースの前処理パスで QML 内の `is_layer_visible\('...'\)` パターンを検出し、要求された `LAYERS` やキャンバスのレイヤ表示状態に応じて `1`（true）/`0`（false）に書き換えます。書換処理は `geo_webview/wms_service.py` に実装済みです。
- 追加のエンドポイントオプション: `LABELS` パラメータを用意し、クライアントが強制的に特定フィールドで一時的にラベルを有効化してレンダリングできるようにしています（レンダリング後は元の状態へ復元します）。これにより、プロジェクトにラベルが永続的に保存されていないケースでも WMS 出力にラベルを反映できます。
- 制約と注意点:
  - 現時点の書換は文字列マッチング（正規表現）に依存するため、複雑な式構造やQMLの微妙な記法差によってはカバーできないケースがあります。
  - 書換のマッチは主に表示名（label/display name）に基づいています。将来的にはレイヤ ID での解決や QML パーサを用いた堅牢化を推奨します。
  - 長期的な安定解としては、ラベル本文をサーバ側で評価可能な属性に永続化するか、クライアント側から `LABEL_EXPR` のような明示的なラベル式を渡す API 拡張を検討してください。
  - 実装済みのファイル: `geo_webview/wms_service.py`（QML 書換・style override・`LABELS` パラメータ処理）

## 6. WMTS (タイルプロキシ) の挙動
WMTS-like タイル (`/wmts/{z}/{x}/{y}.png`):
- タイル座標を BBOX に変換し、内部の WMS レンダラーを呼んで PNG を作成して返す。
- キャッシュは軽量実装では未実装だが、運用向けにはキャッシュ層（ファイル/メモリ/外部 CDN など）追加を推奨。

WMTS GetCapabilities と TileMatrix
- サーバは最小限の WMTS GetCapabilities 応答を提供する。出力には少なくとも以下を含める:
  - レイヤ識別子（Identifier）とタイトル
  - `ResourceURL` エントリ（`resourceType="tile"`、`format="image/png"`、`template` 属性にタイルテンプレートを指定）
  - `TileMatrixSet` セクション（`Identifier`、`SupportedCRS`、および各 `TileMatrix`）

`TileMatrix` は各ズームレベルについて次を含める:
  - `Identifier`（ズームレベル）
  - `ScaleDenominator`（適切な解像度から計算）
  - `TopLeftCorner`（WebMercator では `-20037508.342789244 20037508.342789244`）
  - `TileWidth` / `TileHeight`（本実装は 256）
  - `MatrixWidth` / `MatrixHeight`（各ズームで `2**z`）
- 実務上は完全な WMTS 仕様を満たすためにさらに `OperationsMetadata` 等を含めることが望ましいが、本実装はクライアント互換性を優先して `ResourceURL` と `TileMatrix` を提供することで多くのクライアントが利用可能になる。

### 補足: 実装上の最新修正 (2025-11-16)

- 本リポジトリでは軽量な「WMTS 風」ハンドラを提供しており、以下の点を優先して実装・改善を行いました:
  - GetCapabilities 応答を OWS 名前空間や `OperationsMetadata`、`ResourceURL`、`TileMatrixSet` / `TileMatrix`、および `TileMatrixSetLimits` を含む形で拡張し、より多くのクライアントとの互換性を高めました。
  - `ResourceURL` と `ServiceMetadataURL` にはサーバ側で算出した短い identity（`?v=<identity_short>`）を付与するオプションを導入し、クライアント側でタイルのキャッシュ更新を検知できるようにしています。identity は表示中のレイヤ ID とスタイル ID を組み合わせたハッシュに基づきます（実装関数名: `_get_identity_info()`）。
  - 既存の利便性のため、必ず `/wmts/{z}/{x}/{y}.png`（XYZ）パスベースのエンドポイントを提供します。これは WMTS ResourceURL のテンプレートとは別に維持され、MapLibre 等のクライアントが直接参照できます。
  - TMS 互換のため `tms=1`（または `tms=true`）クエリパラメータをサポートし、必要に応じて内部で `y` を反転してレンダリングします。

- 実装上の注意点と最近の修正:
  - GetCapabilities を生成する際に大きなインライン文字列を扱うため、編集でインデントや波括弧の扱いに注意が必要です（実際に編集時にインデント不整合が発生したため修正パッチを適用済み）。
  - `geo_webview/wmts_service.py` 側で次の補強を行いました: `_validate_tile_coords` ヘルパの追加、GetCapabilities 分岐からの不適切なコード断片削除、`z/x/y` のローカル変数初期化、コメント内の波括弧エスケープ等。
  - これらの変更を反映するには、プラグインの HTTP サーバー（または QGIS）を再起動する必要があります。稼働中の Python プロセスはディスク上のモジュールを自動で再読み込みしないためです。

### GetCapabilities の検証

- リポジトリに検証用スクリプト `tools/validate_wmts_capabilities.py` を追加しています。ローカルの実行手順は次の通りです。

  1. GetCapabilities をダウンロードして一時ファイルに保存します（スクリプトが自動で行います）。
  2. XSD による検証を行うには `lxml` をインストールするか、`xmlschema` によるフォールバックを使います。

  推奨コマンド（PowerShell）:
  ```powershell
  # lxml を使う（推奨）
  python -m pip install lxml
  python .\tools\validate_wmts_capabilities.py --url "http://localhost:8089/wmts?SERVICE=WMTS&REQUEST=GetCapabilities"

  # あるいは xmlschema を使う（ビルド不要）
  python -m pip install xmlschema
  python -c "import xmlschema; xmlschema.XMLSchema('http://schemas.opengis.net/wmts/1.0/wmtsGetCapabilities_response.xsd').validate(r'C:\\Users\\<you>\\AppData\\Local\\Temp\\wmts_cap_<id>.xml'); print('validation OK')"
  ```

  - 検証中に HTTP 500 や Import/Indentation のトレースバックが出る場合は、QGIS の Message Log を確認してください（カテゴリ: `geo_webview`）。プラグインの初期化時にモジュールの文法エラーや例外が発生すると WMTS サービスが None となり HTTP 501 を返すため、トレースバックの共有が迅速な修正に役立ちます。

---

TMS（y 反転）オプション
- 背景: 一部のタイル配列（TMS）ではタイルの Y 起点が bottom-left（左下）であるのに対し、一般的な XYZ（slippy map）では top-left（左上）を起点とする。
- 影響: クライアントとサーバで起点解釈が一致しないと、同じ z/x/y で上下逆の領域が返却される。
- 本実装の対応: クエリパラメータ `tms=1`（または `tms=true`）を受け付けると、受信した `y` を内部処理用に反転して（inverted_y = (2**z - 1) - y）から BBOX 計算を行う。これにより TMS クライアントからのリクエストにも正しく応答可能。
- 例:
  - URL パス方式: `GET /wmts/3/2/1.png?tms=1` は内部で y を反転してレンダリングする（z=3 の場合 inverted_y = 7 - 1 = 6 に相当する領域を返す）。
  - KVP 方式: `GET /wmts?REQUEST=GetTile&TILEMATRIX=3&TILECOL=2&TILEROW=1&tms=1` として同様に反転される。
- 注意点:
  - キャッシュを導入する場合は `tms` フラグをキャッシュキーに含める（tms=0/1 で異なるタイル結果となるため）。
  - Capabilities の `TileMatrix.TopLeftCorner` は top-left を示すので、可能なら README や Capabilities の注記で `tms` オプションの存在を明示することを推奨する。

WMTS キャッシュと identity（V3.1.0）
- 概要: V3.1.0 では、WMTS タイルのキャッシュを表示中のレイヤ ID とスタイル ID を組み合わせた短い identity（sha1 の先頭12文字）で分離し、GetCapabilities に `?v=<identity>` を付与してクライアントが変化を検知できるようにしました。これによりサーバ側のレイヤ・スタイル変更時に WMTS タイルのみを効率的に更新できます。
- identity の算出方法（サーバ側）: 表示中のレイヤ識別子（layer ID）と各レイヤに適用されるスタイル識別子（style ID）を決定的に組み合わせた JSON を sha1 ハッシュ化し、その先頭 12 文字（short hash）を `identity_short` として使用します。実装上は `_get_identity_info()` のような関数でこの情報を生成します。
- GetCapabilities での通知:
  - サーバは `ResourceURL` のタイルテンプレートおよび `ServiceMetadataURL` 等に `?v=<identity_short>` を付与して返します。これによりクライアントは現在サーバが提供している identity を検出できます。
- サーバ側のキャッシュ配置（実装例）:
  - キャッシュは identity 毎のディレクトリに分離して格納する（例: `.cache/wmts/<identity_short>/...`）。
  - キャッシュキーには identity の他に `tms` 等の挙動を変えるフラグや出力フォーマットを含めることを推奨します。
- クライアント（MapLibre）側の推奨挙動:
  - 画面移動（`moveend`）等のタイミングで `/wmts?SERVICE=GetCapabilities` を再取得し、`?v=` の値（または ServiceMetadata の identity）を比較して変化を検知します。
  - identity が変化している場合は、可能な限り「WMTS タイルソースのみ」を差し替えて新しいタイルを取得する（全スタイル再読み込みは避ける）。これにより WFS の重複登録やスタイル注入の副作用を防げます。
  - MapLibre の実装注意点として、`removeSource` を実行する際にそのソースを参照する `layer` が残っていると例外が出るため、安全に差し替えるには以下の順序が推奨されます:
    1. 参照するレイヤを一時的に保存して `removeLayer` で削除
    2. `removeSource` でソースを削除
    3. 新しいタイルテンプレート（`?v=<new>` を含む）で `addSource` を実行
    4. 保存しておいたレイヤを同じ順序・設定で `addLayer` して復元
  - あるいは、タイル URL に `?v=` を埋め込み、ソースを置き換えずに URL のバージョンパラメータだけを変えてキャッシュバイパスする工夫でも可（MapLibre のキャッシュ挙動に依存）。
- 運用上の注意:
  - identity の粒度（どの属性を style ID と見なすか）によっては不要なキャッシュバストや逆に更新を検知できないケースがあるため、サーバ側の identity 計算ロジックは十分ドキュメント化し、必要であれば style ID の生成ルールを固定することを推奨します。
  - GetCapabilities に `?v=` を埋め込むことで CDN やブラウザキャッシュを利用しつつ、identity 変化時に確実に新規タイルを取得できます。

## 7. XYZ タイル (XYZ Tiles)

概要: `/xyz/{z}/{x}/{y}.png` はスリッピーマップ形式の XYZ タイルパスを提供します。
- 実装: サーバは既存の WMTS タイルプロキシ実装を再利用して `/xyz` パスを受け付けます。内部的にはタイル座標を WebMercator の BBOX に変換し、WMS レンダラーで画像を生成します。
- 用例: `GET /xyz/15/17500/10600.png` は `GET /wmts/15/17500/10600.png` と同等に扱われます。
- GetCapabilities: WMTS の `ResourceURL` には `?v=<identity_short>` を付与する実装を継続し、クライアントは identity によるキャッシュバーストを利用できます。`/xyz` はクライアント向けに簡潔な直接参照パスとして案内されます。
- TMS 互換: クエリパラメータ `tms=1` をサポートし、必要に応じて `y` を反転してレンダリングします。

実装上の注意:
- `/xyz` は WMTS のエイリアスであり、キャッシュキー・identity ロジック・tms フラグは WMTS と同一の扱いです。
- クライアント（MapLibre 等）は `/xyz/...` を直接参照してタイルを取得できますが、GetCapabilities による `?v=` を用いた運用（キャッシュ無効化）も推奨します。

---

## 8. WMS/WMTS/XYZ の並列処理と高速化

目的: 高負荷のタイル/マップレンダ要求に対してレスポンス性能を改善し、安定して多数の同時接続をさばけるようにするための方針と実装上の注意点を示す。

設計上の注意
- **QGIS API のスレッド安全性**: QGIS の多くのオブジェクトはスレッド非安全であり、メインスレッドや各プロセス内でのみ安全に操作できる。よってレンダリング並列化はスレッドではなく**プロセス単位（ワーカープロセス）**で行うことを推奨する。各ワーカーは独立した QgsApplication/QgsProject を保持して再利用することでプロジェクト読み込みオーバーヘッドを低減できる。
- **プロセスプールの推奨構成**: CPU コア数に基づき `max_render_workers = max(1, cpu_count() - 1)` を初期値とし、メモリや QGIS プラグインの特性に合わせて調整する。ワーカーが多すぎるとメモリスワップを招くため注意。

並列化パターン
- **I/O バウンド（外部 WMS 参照や WFS フェッチ）**: `asyncio` / `aiohttp` やスレッドプール（`concurrent.futures.ThreadPoolExecutor`）で並列化し、HTTP 接続は `requests.Session` や `aiohttp.ClientSession` などでコネクションプーリングする。タイムアウト・最大同時接続数を設定する（例: `max_pool_connections=20`, `timeout=10s`）。
- **CPU/レンダリングバウンド**: QGIS レンダリングは CPU とメモリを消費するため、`multiprocessing.Process` や `multiprocessing.Pool` でワーカーを立て、レンダリング要求をキュー（例: `multiprocessing.Queue` / `multiprocessing.SimpleQueue`）に投入して処理する。各ワーカーはワークループ内で QgsProject を開いたまま使い回すことで毎リクエストの初期化コストを回避する。
- **ハイブリッド**: HTTP リクエスト受け付けは非同期サーバ（例: `aiohttp`）で行い、レンダリングはプロセスプールにディスパッチするアーキテクチャが高いスループットを実現する。

キャッシュ戦略
- **タイルキャッシュ（on-disk / メモリ）**: `identity` ベースのディレクトリ分離と LRU/TTL を組み合わせる。キー例: `sha1(identity_json)+_tms{0|1}_fmt_png_w{W}_h{H}`。
- **HTTP レスポンスキャッシュヘッダ**: `Cache-Control: public, max-age=86400` や `ETag` を付与してブラウザ/CDN キャッシュを活用する。GetCapabilities に付与する `?v=` を利用してキャッシュを安全にバストする。
- **シード（事前生成）**: 高アクセス領域を事前にバッチで生成（シード）しておく。タイルシードは並列ワーカーで並行実行し、I/O と CPU 負荷を平坦化する。

接続・ネットワーク最適化
- **HTTP Keep-Alive / 接続プール**: 外部 WMS 取得や CDN との通信でセッションを再利用する。短時間で多くの小さな接続を張らない。
- **タイムアウト / 再試行**: 外部リクエストに対しては短めのタイムアウト（例: 5〜10秒）と指数バックオフの再試行（最大 2 回）を行う。失敗はフォールバック（低解像度タイルや空白）で応答するポリシーを用意。

レンダリング固有の最適化
- **要求ピクセル数のクランプ**: `WIDTH * HEIGHT` の最大ピクセル数を制限する（例: 4096*4096 の領域は超えない）。ANGLE != 0 の場合は大きめの内部レンダを行うため、さらなるクランプを適用する。
- **タイルサイズとフォーマット**: タイルは原則 `256x256`。写真や背景には JPEG（`image/jpeg`）を使い、アルファが必要なレイヤは PNG を使う。圧縮率を適切に設定することで転送バイト数を削減。
- **レンダリングパラメータの再利用**: 同一プロジェクト内で複数リクエストが同時に来る場合は `map_settings` やスタイル情報を共有して再計算コストを下げる（スレッド間共有はせずプロセス内でキャッシュ）。

負荷制御と安定化
- **キューと優先度**: レンダリング要求を優先度付きキューに入れ、短時間で完了する小さなリクエストを優先することで平均応答時間を改善する。
- **レート制限**: IP/APIキー 単位でのレート制限を設ける。過負荷時は 503 を返してクライアントに再試行を促す。
- **バックプレッシャー**: ワーカープールが枯渇している場合は受け付け（accept）数を調整するか、新規リクエストを拒否してクライアントに再試行させる（キューが溢れないようにする）。

運用・監視
- **メトリクス**: レスポンスタイム、レンダ時間、キュー長、キャッシュヒット率、メモリ使用量、ワーカー数などを収集する（Prometheus 等を推奨）。
- **ログ**: 長時間処理リクエストや失敗を重要ログとして出力し、アラートを設定する。

実装例（geo_webview 向け推奨）
- プラグイン起動時に `N` 個のレンダーワーカー（プロセス）を生成。各ワーカーは QgsApplication とプロジェクトをロードして待機する。
- HTTP 層は軽量非同期サーバで受け、レンダ要求はキューに入れてワーカーへ委譲。ワーカーは結果をキャッシュへ保存し、呼び出し元へパススルーする。
- `qmap_wmts_service.py` / `qmap_wms_service.py` に設定可能なパラメータを追加:
  - `max_render_workers` (default: cpu_count() - 1)
  - `max_io_workers` (default: 20)
  - `cache_dir` (default: `.cache/wmts/`)
  - `tile_size` (default: 256)
  - `request_timeout_s` (default: 10)
  - `retry_count` (default: 2)

注意事項
- QGIS のバージョンやプラットフォーム依存の挙動によりプロセス化の方法が影響を受ける。プラグイン側でワーカー初期化時の QGIS 環境設定（プロバイダのロード順、プラグイン設定）を固定化すると再現性が高まる。
- ANGLE パイプライン等の大画像レンダはワーカー1つあたりのメモリ要求が増えるため、ワーカー数は必ずメモリ予算に基づいて設定する。テストで最大メモリ使用量を確認すること。

実装上の既定値（現状）
- **WMS 最大画像サイズ**: `4096 x 4096` ピクセル（`qmap_wms_service.py` 内の `max_dimension = 4096`）。この値を超える `WIDTH`/`HEIGHT` の要求は 400 系エラーで拒否される。
- **WMS レンダリング タイムアウト**: `30` 秒（`qmap_wms_service.py` の `_execute_parallel_rendering` 内で `QTimer` により設定）。タイムアウト時はレンダジョブをキャンセルしてエラー扱いとなる。
- **WMTS タイルサイズ（TileWidth/TileHeight）**: `256`（`qmap_wmts_service.py` 内の `tile_size = 256` を既定として GetCapabilities 出力や座標変換で使用）。
- **WMTS キャッシュディレクトリ**: モジュール相対の `.cache/wmts/`（`qmap_wmts_service.py` 内で `os.path.join(os.path.dirname(__file__), '.cache', 'wmts')` により作成）。identity 毎のサブディレクトリに分離される。
- **内部推奨値（実装済み）**: 本仕様で設計上の推奨値として示している各パラメータは、実装側で環境変数またはコンストラクタ引数により上書き可能になりました。利用可能な設定と対応する環境変数は以下の通りです。
  - `max_render_workers` — (計算: `cpu_count() - 1`、ただし最低値 `6` を採用)。
  - `max_io_workers` — (デフォルト: 20)、環境変数: `QMAP_MAX_IO_WORKERS`
  - `wmts_prewarm_workers` — (計算: `cpu_count() - 1`、ただし最低値 `6` を採用)。
  - `request_timeout_s` — (デフォルト: 10 秒)、環境変数: `QMAP_REQUEST_TIMEOUT_S`
  - `retry_count` — (デフォルト: 2)、環境変数: `QMAP_RETRY_COUNT`
  - `max_image_dimension` — (デフォルト: 4096)、環境変数: `QMAP_MAX_IMAGE_DIMENSION`（WMS 出力ピクセル上限）
  - `render_timeout_s` — (デフォルト: 30 秒)、環境変数: `QMAP_RENDER_TIMEOUT_S`（レンダ待機タイムアウト）
  - `tile_size` — (デフォルト: 256)、環境変数: `QMAP_TILE_SIZE`（WMTS タイル幅/高さ）
  - `cache_dir` — (デフォルト: モジュール相対 `.cache/wmts/`)、環境変数: `QMAP_CACHE_DIR`（相対パス可）

  これらの設定は `qmap_wms_service.py` および `qmap_wmts_service.py` のコンストラクタ引数からも渡せます。環境変数が存在する場合はそれを優先し、未指定時は上記のデフォルト値が使われます。運用環境でのチューニング（ワーカー数やタイムアウト、タイルサイズの変更）はこれらの設定を用いて行ってください。

この章は実装指針を提供するものであり、運用環境・アクセスパターンに応じて各設定値を調整してください。


---

## 9. WFS (Web Feature Service) の挙動

### 日本語・多言語対応について

- geo_webview の WFS 機能および MapLibre クライアントは、日本語を含む多言語のレイヤ名・属性名・UI表示に完全対応しています。
- `/wfs-layers` エンドポイントの `title` フィールドや、`TYPENAME` には日本語（全角文字・記号含む）を利用可能です。
- クライアント側（MapLibre等）でIDやHTML要素属性として利用する場合は、`encodeURIComponent` などで一意かつ安全なIDに変換してください。
- JSON/HTML出力時はUTF-8エンコーディングを強制し、`ensure_ascii=False` で日本語がそのまま出力されます。
- 仕様上、レイヤ名・属性名・UIテキスト等に日本語・多言語を利用しても動作・表示・選択・検索に支障はありません。


### 概要
- geo_webview の WFS は QGIS プロジェクトのベクターレイヤーを外部アプリケーションに提供します。
- `/wfs-layers` エンドポイントはプロジェクトの `WFSLayers` エントリを読み、公開対象レイヤの JSON リストを返します。
- `GetCapabilities` は `/wfs-layers` と同じロジックを参照して FeatureTypeList を生成します（すなわち、プロジェクトの `WFSLayers` に登録されたレイヤのみが公開されます）。

### Phase 1 高速化 (v3.4.0)

**レスポンスキャッシュ機構**:
- 同一リクエストを5分間メモリキャッシュ
- キャッシュキー: MD5(layer_id + bbox + srs_name + max_features + output_format)
- キャッシュヒット時: < 5ms (通常の40倍高速)
- 自動クリーンアップ: 10%の確率で期限切れエントリを削除
- スレッドセーフ: `threading.Lock()`による排他制御

**地物クエリ最適化**:
- `QgsFeatureRequest.ExactIntersect`: 空間インデックスを活用した高速検索
- イテレータベース取得: `layer.getFeatures(request)`で効率的な地物取得
- 最適化されたLIMIT処理: イテレータ内でカウントして無駄な取得を回避
- メモリ効率向上: 大量地物でもメモリ使用量を抑制

**パフォーマンスログ**:
- キャッシュヒット: `⚡ WFS Cache HIT: {typename} (saved ~{elapsed}ms)`
- キャッシュミス: `💾 WFS Cache MISS: {typename} ({count}地物, {elapsed}ms) - キャッシュに保存`
- クリーンアップ: `🧹 WFS Cache: {count}個の期限切れエントリを削除`

### MapLibre スタイル注入フロー
1. ベーススタイル（WMTS のみ）を `/maplibre-style` でロード。
2. 公開 WFS レイヤ一覧を GetCapabilities から取得。
3. 各レイヤ毎に `/maplibre-style?typename=<layer.id()>` をフェッチ。
  - 成功: 変換済みスタイルレイヤ（fill/line/circle）が追加。ブラシなしポリゴンは fill レイヤ生成なし。
  - 失敗: GetFeature で GeoJSON のみ取得し最小限フォールバック表示（中立スタイル）。
4. 両ケースでラベルレイヤ（symbol, text-field=['get','label']）を追加。
5. 追加レイヤ ID を `wmtsLayers` に登録し UI で表示/非表示制御。

用語: スタイル注入＝QGIS スタイル成功取り込み。フォールバック＝最小限中立表示。ブラシなし＝QGIS fill α=0。

### `/maplibre-style` エンドポイント
- `GET /maplibre-style` : ベース WMTS ラスタのみ。
- `GET /maplibre-style?typename=<QGIS layer.id()>` : WMTS + 指定レイヤ GeoJSON + 変換スタイルレイヤ。
- 404 時は `{ error, available_typenames }` を JSON で返しクライアントはフォールバックへ移行。

### GetCapabilities
- 挙動: `WFSLayers` に列挙されたレイヤのみを `<FeatureTypeList>` として返す。`WFSLayers` が未定義または空の場合は空の `<FeatureTypeList>` を返す。
- レスポンス: `WFS_Capabilities` XML（version=2.0.0）を返す。
- 注意: 実装変更後は実行中の HTTP サーバ（QGIS プラグイン）を再起動する必要がある（実行中のプロセスはディスク上の変更を自動で読み込まないため）。

### GetFeature
- 入力パラメータ: `TYPENAME`（必須）、`OUTPUTFORMAT`（任意）、`BBOX`、`MAXFEATURES`、`SRSNAME` など。
- OUTPUTFORMAT 判定ロジック: 受け取った値に `gml` を含む文字列があれば GML、それ以外は GeoJSON（例: `application/gml+xml` → GML / `application/json` → GeoJSON）。GeoJSON にはスタイル情報を含めない（データ/スタイル分離）。
- GeoJSON: `QgsJsonExporter` 等を利用して GeoJSON を返す。
- GML: 簡易 GML を生成する実装を持つ。Point, LineString, Polygon に加え、簡易的な MultiPoint/MultiLineString/MultiPolygon の出力をサポートする（ポリゴンは外郭リングのみを扱う等の制限あり）。フルスキーマの互換性を要求するクライアントは事前に検証すること。

**Phase 1 高速化の動作**:
1. キャッシュキーを生成（レイヤーID、BBOX、SRS、最大地物数、出力フォーマット）
2. キャッシュをチェック
   - ヒット: キャッシュされたレスポンスを即座に返す（< 5ms）
   - ミス: 通常処理を実行
3. 地物クエリを最適化手法で実行（`ExactIntersect`フラグ + イテレータ）
4. GeoJSON/GML変換を実行
5. 結果をキャッシュに保存（タイムスタンプ付き）
6. レスポンスを返却
7. 10%の確率で期限切れキャッシュをクリーンアップ

### DescribeFeatureType
- 挙動: 指定レイヤの属性スキーマを XML 形式で返す（既存の実装に準拠）。

### GetStyles
- 挙動: 指定レイヤの QGIS レンダラ設定に基づいて SLD (Styled Layer Descriptor) を生成して XML 形式で返す。
- 入力パラメータ: `TYPENAME`（必須）、`VERSION`（オプション、デフォルト: 1.1.0）。
- サポートするレンダラタイプ: 単一シンボル (singleSymbol)、分類シンボル (categorizedSymbol)、グラデーションシンボル (graduatedSymbol)、ルールベースレンダラ (ruleBased)。
- レスポンス: SLD 1.1.0 準拠の XML。レンダラタイプに応じて適切なシンボル定義を生成。
- 注意: ルールベースレンダラの場合、最初のルールのシンボルをデフォルトとして使用。複雑なルール構造は簡易処理。MapLibre のスタイル注入は SLD を直接利用せず、QGIS レンダラ → MapLibre 変換を別エンドポイント（`/maplibre-style`）で行う。

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

- GetStyles 固有のエラー: レイヤが見つからない場合やレンダラ処理失敗時に同形式エラー。`/maplibre-style` 404 は JSON で返却しクライアントはフォールバック表示へ遷移。

### 運用上の注意
- `GetCapabilities` と `/wfs-layers` が同じ `WFSLayers` を参照するため、公開設定はプロジェクト側で一元的に管理すること。
- GetStyles は QGIS のレンダラ設定を SLD に変換するため、複雑なスタイルは簡易的に処理される場合がある。
- 実装は簡易的な GML 出力を行うため、GML の厳密な互換性が必要なワークフローでは注意して検証すること。

## 10. Google Maps / Google Earth 連携（生成とパース）
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
## 11. External Control（外部制御）のパース優先度と挙動
- 機能: パネルの `External Control` が有効なら、外部から受信した URL を自動適用して QGIS をナビゲートする。
- パース優先度は上記 §6 に準じる。
- 動作:
  - 受信 URL をパースして `navigate_from_http` ルートを使い QGIS の表示を更新する。
  - パネル起動時に既に受信済みの URL がある場合は自動ナビゲートを実行（設定に依存）。
- セキュリティ: 自動ナビゲートは UX を上書きするため、明確な ON/OFF トグルを持ち、ログに受信元・実行時刻を記録することを推奨。

---
## 12. テーマ (Theme) サポート
- `theme` パラメータに指定されたマップテーマ名を仮想マップビューに適用して PNG を生成する。プロジェクト自体の状態を変更しない（仮想ビューを使用）。
- `theme` 値はプロジェクト内の既存マップテーマ名のみサポート。未存在の場合はエラーまたはフォールバック動作（No Theme として位置のみ適用）。
- スタイルのエクスポートでは QGIS バージョン差に備えて `exportNamedStyle` 等の呼び出しにフォールバックを用意。

---
## 13. 回転（ANGLE）パイプラインとパフォーマンス
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
## 14. 投影 (CRS) ポリシー
- OpenLayers（ブラウザ表示）は常に `EPSG:3857` で提供する。
- WMS は複数 CRS を受け付け、要求 CRS に従ってレンダリングする。クライアント向けに変換が必要な場合はサーバ側で `EPSG:3857` に変換して返す（OpenLayers の一貫性のため）。
- `crs` を指定しないパーマリンクは `EPSG:4326` として解釈される。
- 座標変換は `QgsCoordinateTransform` を利用。プロジェクトによっては外部の proj 定義が必要となる場合がある。

---
## 15. セキュリティ・運用上の注意
- デフォルトで外部アクセスを許す設計だが、公開環境ではファイアウォールやプロキシでアクセス制御を厳格に行うこと。
- `External Control` を有効にしていると任意の外部URLで QGIS の表示が書き換わるため、信頼できるネットワーク内または追加の承認フローを用いることを強く推奨。
- WMS の `GetMap` で大きなレンダ要求が可能なため、認証・リクエストレート制限・サイズ上限を検討する。特に `ANGLE!=0` のリクエストは重い。
- ログを適切に出力し、受信元IP・タイムスタンプ・実行アクションを残す運用を推奨。

---
## 16. テスト・QA 手順
自動テスト候補:
- `server_manager.py` のユニットテスト: ポート選定・バインド挙動のモックテスト。
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
## 17. 実装ファイルと責務マッピング
- `plugin.py` — メインプラグインロジック、ユーティリティ関数。
- `panel.py` — パネル UI 実装（ナビゲート、生成、外部制御トグル等）。
- `panel_base.ui` — Qt Designer の UI 定義。
- `server_manager.py` — 組み込み HTTP サーバーの起動/停止・ルーティング（WMS/Map endpoints）。
- `qmap_webmap_generator.py` — OpenLayers / MapLibre HTML テンプレートの生成ロジック。
- `qmap_wmts_service.py` / `qmap_wms_service.py` — WMS/WMTS 関連のヘルパー（タイル変換、BBOX 計算など）。
- `panel.py` から `navigate_from_http` / `navigate_to_coordinates` を呼び出す流れ。

---
## 18. 変更履歴の要約（V2/V3 ハイライト）
- V2.0.0: WMS サポートと外部アクセス（0.0.0.0 バインド）を追加。
- V2.6.0: 投影定義と軸順情報を生成 HTML に埋め込み、座標表示の精度向上。
- V2.8.0: External Control の自動ナビゲート追加。
- V2.10.0: Google Earth `y` トークン対応とスケール推定の改善。
- V2.12.0: テーマ対応 WMS 出力（仮想マップビュー）。
- V2.13.0: WMTS タイルエンドポイント、MapLibre 改善（pitch トグル、zoom clamp 解除）。
- V3.0.0: MapLibre WFS + QGIS スタイル注入の安定化、ベーススタイルの相対URL化、ブラシ無しポリゴンの正しい境界線表示、単位正規化（mm/pt→px）を確立。

- V3.1.0: WMTS キャッシュ導入
  - サーバ側で WMTS タイルのキャッシュを有効化しました。キャッシュは各 "identity" ごとに分離され、identity は表示中のレイヤ識別子（layer ID）と各レイヤに適用されるスタイル識別子（style ID）を決定的に組み合わせた JSON を sha1 ハッシュ化し、その先頭 12 文字（short hash）を採用して生成されます。
  - GetCapabilities の ResourceURL / ServiceMetadataURL に `?v=<identity_short>` を付与することで、クライアントが現在サーバ側で有効な identity を検出できるようにしました。
  - クライアント（MapLibre）は画面移動（moveend）時に GetCapabilities を再取得し、identity が変化していれば WMTS タイルソースのみを差し替えて新しいタイルを取得する挙動を推奨します（WFS やスタイル全体の再読み込みは不要）。
  - この仕組みにより、サーバ側で表示用レイヤやスタイルが変更された際に WMTS のみを効率的に更新・無効化でき、WFS の重複登録や全スタイル再適用に起因する副作用を避けられます。

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
