#!/usr/bin/env python3
"""
GeoJSON生成のテストスクリプト
QGIS環境がないため、モックを使ってテストします。
"""

import json
import sys
import os

# プロジェクトディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(__file__))

class MockQgsVectorLayer:
    """QgsVectorLayerのモック"""
    def __init__(self, name="test_layer"):
        self._name = name
        self._crs = MockQgsCoordinateReferenceSystem()

    def name(self):
        return self._name

    def crs(self):
        return self._crs

    def renderer(self):
        return MockQgsRenderer()

class MockQgsCoordinateReferenceSystem:
    """QgsCoordinateReferenceSystemのモック"""
    def authid(self):
        return "EPSG:4326"

    def isValid(self):
        return True

class MockQgsRenderer:
    """QgsRendererのモック"""
    def symbolForFeature(self, feature, context):
        return MockQgsFillSymbol()

class MockQgsFillSymbol:
    """QgsFillSymbolのモック"""
    def __init__(self):
        self._color = MockQColor("#FF0000")  # 赤色
        self._opacity = 0.8

    def color(self):
        return self._color

    def opacity(self):
        return self._opacity

class MockQColor:
    """QColorのモック"""
    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name

    def isValid(self):
        return True

class MockFeature:
    """QgsFeatureのモック"""
    def __init__(self, id=1, geometry=None, attributes=None):
        self._id = id
        self._geometry = geometry or {"type": "Point", "coordinates": [139.6917, 35.6895]}
        self._attributes = attributes or {"name": "東京", "population": 13929286}

    def id(self):
        return self._id

    def geometry(self):
        return self._geometry

    def attribute(self, name):
        return self._attributes.get(name)

    def fields(self):
        return MockFields()

class MockFields:
    """QgsFieldsのモック"""
    def count(self):
        return 2

    def field(self, index):
        fields = [
            MockField("name", "string"),
            MockField("population", "integer")
        ]
        return fields[index] if index < len(fields) else None

class MockField:
    """QgsFieldのモック"""
    def __init__(self, name, type_name):
        self._name = name
        self._type_name = type_name

    def name(self):
        return self._name

    def typeName(self):
        return self._type_name

class MockQgsJsonExporter:
    """QgsJsonExporterのモック"""
    def __init__(self, layer):
        self.layer = layer

    def exportFeature(self, feature):
        # 基本的なGeoJSONフィーチャーを作成
        geojson = {
            "type": "Feature",
            "geometry": feature.geometry(),
            "properties": feature._attributes
        }
        return json.dumps(geojson)

class MockQgsRenderContext:
    """QgsRenderContextのモック"""
    pass

class MockQgsExpressionContext:
    """QgsExpressionContextのモック"""
    def appendScopes(self, scopes):
        pass

    def setFeature(self, feature):
        pass

class MockQgsExpressionContextUtils:
    """QgsExpressionContextUtilsのモック"""
    @staticmethod
    def globalProjectLayerScopes(layer):
        return []

# WFSサービスのGeoJSON生成部分をテスト
def test_geojson_generation():
    """GeoJSON生成をテスト"""
    print("GeoJSON生成テストを開始します...")

    # モックレイヤーとフィーチャーを作成
    layer = MockQgsVectorLayer("test_layer")
    features = [
        MockFeature(1, {"type": "Point", "coordinates": [139.6917, 35.6895]}, {"name": "東京", "population": 13929286}),
        MockFeature(2, {"type": "Point", "coordinates": [135.5023, 34.6937]}, {"name": "大阪", "population": 8837683})
    ]

    # GeoJSON生成（簡易版）
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    for feature in features:
        # 基本フィーチャー
        feature_json = {
            "type": "Feature",
            "geometry": feature.geometry(),
            "properties": feature._attributes
        }

        # スタイルヒントの追加（モック）
        style_hint = {
            "geomType": "Point",
            "fill": "#FF0000",
            "fill-opacity": 0.8
        }

        if style_hint:
            feature_json['properties']['_qgis_style'] = style_hint
            for sk, sv in style_hint.items():
                if sk not in feature_json['properties']:
                    feature_json['properties'][sk] = sv

        geojson["features"].append(feature_json)

    # 結果を表示
    result = json.dumps(geojson, ensure_ascii=False, indent=2)
    print("生成されたGeoJSON:")
    print(result)

    return result

if __name__ == "__main__":
    test_geojson_generation()