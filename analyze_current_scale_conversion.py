#!/usr/bin/env python3 
"""
現在のスケール変換の問題点を分析するスクリプト
"""

import math

def current_estimate_zoom_from_scale(scale):
    """現在の実装（複雑なテーブル方式）"""
    if not scale:
        return 16.0
    try:
        s = float(scale)
        if s <= 0:
            return 16.0

        # 参照スケール表を作成
        scale_table = {
            0: 400_000_000.0,
            1: 200_000_000.0,
            2: 100_000_000.0,
            3: 60_000_000.0,
            4: 30_000_000.0,
            5: 15_000_000.0,
            6: 8_000_000.0,
            7: 4_000_000.0,
            8: 2_000_000.0,
            9: 1_000_000.0,
            10: 400_000.0,
            11: 200_000.0,
            12: 100_000.0,
            13: 40_000.0,
            14: 20_000.0,
            15: 10_000.0,
            16: 5_000.0,
            17: 2_500.0,
            18: 1_250.0,
            19: 600.0,
            20: 300.0,
            21: 150.0,
            22: 75.0,
            23: 40.0,
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

def web_mercator_zoom_from_scale(scale):
    """Web Mercator標準のズーム変換"""
    if not scale:
        return 16.0
    try:
        s = float(scale)
        if s <= 0:
            return 16.0
        
        # Web Mercator標準式
        base_scale = 156543033.9  # ズーム0の基準スケール
        zoom = math.log2(base_scale / s)
        
        return max(1.0, min(20.0, round(zoom, 1)))
        
    except (ValueError, TypeError, OverflowError):
        return 16.0

def analyze_scale_conversion():
    """現在の変換方式を分析"""
    print("=== スケール変換の問題点分析 ===\n")
    
    # 典型的なQGISスケール値でテスト
    test_scales = [500, 1000, 2500, 5000, 10000, 25000, 50000, 100000]
    
    print("スケール値 | 現在の実装 | Web標準 | 差 | 問題点")
    print("-" * 60)
    
    for scale in test_scales:
        current_zoom = current_estimate_zoom_from_scale(scale)
        standard_zoom = web_mercator_zoom_from_scale(scale)
        diff = current_zoom - standard_zoom
        
        # 問題点を特定
        issues = []
        if abs(diff) > 2:
            issues.append("大きな差")
        if current_zoom == int(current_zoom):
            issues.append("整数のみ")
        
        problem_text = ", ".join(issues) if issues else "問題なし"
        
        print(f"{scale:8} | {current_zoom:10.1f} | {standard_zoom:7.1f} | {diff:+5.1f} | {problem_text}")
    
    print("\n=== 現在のテーブルの問題点 ===")
    print("1. **不自然なスケール値**: ズーム10で400,000、ズーム13で40,000など、")
    print("   Web地図の標準とは大きく異なる値が設定されています")
    print("2. **整数ズームのみ**: 小数点のズームレベルが返されず、粗い変換しかできません")  
    print("3. **不連続な変化**: 隣接するズームレベル間でスケールが大きく跳ぶ場合があります")
    print("4. **Web標準からの乖離**: Google Maps等で使われる標準的なスケール変換と一致しません")
    
    print("\n=== スケールテーブルの詳細分析 ===")
    scale_table = {
        0: 400_000_000.0, 1: 200_000_000.0, 2: 100_000_000.0, 3: 60_000_000.0, 4: 30_000_000.0,
        5: 15_000_000.0, 6: 8_000_000.0, 7: 4_000_000.0, 8: 2_000_000.0, 9: 1_000_000.0,
        10: 400_000.0, 11: 200_000.0, 12: 100_000.0, 13: 40_000.0, 14: 20_000.0,
        15: 10_000.0, 16: 5_000.0, 17: 2_500.0, 18: 1_250.0, 19: 600.0,
        20: 300.0, 21: 150.0, 22: 75.0, 23: 40.0,
    }
    
    print("ズーム | テーブル値 | Web標準値 | 比率差")
    print("-" * 40)
    base_scale = 156543033.9
    for zoom in range(0, 24):
        table_scale = scale_table[zoom]
        web_scale = base_scale / (2 ** zoom)
        ratio = table_scale / web_scale
        print(f"{zoom:5} | {table_scale:10.0f} | {web_scale:9.0f} | {ratio:6.2f}x")
    
    print("\n=== 推奨改善策 ===")
    print("1. Web Mercator標準式を使用: zoom = log₂(156543033.9 / scale)")
    print("2. 小数点ズームレベルをサポート")
    print("3. Google Maps等との互換性向上")
    print("4. より滑らかで予測可能な変換")

if __name__ == "__main__":
    analyze_scale_conversion()