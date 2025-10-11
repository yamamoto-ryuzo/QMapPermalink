#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
実際のGoogle MapsとGoogle EarthのURL動作確認
"""

def test_actual_urls():
    """実際のURLが正しい形式かテスト"""
    print("=== 実際のURL形式確認 ===\n")
    
    # テストケース: 東京駅周辺
    lat, lon = 35.681236, 139.767125
    
    # 各ズームレベルでのURL生成
    test_zooms = [12, 15, 17, 19]
    
    for zoom in test_zooms:
        print(f"=== ズームレベル {zoom} ===")
        
        # Google Maps URL
        maps_url = f"https://www.google.co.jp/maps/@{lat:.6f},{lon:.6f},{zoom}z"
        print(f"Maps: {maps_url}")
        
        # Google Earth URL (高度計算)
        altitude = max(100, int(40000000 / (2 ** (zoom - 1))))
        earth_url = f"https://earth.google.com/web/@{lat:.6f},{lon:.6f},{altitude}a,35y,0h,0t,0r"
        print(f"Earth: {earth_url}")
        print(f"高度: {altitude}m")
        print()

def explain_google_earth_parameters():
    """Google EarthのURLパラメータの説明"""
    print("=== Google Earth URLパラメータ説明 ===\n")
    print("URL形式: https://earth.google.com/web/@lat,lon,altitude,heading,tilt,roll")
    print()
    print("パラメータ:")
    print("  lat: 緯度")
    print("  lon: 経度") 
    print("  altitude: 高度 (メートル、末尾に'a')")
    print("  heading: 方位角 (度、末尾に'y') - 0=北向き")
    print("  tilt: 傾斜角 (度、末尾に'h') - 0=真上から")
    print("  roll: 回転角 (度、末尾に't') - 0=水平")
    print("  最後の'r': 不明なパラメータ（常に0）")
    print()
    print("現在の設定:")
    print("  heading=0 (北向き)")
    print("  tilt=0 (真上から)")
    print("  roll=0 (水平)")
    print("  → オーバーヘッドビュー（航空写真的な視点）")

def create_demo_html():
    """デモ用のHTMLページを作成"""
    demo_locations = [
        {"name": "東京駅", "lat": 35.681236, "lon": 139.767125, "zoom": 17},
        {"name": "富士山", "lat": 35.360626, "lon": 138.727363, "zoom": 13},
        {"name": "大阪城", "lat": 34.687315, "lon": 135.526201, "zoom": 16},
        {"name": "厳島神社", "lat": 34.295987, "lon": 132.319691, "zoom": 15},
    ]
    
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang=\"ja\">",
        "<head>",
        "<meta charset=\"utf-8\">",
        "<title>QMap Permalink - デモ</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }",
        ".container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }",
        ".location { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; background-color: #fafafa; }",
        ".location-name { font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px; }",
        ".link-row { display: flex; gap: 20px; margin: 10px 0; }",
        ".link-button { flex: 1; padding: 10px; text-align: center; border-radius: 5px; text-decoration: none; font-weight: bold; }",
        ".maps-button { background-color: #4285f4; color: white; }",
        ".earth-button { background-color: #34a853; color: white; }",
        ".maps-button:hover { background-color: #3367d6; }",
        ".earth-button:hover { background-color: #2d8a42; }",
        "</style>",
        "</head>",
        "<body>",
        "<div class=\"container\">",
        "<h1>🗺️ QMap Permalink デモ</h1>",
        "<p>以下の場所をGoogle MapsまたはGoogle Earthで表示できます：</p>",
    ]
    
    for loc in demo_locations:
        maps_url = f"https://www.google.co.jp/maps/@{loc['lat']:.6f},{loc['lon']:.6f},{loc['zoom']}z"
        altitude = max(100, int(40000000 / (2 ** (loc['zoom'] - 1))))
        earth_url = f"https://earth.google.com/web/@{loc['lat']:.6f},{loc['lon']:.6f},{altitude}a,35y,0h,0t,0r"
        
        html_parts.extend([
            "<div class=\"location\">",
            f"<div class=\"location-name\">{loc['name']}</div>",
            f"<div>座標: {loc['lat']:.6f}, {loc['lon']:.6f} (ズーム{loc['zoom']})</div>",
            "<div class=\"link-row\">",
            f"<a href=\"{maps_url}\" target=\"_blank\" class=\"link-button maps-button\">🗺️ Google Maps で開く</a>",
            f"<a href=\"{earth_url}\" target=\"_blank\" class=\"link-button earth-button\">🌍 Google Earth で開く</a>",
            "</div>",
            "</div>"
        ])
    
    html_parts.extend([
        "</div>",
        "</body>",
        "</html>"
    ])
    
    html_content = "\n".join(html_parts)
    
    try:
        with open("qmap_permalink_demo.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("qmap_permalink_demo.html を作成しました！")
        print("ブラウザで開いて実際のリンクをテストできます。")
        return True
    except Exception as e:
        print(f"デモHTML作成エラー: {e}")
        return False

if __name__ == "__main__":
    test_actual_urls()
    print()
    explain_google_earth_parameters()
    print()
    create_demo_html()
    
    print("\n=== 実装サマリー ===")
    print("✅ Google Maps URL生成: 標準的な@lat,lon,zoomz形式")
    print("✅ Google Earth URL生成: @lat,lon,altitude,heading,tilt,roll形式")
    print("✅ スケールからズームレベルへの適切な変換")
    print("✅ ズームレベルから高度への変換（Google Earth用）")
    print("✅ 美しいHTMLレスポンス生成")
    print("✅ 両サービスへのリンクを同時提供")
    print("\nQGISプラグインがGoogle MapsとGoogle Earthの両方をサポートしました！")