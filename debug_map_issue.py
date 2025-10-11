#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地図表示問題の詳細デバッグスクリプト
サーバー側とクライアント側の両方の問題を特定
"""

import urllib.request
import urllib.parse
import re
import json
from datetime import datetime

def analyze_server_response():
    """サーバーレスポンスの詳細分析"""
    
    params = {
        'x': '15557945.984400',
        'y': '4257187.015550', 
        'scale': '21280.2',
        'crs': 'EPSG:3857',
        'rotation': '0.00'
    }
    
    base_url = 'http://localhost:8089/qgis-map'
    query_string = urllib.parse.urlencode(params)
    full_url = f"{base_url}?{query_string}"
    
    print("=" * 80)
    print("🔍 サーバー側レスポンス分析")
    print("=" * 80)
    
    try:
        with urllib.request.urlopen(full_url, timeout=10) as response:
            content = response.read().decode('utf-8')
            
            # 1. OpenLayersライブラリの読み込み確認
            print("📚 OpenLayersライブラリ確認:")
            ol_css = re.search(r'href="([^"]*ol[^"]*\.css[^"]*)"', content)
            ol_js = re.search(r'src="([^"]*ol[^"]*\.js[^"]*)"', content)
            
            if ol_css:
                print(f"  ✅ CSS: {ol_css.group(1)}")
                # CDNの接続確認
                try:
                    urllib.request.urlopen(ol_css.group(1), timeout=5)
                    print("    ✅ CSS CDN アクセス可能")
                except:
                    print("    ❌ CSS CDN アクセス不可")
            else:
                print("  ❌ OpenLayers CSS が見つからない")
            
            if ol_js:
                print(f"  ✅ JS: {ol_js.group(1)}")
                # CDNの接続確認
                try:
                    urllib.request.urlopen(ol_js.group(1), timeout=5)
                    print("    ✅ JS CDN アクセス可能")
                except:
                    print("    ❌ JS CDN アクセス不可")
            else:
                print("  ❌ OpenLayers JS が見つからない")
            
            # 2. マップコンテナの確認
            print("\n🗺️ マップコンテナ確認:")
            map_div = re.search(r'<div[^>]*id=[\'"]\s*map\s*[\'"][^>]*>', content)
            if map_div:
                print(f"  ✅ マップDIV: {map_div.group(0)}")
            else:
                print("  ❌ マップDIVが見つからない")
            
            # 3. マップ初期化スクリプトの確認
            print("\n🚀 マップ初期化スクリプト確認:")
            map_init = re.search(r'new ol\.Map\s*\(\s*\{([^}]*)\}', content, re.DOTALL)
            if map_init:
                print("  ✅ ol.Map初期化コード発見")
                map_config = map_init.group(1)
                print(f"  📋 設定内容: {map_config[:200]}...")
            else:
                print("  ❌ ol.Map初期化コードが見つからない")
            
            # 4. 座標データの確認
            print("\n📍 座標データ確認:")
            coord_pattern = r'ol\.proj\.fromLonLat\s*\(\s*\[\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\]\s*\)'
            coords = re.findall(coord_pattern, content)
            if coords:
                for i, (lon, lat) in enumerate(coords):
                    print(f"  ✅ 座標{i+1}: 経度={lon}, 緯度={lat}")
            else:
                print("  ❌ 座標データが見つからない")
            
            # 5. エラーメッセージの確認
            print("\n⚠️ エラーメッセージ確認:")
            error_divs = re.findall(r'<div[^>]*class="error-message"[^>]*>([^<]*)</div>', content)
            if error_divs:
                for error in error_divs:
                    print(f"  ❌ エラー: {error}")
            else:
                print("  ✅ エラーメッセージなし")
            
            # 6. JavaScriptコンソールログの確認
            print("\n📝 JavaScriptコンソールログ:")
            console_logs = re.findall(r'console\.log\([^)]*\)', content)
            for log in console_logs:
                print(f"  📋 {log}")
            
            # 7. CSSスタイルの確認
            print("\n🎨 マップスタイル確認:")
            map_style = re.search(r'#map\s*\{([^}]*)\}', content)
            if map_style:
                style_content = map_style.group(1)
                print(f"  ✅ マップスタイル: {style_content}")
                
                # 高さの確認
                height_match = re.search(r'height:\s*([^;]+)', style_content)
                if height_match:
                    height = height_match.group(1).strip()
                    print(f"  📏 マップ高さ: {height}")
                    if '400px' in height:
                        print("    ⚠️ 高さが400pxです（600pxが期待値）")
                    elif '600px' in height:
                        print("    ✅ 高さが600pxです")
            else:
                print("  ❌ マップスタイルが見つからない")
            
            return content
            
    except Exception as e:
        print(f"❌ サーバーエラー: {e}")
        return None

def create_minimal_test_page():
    """最小限のテストページを作成"""
    
    print("\n" + "=" * 80)
    print("🧪 最小限テストページ作成")
    print("=" * 80)
    
    minimal_html = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>OpenLayers 最小テスト</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ol@v8.2.0/ol.css">
    <script src="https://cdn.jsdelivr.net/npm/ol@v8.2.0/dist/ol.js"></script>
    <style>
        body { margin: 0; padding: 10px; font-family: Arial, sans-serif; }
        #map { width: 100%; height: 600px; border: 2px solid red; }
        .debug { background: yellow; padding: 10px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="debug">
        <h2>🧪 OpenLayers 最小動作テスト</h2>
        <p>OpenLayersバージョン: <span id="ol-version">読み込み中...</span></p>
        <p>マップ状態: <span id="map-status">初期化中...</span></p>
    </div>
    
    <div id="map"></div>
    
    <script>
        console.log('🚀 OpenLayers最小テスト開始');
        
        // OpenLayersバージョン表示
        document.getElementById('ol-version').textContent = ol.VERSION_ || 'unknown';
        
        try {
            // 日本の座標（東京駅）
            const tokyo = [139.7671, 35.6812];
            
            console.log('📍 使用座標:', tokyo);
            
            const map = new ol.Map({
                target: 'map',
                layers: [
                    new ol.layer.Tile({
                        source: new ol.source.OSM()
                    })
                ],
                view: new ol.View({
                    center: ol.proj.fromLonLat(tokyo),
                    zoom: 12
                })
            });
            
            // マーカー追加
            const marker = new ol.Feature({
                geometry: new ol.geom.Point(ol.proj.fromLonLat(tokyo))
            });
            
            marker.setStyle(new ol.style.Style({
                image: new ol.style.Circle({
                    radius: 10,
                    fill: new ol.style.Fill({color: 'red'}),
                    stroke: new ol.style.Stroke({color: 'white', width: 2})
                }),
                text: new ol.style.Text({
                    text: '東京駅',
                    font: '14px Arial',
                    fill: new ol.style.Fill({color: 'black'}),
                    offsetY: -20
                })
            }));
            
            const vectorLayer = new ol.layer.Vector({
                source: new ol.source.Vector({
                    features: [marker]
                })
            });
            
            map.addLayer(vectorLayer);
            
            document.getElementById('map-status').textContent = '✅ 初期化成功';
            document.getElementById('map-status').style.color = 'green';
            
            console.log('✅ OpenLayersマップ初期化成功');
            
            // クリックイベント
            map.on('click', function(evt) {
                const coord = ol.proj.toLonLat(evt.coordinate);
                console.log('🖱️ クリック座標:', coord);
                alert('クリック位置: ' + coord[1].toFixed(6) + ', ' + coord[0].toFixed(6));
            });
            
        } catch (error) {
            console.error('❌ マップ初期化エラー:', error);
            document.getElementById('map-status').textContent = '❌ エラー: ' + error.message;
            document.getElementById('map-status').style.color = 'red';
            document.getElementById('map').innerHTML = '<div style="color: red; padding: 20px; text-align: center;">マップ初期化に失敗しました: ' + error.message + '</div>';
        }
    </script>
</body>
</html>"""
    
    with open('c:/github/QMapPermalink/minimal_test.html', 'w', encoding='utf-8') as f:
        f.write(minimal_html)
    
    print("✅ 最小テストページを作成しました: minimal_test.html")
    print("   ブラウザで直接開いて動作確認してください")

