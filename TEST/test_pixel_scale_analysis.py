#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ピクセルサイズとスケール変換の影響を解析するスクリプト
"""

import math

def estimate_zoom_from_scale_current(scale):
    """現在の実装: QGIS実スケール対応の固定スケールテーブル"""
    if not scale:
        return 16.0
    try:
        s = float(scale)
        if s <= 0:
            return 16.0

        # QGIS実スケール対応の固定スケールテーブル
        scale_table = {
            0: 400_000_000.0, 1: 200_000_000.0, 2: 100_000_000.0, 3: 60_000_000.0, 4: 30_000_000.0,
            5: 15_000_000.0, 6: 8_000_000.0, 7: 4_000_000.0, 8: 2_000_000.0, 9: 1_000_000.0,
            10: 400_000.0, 11: 200_000.0, 12: 100_000.0, 13: 40_000.0, 14: 20_000.0,
            15: 10_000.0, 16: 5_000.0, 17: 2_500.0, 18: 1_250.0, 19: 600.0,
            20: 300.0, 21: 150.0, 22: 75.0, 23: 40.0,
        }

        # 外挿: 24-30 は 23 の値を半分ずつ外挿
        for z in range(24, 31):
            scale_table[z] = scale_table[23] / (2 ** (z - 23))

        # 比較は対数空間（スケールの比率差）で行う方が自然
        target_log = math.log(s)
        best_zoom = 16
        best_diff = None
        for z, zscale in scale_table.items():
            diff = abs(math.log(zscale) - target_log)
            if best_diff is None or diff < best_diff:
                best_diff = diff
                best_zoom = z

        # clamp 0..30
        return max(0, min(30, int(best_zoom)))
    except (ValueError, TypeError, OverflowError):
        return 16.0

def estimate_zoom_web_mercator_standard(scale):
    """Web Mercator標準式によるズーム推定"""
    if not scale:
        return 16.0
    try:
        s = float(scale)
        if s <= 0:
            return 16.0
        
        # Web Mercator標準: 赤道での1ピクセルあたりのメートル数
        base_scale = 156543033.9  # zoom 0での基準値
        zoom = math.log2(base_scale / s)
        return max(0, min(30, round(zoom)))
    except (ValueError, TypeError, OverflowError):
        return 16.0

def estimate_zoom_pixel_adjusted(scale, dpi=96):
    """画面DPI調整版のズーム推定"""
    if not scale:
        return 16.0
    try:
        s = float(scale)
        if s <= 0:
            return 16.0
        
        # DPI調整係数 (標準96dpiからの比率)
        dpi_factor = dpi / 96.0
        
        # 調整されたスケール
        adjusted_scale = s * dpi_factor
        
        # Web Mercator標準式を適用
        base_scale = 156543033.9
        zoom = math.log2(base_scale / adjusted_scale)
        return max(0, min(30, round(zoom)))
    except (ValueError, TypeError, OverflowError):
        return 16.0

def analyze_scale_differences():
    """異なるスケール変換方式の比較分析"""
    print("=== スケール変換方式の比較分析 ===\n")
    
    # テスト用のスケール値（典型的なQGISスケール）
    test_scales = [
        1000, 2500, 5000, 10000, 25000, 50000,
        100000, 250000, 500000, 1000000, 2500000, 5000000
    ]
    
    print("スケール値 | 現在実装 | Web標準 | DPI120調整 | DPI144調整")
    print("-" * 60)
    
    for scale in test_scales:
        zoom_current = estimate_zoom_from_scale_current(scale)
        zoom_web = estimate_zoom_web_mercator_standard(scale)
        zoom_dpi120 = estimate_zoom_pixel_adjusted(scale, 120)
        zoom_dpi144 = estimate_zoom_pixel_adjusted(scale, 144)
        
        print(f"{scale:>8} | {zoom_current:>8.1f} | {zoom_web:>7.1f} | {zoom_dpi120:>10.1f} | {zoom_dpi144:>10.1f}")

def analyze_reverse_conversion():
    """逆変換の分析（ズームレベルからスケールへ）"""
    print("\n=== 逆変換分析（ズーム→スケール） ===\n")
    
    # 現在の固定テーブル
    scale_table = {
        10: 400_000.0, 11: 200_000.0, 12: 100_000.0, 13: 40_000.0, 14: 20_000.0,
        15: 10_000.0, 16: 5_000.0, 17: 2_500.0, 18: 1_250.0, 19: 600.0,
        20: 300.0, 21: 150.0, 22: 75.0, 23: 40.0,
    }
    
    print("ズーム | 固定テーブル | Web標準式 | 差異率(%)")
    print("-" * 45)
    
    for zoom in range(10, 24):
        if zoom in scale_table:
            fixed_scale = scale_table[zoom]
        else:
            # 外挿計算
            fixed_scale = scale_table[23] / (2 ** (zoom - 23))
        
        # Web標準式での逆算
        base_scale = 156543033.9
        web_scale = base_scale / (2 ** zoom)
        
        # 差異率計算
        diff_percent = ((web_scale - fixed_scale) / fixed_scale) * 100
        
        print(f"{zoom:>4} | {fixed_scale:>11.1f} | {web_scale:>9.1f} | {diff_percent:>7.1f}")

def test_typical_qgis_scenarios():
    """典型的なQGISシナリオでのテスト"""
    print("\n=== 典型的なQGISシナリオテスト ===\n")
    
    scenarios = [
        ("都市部詳細表示", 1000),
        ("街区レベル", 5000),
        ("市区町村レベル", 25000),
        ("県レベル", 500000),
        ("全国レベル", 5000000),
    ]
    
    print("シナリオ           | スケール | 現在ズーム | 期待ズーム | 差異")
    print("-" * 65)
    
    for name, scale in scenarios:
        current_zoom = estimate_zoom_from_scale_current(scale)
        
        # 経験的な期待値（Google Mapsでの一般的な対応）
        expected_zoom_map = {
            1000: 19,      # 詳細な建物レベル
            5000: 16,      # 街区レベル
            25000: 13,     # 地区レベル
            500000: 10,    # 市レベル
            5000000: 7,    # 県レベル
        }
        
        expected = expected_zoom_map.get(scale, current_zoom)
        diff = current_zoom - expected
        
        print(f"{name:<15} | {scale:>7} | {current_zoom:>8.1f} | {expected:>8} | {diff:>+4.1f}")

if __name__ == "__main__":
    analyze_scale_differences()
    analyze_reverse_conversion()
    test_typical_qgis_scenarios()
    
    print("\n=== 分析結果サマリー ===")
    print("1. 現在の固定テーブル方式とWeb標準式には大きな差異があります")
    print("2. 高DPI環境では画面の物理的なピクセルサイズが影響する可能性があります")
    print("3. QGISとGoogle Mapsのスケール感覚には根本的な違いがあります")
    print("4. 'ズームレベルが小さく表示される'問題は、スケール対応表の調整が必要かもしれません")