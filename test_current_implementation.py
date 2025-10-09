#!/usr/bin/env python3
"""
現在の実装の実際の動作を確認するテスト
"""

import math

def current_implementation_zoom_from_scale(scale):
    """現在のqmap_permalink.pyの実装をそのまま再現"""
    if not scale:
        return 16.0
    try:
        s = float(scale)
        if s <= 0:
            return 16.0
        
        # Web Mercator標準の変換式
        base_scale = 156543033.9  # ズーム0の基準スケール（Web Mercator）
        zoom = math.log2(base_scale / s)
        
        # 1-20の範囲に制限（Google Mapsの有効範囲）
        return max(1.0, min(20.0, round(zoom, 1)))
        
    except (ValueError, TypeError, OverflowError):
        return 16.0

def old_table_zoom_from_scale(scale):
    """旧版の固定テーブル方式"""
    if not scale:
        return 16.0
    try:
        s = float(scale)
        if s <= 0:
            return 16.0

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

def test_comparison():
    """現在の実装と旧テーブルの比較テスト"""
    print("=== 現在の実装 vs 旧固定テーブルの比較 ===\n")
    
    # 実際のQGISでよく使われるスケール値
    test_scales = [500, 1000, 2500, 5000, 10000, 25000, 50000, 100000, 250000, 500000]
    
    print("スケール値 | 現在実装 | 旧テーブル | 差異 | 評価")
    print("-" * 60)
    
    for scale in test_scales:
        current_zoom = current_implementation_zoom_from_scale(scale)
        old_zoom = old_table_zoom_from_scale(scale)
        diff = current_zoom - old_zoom
        
        # 評価
        if abs(diff) < 0.5:
            evaluation = "🟢 ほぼ同じ"
        elif abs(diff) < 1.5:
            evaluation = "🟡 小さな差"
        elif abs(diff) < 3.0:
            evaluation = "🟠 中程度の差"
        else:
            evaluation = "🔴 大きな差"
            
        print(f"{scale:8} | {current_zoom:7.1f} | {old_zoom:9.0f} | {diff:+5.1f} | {evaluation}")
    
    print("\n=== 詳細分析 ===")
    print("現在の実装の特徴:")
    print("• Web Mercator標準式を使用")
    print("• 小数点ズームレベル対応（例：17.3）")
    print("• 1-20の範囲に制限")
    print("• 数学的に一貫した変換")
    
    print("\n旧テーブルの特徴:")
    print("• 固定された24個のスケール値")
    print("• 整数ズームのみ")
    print("• 0-30の範囲")
    print("• 不連続な変換")
    
    print("\n=== Google Maps との互換性比較 ===")
    print("Google Mapsの標準ズームレベルでの逆算テスト:")
    print("ズーム | Web標準スケール | 現在実装 | 旧テーブル | 現在実装の精度")
    print("-" * 75)
    
    base_scale = 156543033.9
    for zoom in [10, 12, 14, 16, 18, 20]:
        theoretical_scale = base_scale / (2 ** zoom)
        current_result = current_implementation_zoom_from_scale(theoretical_scale)
        old_result = old_table_zoom_from_scale(theoretical_scale)
        current_accuracy = abs(zoom - current_result)
        
        print(f"{zoom:5} | {theoretical_scale:13.0f} | {current_result:7.1f} | {old_result:9.0f} | {current_accuracy:13.1f}")

if __name__ == "__main__":
    test_comparison()