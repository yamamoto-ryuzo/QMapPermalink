#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地図が表示されない根本原因の調査
JavaScript実行エラーやレンダリング問題を特定
"""

import urllib.request
import urllib.parse
import re
from datetime import datetime

def create_detailed_debug_page():
    """詳細なデバッグ機能付きのテストページを作成"""
    
    debug_html = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>地図表示デバッグ - 詳細診断</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ol@v8.2.0/ol.css">
    <script src="https://cdn.jsdelivr.net/npm/ol@v8.2.0/dist/ol.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 10px; background: #f5f5f5; }
        .debug-panel { background: white; border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .debug-title { font-weight: bold; color: #333; margin-bottom: 10px; font-size: 16px; }
        #map { width: 100%; height: 400px; border: 3px solid #ff0000; background: #f0f0f0; }
        .log { font-family: monospace; font-size: 12px; background: #000; color: #0f0; padding: 10px; max-height: 200px; overflow-y: auto; }
        .error { color: #ff0000; font-weight: bold; }
        .success { color: #00aa00; font-weight: bold; }
        .info { color: #0066cc; }
        .test-step { margin: 5px 0; padding: 5px; background: #f9f9f9; border-left: 4px solid #ccc; }
        .step-success { border-left-color: #4caf50; }
        .step-error { border-left-color: #f44336; }
        .coordinates { font-family: monospace; background: #ffffcc; padding: 5px; margin: 5px 0; }
    </style>
</head>
<body>
    <div class="debug-panel">
        <div class="debug-title">🔍 地図表示問題 - 詳細診断ツール</div>
        <p>この画面で地図が表示されない原因を特定します。各ステップの結果を確認してください。</p>
        <div id="overall-status" class="test-step">診断実行中...</div>
    </div>

    <div class="debug-panel">
        <div class="debug-title">📋 診断ステップ</div>
        <div id="step1" class="test-step">ステップ1: OpenLayersライブラリ読み込み確認</div>
        <div id="step2" class="test-step">ステップ2: 基本マップ初期化テスト</div>
        <div id="step3" class="test-step">ステップ3: 座標変換テスト</div>
        <div id="step4" class="test-step">ステップ4: レイヤー作成テスト</div>
        <div id="step5" class="test-step">ステップ5: 実際の地図表示テスト</div>
    </div>

    <div class="debug-panel">
        <div class="debug-title">🗺️ 地図表示エリア</div>
        <p>ここに地図が表示されるはずです。赤い枠が見える場合は、地図コンテナは存在しています。</p>
        <div id="map"></div>
    </div>

    <div class="debug-panel">
        <div class="debug-title">📊 リアルタイムログ</div>
        <div id="debug-log" class="log">診断開始...\n</div>
    </div>

    <script>
        let debugLog = document.getElementById('debug-log');
        let stepCount = 0;
        let errorCount = 0;

        function log(message, type = 'info') {
            const timestamp = new Date().toLocaleTimeString();
            const className = type === 'error' ? 'error' : type === 'success' ? 'success' : 'info';
            debugLog.innerHTML += `<span class="${className}">[${timestamp}] ${message}</span>\n`;
            debugLog.scrollTop = debugLog.scrollHeight;
            console.log(`[DEBUG] ${message}`);
        }

        function updateStep(stepId, message, success = true) {
            const step = document.getElementById(stepId);
            step.innerHTML = message;
            step.className = success ? 'test-step step-success' : 'test-step step-error';
            if (!success) errorCount++;
        }

        function runDiagnostics() {
            log('🚀 地図表示診断を開始します', 'info');

            // ステップ1: OpenLayersライブラリ確認
            try {
                if (typeof ol === 'undefined') {
                    throw new Error('OpenLayersライブラリが読み込まれていません');
                }
                log(`✅ OpenLayersライブラリ検出: バージョン ${ol.VERSION_}`, 'success');
                updateStep('step1', `✅ ステップ1: OpenLayers v${ol.VERSION_} 読み込み成功`, true);
            } catch (error) {
                log(`❌ ステップ1 失敗: ${error.message}`, 'error');
                updateStep('step1', `❌ ステップ1: ${error.message}`, false);
                return;
            }

            // ステップ2: 基本マップ初期化テスト
            try {
                log('📍 基本マップ初期化テスト開始', 'info');
                const testCoords = [139.6917, 35.6895]; // 東京
                log(`使用座標: 経度=${testCoords[0]}, 緯度=${testCoords[1]}`, 'info');

                const map = new ol.Map({
                    target: 'map',
                    layers: [],
                    view: new ol.View({
                        center: ol.proj.fromLonLat(testCoords),
                        zoom: 10
                    })
                });

                log('✅ 基本マップオブジェクト作成成功', 'success');
                updateStep('step2', '✅ ステップ2: 基本マップ初期化成功', true);

                // ステップ3: 座標変換テスト
                log('🔄 座標変換テスト実行', 'info');
                const projectedCoords = ol.proj.fromLonLat(testCoords);
                log(`変換結果: [${projectedCoords[0].toFixed(2)}, ${projectedCoords[1].toFixed(2)}]`, 'success');
                updateStep('step3', '✅ ステップ3: 座標変換成功', true);

                // ステップ4: レイヤー作成テスト
                log('🗺️ OpenStreetMapレイヤー作成テスト', 'info');
                const osmLayer = new ol.layer.Tile({
                    source: new ol.source.OSM()
                });
                map.addLayer(osmLayer);
                log('✅ OSMレイヤー追加成功', 'success');
                updateStep('step4', '✅ ステップ4: レイヤー作成・追加成功', true);

                // ステップ5: 地図表示確認
                setTimeout(() => {
                    try {
                        const mapDiv = document.getElementById('map');
                        const mapSize = map.getSize();
                        log(`地図コンテナサイズ: [${mapSize[0]}, ${mapSize[1]}]`, 'info');
                        
                        // マーカー追加でテスト
                        const marker = new ol.Feature({
                            geometry: new ol.geom.Point(ol.proj.fromLonLat(testCoords))
                        });
                        
                        marker.setStyle(new ol.style.Style({
                            image: new ol.style.Circle({
                                radius: 10,
                                fill: new ol.style.Fill({color: 'red'}),
                                stroke: new ol.style.Stroke({color: 'white', width: 2})
                            }),
                            text: new ol.style.Text({
                                text: 'TEST',
                                font: '14px Arial',
                                fill: new ol.style.Fill({color: 'black'}),
                                offsetY: -25
                            })
                        }));

                        const vectorLayer = new ol.layer.Vector({
                            source: new ol.source.Vector({
                                features: [marker]
                            })
                        });
                        
                        map.addLayer(vectorLayer);
                        log('✅ テストマーカー追加成功', 'success');
                        updateStep('step5', '✅ ステップ5: 地図表示・マーカー追加成功', true);

                        // 最終判定
                        document.getElementById('overall-status').innerHTML = '✅ 全ての診断項目が成功しました。地図は正常に表示されているはずです。';
                        document.getElementById('overall-status').className = 'test-step step-success';

                        // クリックイベント追加
                        map.on('click', function(evt) {
                            const coordinate = ol.proj.toLonLat(evt.coordinate);
                            log(`🖱️ 地図クリック: 緯度=${coordinate[1].toFixed(6)}, 経度=${coordinate[0].toFixed(6)}`, 'success');
                            alert(`クリック位置: ${coordinate[1].toFixed(6)}, ${coordinate[0].toFixed(6)}`);
                        });

                        log('🎉 地図表示診断完了 - 全て成功', 'success');

                    } catch (error) {
                        log(`❌ ステップ5 失敗: ${error.message}`, 'error');
                        updateStep('step5', `❌ ステップ5: ${error.message}`, false);
                    }
                }, 2000);

            } catch (error) {
                log(`❌ マップ初期化エラー: ${error.message}`, 'error');
                updateStep('step2', `❌ ステップ2: ${error.message}`, false);
                document.getElementById('overall-status').innerHTML = `❌ 診断失敗: ${error.message}`;
                document.getElementById('overall-status').className = 'test-step step-error';
            }
        }

        // ページ読み込み完了後に診断実行
        window.addEventListener('load', function() {
            log('📄 ページ読み込み完了', 'info');
            setTimeout(runDiagnostics, 500);
        });

        // エラーハンドリング
        window.addEventListener('error', function(event) {
            log(`❌ JavaScript エラー: ${event.error.message}`, 'error');
            log(`エラー場所: ${event.filename}:${event.lineno}`, 'error');
        });

    </script>
</body>
</html>"""

    with open('c:/github/QMapPermalink/map_display_debug.html', 'w', encoding='utf-8') as f:
        f.write(debug_html)
    
    print("✅ 詳細デバッグページを作成しました: map_display_debug.html")
    return 'c:/github/QMapPermalink/map_display_debug.html'

