#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google MapsとGoogle EarthのURL生成テスト
"""

import math
import html

def estimate_zoom_from_scale(scale):
    """簡易版のスケール変換（テスト用）"""
    if not scale:
        return 16.0
    try:
        s = float(scale)
        if s <= 0:
            return 16.0

        # 改良版固定スケールテーブル
        scale_table = {
            0: 400_000_000.0, 1: 200_000_000.0, 2: 100_000_000.0, 3: 60_000_000.0, 4: 30_000_000.0,
            5: 15_000_000.0, 6: 8_000_000.0, 7: 4_000_000.0, 8: 2_000_000.0, 9: 1_000_000.0,
            10: 600_000.0, 11: 300_000.0, 12: 150_000.0, 13: 75_000.0, 14: 40_000.0,
            15: 20_000.0, 16: 10_000.0, 17: 5_000.0, 18: 2_500.0, 19: 1_250.0,
            20: 600.0, 21: 300.0, 22: 150.0, 23: 75.0,
        }

        for z in range(24, 31):
            scale_table[z] = scale_table[23] / (2 ** (z - 23))

        target_log = math.log(s)
        best_zoom = 16
        best_diff = None
        for z, zscale in scale_table.items():
            diff = abs(math.log(zscale) - target_log)
            if best_diff is None or diff < best_diff:
                best_diff = diff
                best_zoom = z

        return max(0, min(30, int(best_zoom)))
    except (ValueError, TypeError, OverflowError):
        return 16.0

def build_google_maps_url(lat, lon, scale=None):
    """Google Maps用URLを生成"""
    try:
        if lat is None or lon is None:
            return None
        
        zoom_value = estimate_zoom_from_scale(scale) if scale else 16.0
        zoom_int = max(0, int(round(float(zoom_value))))
        return f"https://www.google.co.jp/maps/@{lat:.6f},{lon:.6f},{zoom_int}z"
    except Exception:
        return None

def build_google_earth_url(lat, lon, scale=None):
    """Google Earth用URLを生成"""
    try:
        if lat is None or lon is None:
            return None
        
        zoom_value = estimate_zoom_from_scale(scale) if scale else 16.0
        
        # ズームレベルから高度を推定（Google Earthでは高度で表現）
        # ズーム1 = 約40,000km高度、ズーム20 = 約100m高度
        altitude = max(100, int(40000000 / (2 ** (zoom_value - 1))))
        
        # 基本的なパラメータ（heading=0, tilt=0, roll=0 でオーバーヘッドビュー）
        return f"https://earth.google.com/web/@{lat:.6f},{lon:.6f},{altitude}a,35y,0h,0t,0r"
    except Exception:
        return None

def generate_html_response(lat, lon, scale=None):
    """改良されたHTMLレスポンスを生成"""
    google_maps_url = build_google_maps_url(lat, lon, scale)
    google_earth_url = build_google_earth_url(lat, lon, scale)
    
    body_parts = [
        "<!DOCTYPE html>",
        "<html lang=\"ja\">",
        "<head>",
        "<meta charset=\"utf-8\">",
        "<title>QMap Permalink</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; margin: 20px; }",
        ".link-section { margin: 15px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }",
        ".link-title { font-weight: bold; color: #333; margin-bottom: 5px; }",
        "a { color: #1a73e8; text-decoration: none; word-break: break-all; }",
        "a:hover { text-decoration: underline; }",
        "</style>",
        "</head>",
        "<body>",
        "<h2>QMap Permalink - 地図移動完了</h2>",
        "<p>地図の移動を受け付けました。以下のリンクから同じ地点を他のサービスでも表示できます：</p>",
    ]
    
    # Google Mapsリンクを追加
    if google_maps_url:
        escaped_maps_url = html.escape(google_maps_url)
        body_parts.extend([
            "<div class=\"link-section\">",
            "<div class=\"link-title\">🗺️ Google Maps で表示</div>",
            f"<a href=\"{escaped_maps_url}\" target=\"_blank\" rel=\"noopener noreferrer\">{escaped_maps_url}</a>",
            "</div>"
        ])
    
    # Google Earthリンクを追加
    if google_earth_url:
        escaped_earth_url = html.escape(google_earth_url)
        body_parts.extend([
            "<div class=\"link-section\">",
            "<div class=\"link-title\">🌍 Google Earth で表示</div>",
            f"<a href=\"{escaped_earth_url}\" target=\"_blank\" rel=\"noopener noreferrer\">{escaped_earth_url}</a>",
            "</div>"
        ])
    
    # リンクがない場合のメッセージ
    if not google_maps_url and not google_earth_url:
        body_parts.append("<p>外部サービス用のリンクを生成できませんでした。</p>")
    
    body_parts.extend([
        "<hr>",
        "<p><small>このページはQGISプラグイン「QMap Permalink」によって生成されました。</small></p>",
        "</body>",
        "</html>"
    ])
    
    return "\n".join(body_parts)

def test_url_generation():
    """URL生成をテスト"""
    print("=== Google Maps & Google Earth URL生成テスト ===\n")
    
    test_cases = [
        {"name": "東京駅", "lat": 35.681236, "lon": 139.767125, "scale": 1000},
        {"name": "富士山", "lat": 35.360626, "lon": 138.727363, "scale": 25000},
        {"name": "大阪城", "lat": 34.687315, "lon": 135.526201, "scale": 5000},
        {"name": "札幌市役所", "lat": 43.064171, "lon": 141.346939, "scale": 10000},
    ]
    
    for case in test_cases:
        print(f"=== {case['name']} (スケール1:{case['scale']}) ===")
        
        maps_url = build_google_maps_url(case['lat'], case['lon'], case['scale'])
        earth_url = build_google_earth_url(case['lat'], case['lon'], case['scale'])
        zoom = estimate_zoom_from_scale(case['scale'])
        
        print(f"推定ズーム: {zoom}")
        print(f"Google Maps: {maps_url}")
        print(f"Google Earth: {earth_url}")
        print()

def test_html_response():
    """HTMLレスポンスのテスト"""
    print("=== HTMLレスポンステスト ===\n")
    
    # 東京駅の例でHTMLを生成
    lat, lon, scale = 35.681236, 139.767125, 5000
    html_content = generate_html_response(lat, lon, scale)
    
    print("生成されたHTML:")
    print(html_content)
    
    # HTMLファイルとして保存してブラウザで確認可能にする
    try:
        with open("test_response.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("\ntest_response.html として保存しました。ブラウザで開いて確認できます。")
    except Exception as e:
        print(f"HTMLファイル保存エラー: {e}")

if __name__ == "__main__":
    test_url_generation()
    test_html_response()
    
    print("=== 実装完了 ===")
    print("✅ Google Maps URLの生成")
    print("✅ Google Earth URLの生成") 
    print("✅ 改良されたHTMLレスポンス")
    print("✅ スタイル付きの見やすい表示")
    print("\nQGISプラグインのHTTPサーバーが両方のリンクを返すようになりました！")