def main():
    """メイン実行"""
    print(f"🔍 地図表示問題デバッグ開始: {datetime.now()}")
    
    # サーバーレスポンス分析
    content = analyze_server_response()
    
    # 最小テストページ作成
    create_minimal_test_page()
    
    print("\n" + "=" * 80)
    print("📋 デバッグ結果サマリー")
    print("=" * 80)
    
    if content:
        print("✅ サーバー側: レスポンス正常")
        
        # 主要チェックポイント
        checks = [
            ('OpenLayers CSS', 'ol@v8.2.0/ol.css' in content or 'ol.css' in content),
            ('OpenLayers JS', 'ol@v8.2.0/dist/ol.js' in content or 'ol.js' in content),
            ('マップDIV', '<div id="map"' in content),
            ('マップ初期化', 'new ol.Map' in content),
            ('座標変換', 'ol.proj.fromLonLat' in content)
        ]
        
        print("\n🔍 サーバーレスポンス チェック結果:")
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}")
        
        if all(result for _, result in checks):
            print("\n💡 推定原因: クライアント側の問題")
            print("   - ブラウザのJavaScript設定")
            print("   - CDNへのネットワーク接続")
            print("   - ブラウザの互換性")
            print("   - minimal_test.htmlで基本動作を確認してください")
        else:
            print("\n💡 推定原因: サーバー側の問題")
            print("   - HTMLテンプレート生成エラー")
            print("   - WebMapGeneratorの問題")
    else:
        print("❌ サーバー側: 接続エラー")
        print("   - HTTPサーバーが起動していない")
        print("   - ポート8089が使用できない")

if __name__ == "__main__":
    main()