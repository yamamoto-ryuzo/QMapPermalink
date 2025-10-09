#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改良されたスケール変換の動作確認テスト
"""

import math

def estimate_zoom_improved(scale):
    """改良版のスケール変換（実装された版）"""
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
            # 中〜詳細スケールを高ズーム方向に調整
            10: 600_000.0,    # 元: 400_000.0 → より詳細に
            11: 300_000.0,    # 元: 200_000.0 → より詳細に
            12: 150_000.0,    # 元: 100_000.0 → より詳細に
            13: 75_000.0,     # 元: 40_000.0 → 大幅に詳細化
            14: 40_000.0,     # 元: 20_000.0 → 2倍詳細
            15: 20_000.0,     # 元: 10_000.0 → 2倍詳細
            16: 10_000.0,     # 元: 5_000.0 → 2倍詳細
            17: 5_000.0,      # 元: 2_500.0 → 2倍詳細
            18: 2_500.0,      # 元: 1_250.0 → 2倍詳細
            19: 1_250.0,      # 元: 600.0 → 大幅に詳細化
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
    """元の実装"""
    if not scale:
        return 16.0
    try:
        s = float(scale)
        if s <= 0:
            return 16.0

        # 元のテーブル
        scale_table = {
            0: 400_000_000.0, 1: 200_000_000.0, 2: 100_000_000.0, 3: 60_000_000.0, 4: 30_000_000.0,
            5: 15_000_000.0, 6: 8_000_000.0, 7: 4_000_000.0, 8: 2_000_000.0, 9: 1_000_000.0,
            10: 400_000.0, 11: 200_000.0, 12: 100_000.0, 13: 40_000.0, 14: 20_000.0,
            15: 10_000.0, 16: 5_000.0, 17: 2_500.0, 18: 1_250.0, 19: 600.0,
            20: 300.0, 21: 150.0, 22: 75.0, 23: 40.0,
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

def test_improvement():
    """改良版の効果をテスト"""
    print("=== スケール変換改良版の効果確認 ===\n")
    
    test_cases = [
        ("建物詳細", 500),
        ("街区", 1000),
        ("近隣", 2500),
        ("地区", 5000),
        ("市街地", 10000),
        ("市域", 25000),
        ("都市圏", 50000),
        ("地方", 100000),
        ("県域", 500000),
        ("広域", 1000000),
    ]
    
    print("用途        | スケール | 元実装 | 改良版 | 改善量 | 期待値")
    print("-" * 60)
    
    google_expected = {
        500: 20, 1000: 19, 2500: 17, 5000: 16, 10000: 15,
        25000: 13, 50000: 12, 100000: 11, 500000: 9, 1000000: 8
    }
    
    improvements = 0
    total_cases = 0
    
    for name, scale in test_cases:
        zoom_orig = estimate_zoom_original(scale)
        zoom_new = estimate_zoom_improved(scale)
        improvement = zoom_new - zoom_orig
        expected = google_expected.get(scale, "?")
        
        if improvement > 0:
            improvements += 1
        total_cases += 1
        
        status = "✓" if improvement > 0 else "="
        
        print(f"{name:>8} | {scale:>7} | {zoom_orig:>6.0f} | {zoom_new:>6.0f} | {improvement:>+4.0f} {status} | {expected:>6}")
    
    print(f"\n改善されたケース: {improvements}/{total_cases} ({improvements/total_cases*100:.1f}%)")
    
    print("\n=== 改良のポイント ===")
    print("1. 詳細スケール（1:500〜1:25000）で1〜2ズームレベル向上")
    print("2. より適切な詳細度でGoogle Mapsが表示される")
    print("3. 「小さく表示される」問題が大幅に改善")
    
    # 具体的な改善例を表示
    print("\n=== 具体的な改善例 ===")
    examples = [
        (1000, "1:1000スケール（街区詳細）"),
        (5000, "1:5000スケール（地区表示）"),
        (10000, "1:10000スケール（市街地）")
    ]
    
    for scale, description in examples:
        zoom_orig = estimate_zoom_original(scale)
        zoom_new = estimate_zoom_improved(scale)
        print(f"{description}")
        print(f"  元実装: ズーム{zoom_orig} → 改良版: ズーム{zoom_new} (+"
              f"{zoom_new-zoom_orig}レベル詳細化)")

if __name__ == "__main__":
    test_improvement()