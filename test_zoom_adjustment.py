#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ズームレベル調整版のスケール変換テスト
「ズームレベルが小さく表示される」問題を解決するためのテスト
"""

import math

def estimate_zoom_adjusted_higher(scale):
    """ズームレベルを高く調整したスケール変換"""
    if not scale:
        return 16.0
    try:
        s = float(scale)
        if s <= 0:
            return 16.0

        # 調整版: より高いズームレベルになるよう調整した固定スケールテーブル
        # 元のテーブルより1-2レベル高く設定
        scale_table = {
            0: 400_000_000.0, 1: 200_000_000.0, 2: 100_000_000.0, 3: 60_000_000.0, 4: 30_000_000.0,
            5: 15_000_000.0, 6: 8_000_000.0, 7: 4_000_000.0, 8: 2_000_000.0, 9: 1_000_000.0,
            # ここから調整（元より1-2レベル高くシフト）
            10: 600_000.0,    # 元: 400_000.0
            11: 300_000.0,    # 元: 200_000.0  
            12: 150_000.0,    # 元: 100_000.0
            13: 75_000.0,     # 元: 40_000.0 → より詳細に
            14: 40_000.0,     # 元: 20_000.0 → 2倍詳細
            15: 20_000.0,     # 元: 10_000.0 → 2倍詳細
            16: 10_000.0,     # 元: 5_000.0 → 2倍詳細
            17: 5_000.0,      # 元: 2_500.0 → 2倍詳細
            18: 2_500.0,      # 元: 1_250.0 → 2倍詳細
            19: 1_250.0,      # 元: 600.0 → より詳細に
            20: 600.0,        # 元: 300.0 → 2倍詳細
            21: 300.0,        # 元: 150.0 → 2倍詳細
            22: 150.0,        # 元: 75.0 → 2倍詳細
            23: 75.0,         # 元: 40.0 → やや詳細に
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

def estimate_zoom_original(scale):
    """元の実装: QGIS実スケール対応の固定スケールテーブル"""
    if not scale:
        return 16.0
    try:
        s = float(scale)
        if s <= 0:
            return 16.0

        # 元のQGIS実スケール対応の固定スケールテーブル
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

def compare_zoom_adjustments():
    """ズーム調整版の比較テスト"""
    print("=== ズームレベル調整版の比較 ===\n")
    
    # テスト用のスケール値（典型的なQGISスケール）
    test_scales = [
        500, 1000, 2500, 5000, 10000, 25000, 50000,
        100000, 250000, 500000, 1000000, 2500000
    ]
    
    print("スケール値 | 元実装 | 調整版 | 差異 | Google感覚")
    print("-" * 50)
    
    google_expected = {
        500: 20, 1000: 19, 2500: 17, 5000: 16, 10000: 15, 25000: 13, 50000: 12,
        100000: 11, 250000: 10, 500000: 9, 1000000: 8, 2500000: 7
    }
    
    for scale in test_scales:
        zoom_original = estimate_zoom_original(scale)
        zoom_adjusted = estimate_zoom_adjusted_higher(scale)
        diff = zoom_adjusted - zoom_original
        google_zoom = google_expected.get(scale, "?")
        
        print(f"{scale:>8} | {zoom_original:>6.0f} | {zoom_adjusted:>6.0f} | {diff:>+4.0f} | {google_zoom:>8}")

def test_practical_scenarios():
    """実用的なシナリオでのテスト"""
    print("\n=== 実用シナリオテスト ===\n")
    
    scenarios = [
        ("建物詳細（1:500）", 500),
        ("街区詳細（1:1000）", 1000),
        ("近隣地区（1:5000）", 5000),
        ("市街地（1:10000）", 10000),
        ("市全体（1:100000）", 100000),
        ("県全体（1:1000000）", 1000000),
    ]
    
    print("シナリオ                | スケール | 元実装 | 調整版 | 改善")
    print("-" * 60)
    
    for name, scale in scenarios:
        zoom_original = estimate_zoom_original(scale)
        zoom_adjusted = estimate_zoom_adjusted_higher(scale)
        improvement = zoom_adjusted - zoom_original
        
        print(f"{name:<20} | {scale:>7} | {zoom_original:>6.0f} | {zoom_adjusted:>6.0f} | {improvement:>+4.0f}")

if __name__ == "__main__":
    compare_zoom_adjustments()
    test_practical_scenarios()
    
    print("\n=== 調整案の提案 ===")
    print("1. 現在の固定テーブルをより詳細（高ズーム）方向に調整")
    print("2. 特に市街地スケール（1:5000〜1:25000）でズーム+1〜2レベル")
    print("3. 詳細スケール（1:500〜1:2500）でズーム+1レベル")
    print("4. これにより「小さく表示される」問題が改善される可能性があります")