def test_actual_server_response():
    """実際のサーバーレスポンスをより詳細に分析"""
    
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
    
    print("\n" + "=" * 80)
    print("🔍 サーバーレスポンス - JavaScript詳細分析")
    print("=" * 80)
    
    try:
        with urllib.request.urlopen(full_url, timeout=10) as response:
            content = response.read().decode('utf-8')
            
            # JavaScriptの構文エラーをチェック
            print("🔧 JavaScript構文チェック:")
            
            # 1. 括弧の対応確認
            open_braces = content.count('{')
            close_braces = content.count('}')
            open_parens = content.count('(')
            close_parens = content.count(')')
            
            print(f"  波括弧: {{ {open_braces} 個, }} {close_braces} 個 - {'✅' if open_braces == close_braces else '❌'}")
            print(f"  丸括弧: ( {open_parens} 個, ) {close_parens} 個 - {'✅' if open_parens == close_parens else '❌'}")
            
            # 2. 重要なOpenLayers関数の存在確認
            ol_functions = [
                'new ol.Map',
                'ol.proj.fromLonLat',
                'new ol.layer.Tile',
                'new ol.source.OSM',
                'new ol.View'
            ]
            
            print("\n📚 OpenLayers関数確認:")
            for func in ol_functions:
                exists = func in content
                print(f"  {'✅' if exists else '❌'} {func}")
            
            # 3. 座標値の妥当性確認
            print("\n📍 座標値確認:")
            coord_pattern = r'ol\.proj\.fromLonLat\s*\(\s*\[\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\]\s*\)'
            coords = re.findall(coord_pattern, content)
            
            for i, (lon, lat) in enumerate(coords):
                lon_val = float(lon)
                lat_val = float(lat)
                valid_lon = -180 <= lon_val <= 180
                valid_lat = -90 <= lat_val <= 90
                print(f"  座標{i+1}: 経度={lon_val} {'✅' if valid_lon else '❌'}, 緯度={lat_val} {'✅' if valid_lat else '❌'}")
            
            # 4. エラーを起こしやすいパターンをチェック
            print("\n⚠️ 問題のあるパターンをチェック:")
            
            issues = []
            
            # undefined変数
            if 'undefined' in content.lower():
                issues.append("undefined変数の可能性")
            
            # 未閉じの文字列
            single_quotes = content.count("'")
            double_quotes = content.count('"')
            if single_quotes % 2 != 0:
                issues.append("未閉じのシングルクォート")
            if double_quotes % 2 != 0:
                issues.append("未閉じのダブルクォート")
            
            # セミコロン不足（簡易チェック）
            lines = content.split('\n')
            js_lines = [line.strip() for line in lines if 'console.log' in line or 'new ol.' in line]
            for line in js_lines:
                if line and not line.endswith(';') and not line.endswith('{') and not line.endswith('}'):
                    issues.append(f"セミコロン不足の可能性: {line[:50]}...")
            
            if issues:
                for issue in issues:
                    print(f"  ❌ {issue}")
            else:
                print("  ✅ 明らかな構文問題は検出されませんでした")
            
            # 5. 生成されたHTMLファイルを保存（詳細デバッグ用）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            debug_file = f'server_response_debug_{timestamp}.html'
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"\n💾 サーバーレスポンスを保存: {debug_file}")
            
            return content
            
    except Exception as e:
        print(f"❌ サーバーアクセスエラー: {e}")
        return None

def main():
    print("🔍 地図が表示されない問題の根本原因調査")
    print("=" * 80)
    
    # 1. 詳細デバッグページ作成
    debug_file = create_detailed_debug_page()
    
    # 2. サーバーレスポンス詳細分析
    content = test_actual_server_response()
    
    print("\n" + "=" * 80)
    print("📋 調査結果と推奨アクション")
    print("=" * 80)
    
    print("1. 📄 詳細デバッグページでの確認:")
    print(f"   {debug_file} をブラウザで開いてください")
    print("   各ステップの結果を確認し、どこで失敗するかチェック")
    
    print("\n2. 🌐 ブラウザでの確認手順:")
    print("   - F12で開発者ツールを開く")
    print("   - Consoleタブでエラーメッセージを確認")
    print("   - Networkタブで外部リソース読み込み状況を確認")
    
    print("\n3. 🔧 よくある原因:")
    print("   - JavaScriptが無効になっている")
    print("   - CDN（OpenLayersライブラリ）へのアクセスがブロックされている")
    print("   - ブラウザのコンテンツブロッカーが動作している")
    print("   - 企業ファイアウォールによるブロック")
    print("   - ブラウザの互換性問題")

if __name__ == "__main__":
    main()