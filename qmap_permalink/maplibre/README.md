# QMapPermalink maplibre helpers

このディレクトリには MapLibre 用の軽量ヘルパーモジュールを置いてあります。
目的は `qmap_maplibre.py` 内の WMTS/WFS/SLD 関連のロジックを分離して再利用性を高めることです。

エクスポートされる API

- choose_tile_template() -> str
  - 説明: 実行環境が QGIS を含む場合はローカル WMTS テンプレート (`/wmts/{z}/{x}/{y}.png`) を返し、
    それ以外では OpenStreetMap のタイルテンプレートを返します。
  - 戻り値: タイル URL テンプレート文字列

- default_wmts_layers_js() -> str
  - 説明: MapLibre HTML テンプレートにそのまま埋め込める、WMTS レイヤの初期 JavaScript 配列（文字列）を返します。
  - 戻り値: JS スニペット例: "const wmtsLayers = [{ id: 'qmap', title: 'QGIS Map (WMTS)' }];"

- prepare_wfs_for_maplibre(permalink_text: str, wfs_typename: Optional[str]=None) -> dict
  - 説明: permalink（URL 文字列）と任意の `wfs_typename` を受け取り、MapLibre HTML に埋めるための WFS 関連変数
    を正規化して返します（typename の抽出・URLエンコード・QGIS 環境があれば canonical id への正規化等）。
  - 戻り値: dict には少なくとも以下のキーが含まれます:
    - 'final_typename', 'wfs_typename', 'wfs_query_url', 'wfs_source_id', 'wfs_layer_id',
      'wfs_label_id', 'wfs_layer_title', 'wfs_label_title', 'style_url', 'wfs_layers_js'
  - 例外: typename が提供されない場合、ValueError を送出します。

- sld_to_mapbox_style(sld_xml: str, source_id: str = 'qgis') -> list
  - 説明: SLD XML を解析し、Mapbox/MapLibre スタイルの layer オブジェクト配列（Python dict のリスト）を返します。
    対応: PointSymbolizer, LineSymbolizer, PolygonSymbolizer の簡易変換。
  - 戻り値: Mapbox style の layers に相当する Python dict のリスト。
  - 失敗時: 空リストを返します（例外は基本的に上げず、ログ/print で通知します）。

使用例（短いスニペット）

```py
from qmap_permalink.maplibre import (
    choose_tile_template,
    default_wmts_layers_js,
    prepare_wfs_for_maplibre,
    sld_to_mapbox_style,
)

# tile template
tpl = choose_tile_template()

# prepare wfs
wfs_info = prepare_wfs_for_maplibre('https://example/?typename=mylayer')
print(wfs_info['wfs_query_url'])

# convert sld
layers = sld_to_mapbox_style(sld_xml_string, source_id='mylayer')

```

注意事項

- QGIS の Python バインディングが利用可能な場合、関数は QGIS の API を呼んで名前の正規化や座標変換等の処理を行います。
- ヘビーデペンデンシーを避けるため、QGIS は実行時チェックでのみ使用します。QGIS が無い環境でもインポート可能です。
