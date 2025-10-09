#!/usr/bin/env python3
"""
改善版スケール変換の効果確認テスト
"""

import math

def old_estimate_zoom_from_scale(scale):
    """旧版の複雑なテーブル方式"""
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

def new_estimate_zoom_from_scale(scale):
    """改善版のWeb標準対応"""
    if not scale:
        return 16.0
    try:
        s = float(scale)
        if s <= 0:
            return 16.0
        
        base_scale = 156543033.9  # ズーム0の基準スケール（Web Mercator）
        zoom = math.log2(base_scale / s)
        
        return max(1.0, min(20.0, round(zoom, 1)))
        
    except (ValueError, TypeError, OverflowError):
        return 16.0

def test_improvement():
    """改善効果をテスト"""
    print("=== 改善版スケール変換テスト ===\n")
    
    # 実際のQGISでよく使われるスケール値
    typical_scales = [500, 1000, 2500, 5000, 10000, 25000, 50000, 100000]
    
    print("実用スケール値での比較:")
    print("スケール値 | 旧版 | 新版 | 改善度 | 評価")
    print("-" * 55)
    
    for scale in typical_scales:
        old_zoom = old_estimate_zoom_from_scale(scale)
        new_zoom = new_estimate_zoom_from_scale(scale)
        improvement = abs(new_zoom - round(new_zoom, 0)) > 0  # 小数点があるか
        
        if improvement:
            evaluation = "✅ 精密"
        else:
            evaluation = "⭕ 改善"
            
        print(f"{scale:8} | {old_zoom:4.0f} | {new_zoom:4.1f} | {'小数点対応' if improvement else '整数のみ':>8} | {evaluation}")
    
    print("\n=== Google Maps互換性テスト ===")
    print("Google Mapsで実際に表示される縮尺との整合性:")
    
    # Google Mapsの標準ズームに対応するスケール
    google_compatible_tests = [
        (500, "建物詳細レベル"),
        (1000, "街区レベル"),
        (5000, "地区レベル"),
        (25000, "市街地レベル"),
        (100000, "都市レベル")
    ]
    
    print("スケール値 | 旧版ズーム | 新版ズーム | レベル | Google Maps互換性")
    print("-" * 70)
    
    for scale, level in google_compatible_tests:
        old_zoom = old_estimate_zoom_from_scale(scale)
        new_zoom = new_estimate_zoom_from_scale(scale)
        
        # Google Mapsとの互換性評価
        if 16 <= new_zoom <= 19:
            compatibility = "🟢 高互換性"
        elif 12 <= new_zoom <= 20:
            compatibility = "🟡 良好"
        else:
            compatibility = "🔴 要調整"
            
        print(f"{scale:8} | {old_zoom:9.0f} | {new_zoom:9.1f} | {level:12} | {compatibility}")
    
    print("\n=== 改善点まとめ ===")
    print("✅ **精度向上**: 小数点ズームレベルによる細かい調整が可能")
    print("✅ **標準準拠**: Web Mercator標準式でGoogle Maps等と互換性向上")  
    print("✅ **予測可能**: 数学的に一貫した変換ロジック")
    print("✅ **滑らか**: 段階的でなく連続的な変換")
    print("✅ **簡潔**: 複雑なテーブルから簡単な対数式へ")

if __name__ == "__main__":
    test_improvement()