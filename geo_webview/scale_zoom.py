"""Pure-Python scale/zoom estimation utilities.

This module contains functions that convert between map scale denominators
and Web/Google-style zoom levels. It intentionally avoids importing QGIS
APIs so it can be used by helper modules that run outside a QGIS runtime
(for example the MapLibre HTML generator / test harness).

The repository also records a small set of canonical, human-oriented
zoom→scale reference values (provided by the user) below as
``STANDARD_ZOOM_SCALE_REFERENCE``. These are intended as a readable
reference and tuning guide; the conversion functions below keep their
existing behaviour unless you explicitly change them to use this
reference.

ズームとスケールの標準換算値（ユーザー提供）:

Zoom (ズーム)  | 概略縮尺 (スケール)
--------------+---------------------
0             |  1:500,000,000
5             |  1:10,000,000
10            |  1:500,000
12            |  1:150,000
14            |  1:40,000
16            |  1:10,000
18            |  1:2,000
20            |  1:500
22            |  1:100
24            |  1:25
28            |  1:1

If you want the conversion algorithms to use these exact anchors you can
either (a) replace the internal scale tables in the functions below with
this constant or (b) write a small wrapper that maps through these
anchors and interpolates. For now this constant is provided as a
documented reference only.
"""


import math

# --- Human-oriented reference (user-provided) --------------------------------
# A compact set of canonical zoom -> scale anchors supplied by the user.
# This is intentionally advisory/documentary; the functions below retain
# their existing internal scale tables unless adapted to use these
# anchors.
STANDARD_ZOOM_SCALE_REFERENCE = {
    0: 500_000_000.0,
    5: 10_000_000.0,
    10: 500_000.0,
    12: 150_000.0,
    14: 40_000.0,
    16: 10_000.0,
    18: 2_000.0,
    20: 500.0,
    22: 100.0,
    24: 25.0,
    28: 1.0,
}

# MapLibre-specific reference table. Start as a copy of the project standard
# anchors but kept separate so MapLibre tuning does not affect the generic
# reference. You can modify MAPLIBRE_ZOOM_SCALE_REFERENCE independently.
MAPLIBRE_ZOOM_SCALE_REFERENCE = {
    0: 500_000_000.0,
    5: 10_000_000.0,
    8.38: 1_000_000.0,
    9.28: 500_000.0,
    10.29: 250_000.0,
    11.50: 100_000.0,
    12.56: 50_000.0,
    13.62: 25_000.0,
    14.98: 10_000.0,
    15.89: 5_000.0,
    16.29: 2_500.0,
    18.29: 1_000.0,
    19.24: 500.0,
    20.16: 250.0,
    21.66: 100.0,
    24: 25.0,
    28: 1.0,
}



def estimate_zoom_from_scale(scale):
    """Estimate a continuous zoom level from a scale denominator.

    Args:
        scale: numeric scale denominator (e.g. 10000 for 1:10000). If falsy,
               returns a sensible default (16.0).

    Returns:
        float: estimated zoom level (may be fractional).
    """
    if not scale:
        return 16.0
    try:
        s = float(scale)
        if s <= 0:
            return 16.0

        scale_table = {
            0: 400_000_000.0, 1: 200_000_000.0, 2: 100_000_000.0, 3: 60_000_000.0, 4: 30_000_000.0,
            5: 15_000_000.0, 6: 8_000_000.0, 7: 4_000_000.0, 8: 2_000_000.0, 9: 1_000_000.0,
            10: 600_000.0, 11: 300_000.0, 12: 150_000.0, 13: 75_000.0, 14: 40_000.0,
            15: 20_000.0, 16: 10_000.0, 17: 5_000.0, 18: 2_500.0, 19: 1_250.0,
            20: 600.0, 21: 300.0, 22: 150.0, 23: 75.0,
        }

        # extrapolate higher zooms
        for z in range(24, 31):
            scale_table[z] = scale_table[23] / (2 ** (z - 23))

        target_log = math.log(s)
        zoom_levels = sorted(scale_table.keys())

        if s >= scale_table[zoom_levels[0]]:
            return float(zoom_levels[0])
        if s <= scale_table[zoom_levels[-1]]:
            return float(zoom_levels[-1])

        for i in range(len(zoom_levels) - 1):
            z1, z2 = zoom_levels[i], zoom_levels[i + 1]
            s1, s2 = scale_table[z1], scale_table[z2]
            if s1 >= s >= s2:
                log_s1, log_s2 = math.log(s1), math.log(s2)
                t = (target_log - log_s1) / (log_s2 - log_s1) if log_s2 != log_s1 else 0.0
                interpolated_zoom = z1 + t * (z2 - z1)
                return max(0.0, min(30.0, interpolated_zoom))

        return 16.0

    except (ValueError, TypeError, OverflowError):
        return 16.0


def estimate_scale_from_zoom(zoom_level):
    """Estimate a scale denominator from a (possibly fractional) zoom level.

    Args:
        zoom_level: numeric zoom level (can be fractional). If None, returns
                    a sensible default (20000.0).

    Returns:
        float: estimated scale denominator.
    """
    if zoom_level is None:
        return 20000.0
    try:
        z = float(zoom_level)
        scale_table = {
            0: 400_000_000.0, 1: 200_000_000.0, 2: 100_000_000.0, 3: 60_000_000.0, 4: 30_000_000.0,
            5: 15_000_000.0, 6: 8_000_000.0, 7: 4_000_000.0, 8: 2_000_000.0, 9: 1_000_000.0,
            10: 600_000.0, 11: 300_000.0, 12: 150_000.0, 13: 75_000.0, 14: 40_000.0,
            15: 20_000.0, 16: 10_000.0, 17: 5_000.0, 18: 2_500.0, 19: 1_250.0,
            20: 600.0, 21: 300.0, 22: 150.0, 23: 75.0,
        }
        for zoom in range(24, 31):
            scale_table[zoom] = scale_table[23] / (2 ** (zoom - 23))

        z = max(0.0, min(30.0, z))
        if z == int(z) and int(z) in scale_table:
            return scale_table[int(z)]

        z_floor = int(math.floor(z))
        z_ceil = int(math.ceil(z))
        if z_floor < 0:
            z_floor = 0
        if z_ceil > 30:
            z_ceil = 30
        if z_floor not in scale_table:
            z_floor = max([k for k in scale_table.keys() if k <= z_floor], default=0)
        if z_ceil not in scale_table:
            z_ceil = min([k for k in scale_table.keys() if k >= z_ceil], default=30)
        if z_floor == z_ceil:
            return scale_table.get(z_floor, 20000.0)

        s1, s2 = scale_table[z_floor], scale_table[z_ceil]
        log_s1, log_s2 = math.log(s1), math.log(s2)
        t = (z - z_floor) / (z_ceil - z_floor) if z_ceil != z_floor else 0.0
        interpolated_log_scale = log_s1 + t * (log_s2 - log_s1)
        interpolated_scale = math.exp(interpolated_log_scale)
        return interpolated_scale

    except (ValueError, TypeError, OverflowError):
        return 20000.0


# --- Helpers to expand the human reference into a full integer zoom table ---
def _expand_reference_to_table(ref, min_zoom=0, max_zoom=30):
    """Expand a sparse zoom->scale reference to a full integer table.

    Uses log-linear interpolation between provided anchors and
    halving/doubling behaviour beyond the highest/lowest anchors.
    """
    if not ref:
        return {}

    anchors = sorted(ref.keys())
    min_anchor, max_anchor = anchors[0], anchors[-1]

    table = {}
    # Precompute logs for anchors to speed interpolation
    log_ref = {z: math.log(ref[z]) for z in anchors}

    for z in range(min_zoom, max_zoom + 1):
        if z in ref:
            table[z] = float(ref[z])
            continue

        if z < min_anchor:
            # extrapolate towards lower zooms (bigger scales): double per step
            table[z] = float(ref[min_anchor] * (2 ** (min_anchor - z)))
            continue

        if z > max_anchor:
            # extrapolate beyond highest anchor: halve per step
            table[z] = float(ref[max_anchor] / (2 ** (z - max_anchor)))
            continue

        # find neighbouring anchors za < z < zb
        za = max([a for a in anchors if a < z], default=min_anchor)
        zb = min([a for a in anchors if a > z], default=max_anchor)
        if za == zb:
            table[z] = float(ref.get(za, 1.0))
            continue

        # log-linear interpolation
        log_za, log_zb = log_ref[za], log_ref[zb]
        t = (z - za) / float(zb - za)
        log_s = log_za + t * (log_zb - log_za)
        table[z] = float(math.exp(log_s))

    return table


# --- MapLibre-specific copies -------------------------------------------------
# The following functions are duplicated versions of the generic utilities
# so consumers that are MapLibre-specific can import and customize them
# independently without affecting the generic implementations used elsewhere.
def estimate_zoom_from_scale_maplibre(scale):
    """MapLibre-specific wrapper: duplicated implementation of
    estimate_zoom_from_scale so it can be freely modified for MapLibre
    behaviour without changing the generic utility.
    """
    # Implementation duplicated from estimate_zoom_from_scale above.
    if not scale:
        return 16.0
    try:
        s = float(scale)
        if s <= 0:
            return 16.0

        # Build a full integer zoom->scale table from the MapLibre-specific
        # reference. This produces entries for 0..30 (inclusive) using
        # log-linear interpolation between anchors and halving/doubling
        # beyond the anchor range.
        scale_table = _expand_reference_to_table(MAPLIBRE_ZOOM_SCALE_REFERENCE, 0, 30)

        target_log = math.log(s)
        zoom_levels = sorted(scale_table.keys())

        if s >= scale_table[zoom_levels[0]]:
            return float(zoom_levels[0])
        if s <= scale_table[zoom_levels[-1]]:
            return float(zoom_levels[-1])

        for i in range(len(zoom_levels) - 1):
            z1, z2 = zoom_levels[i], zoom_levels[i + 1]
            s1, s2 = scale_table[z1], scale_table[z2]
            if s1 >= s >= s2:
                log_s1, log_s2 = math.log(s1), math.log(s2)
                t = (target_log - log_s1) / (log_s2 - log_s1) if log_s2 != log_s1 else 0.0
                interpolated_zoom = z1 + t * (z2 - z1)
                return max(0.0, min(30.0, interpolated_zoom))

        return 16.0

    except (ValueError, TypeError, OverflowError):
        return 16.0


def estimate_scale_from_zoom_maplibre(zoom_level):
    """MapLibre-specific duplicated implementation of estimate_scale_from_zoom.

    Kept separate so MapLibre behaviour can be tuned independently.
    """
    # Implementation duplicated from estimate_scale_from_zoom above.
    if zoom_level is None:
        return 20000.0
    try:
        z = float(zoom_level)
        # Use the MapLibre-specific expanded table.
        scale_table = _expand_reference_to_table(MAPLIBRE_ZOOM_SCALE_REFERENCE, 0, 30)

        z = max(0.0, min(30.0, z))
        if z == int(z) and int(z) in scale_table:
            return scale_table[int(z)]

        z_floor = int(math.floor(z))
        z_ceil = int(math.ceil(z))
        if z_floor < 0:
            z_floor = 0
        if z_ceil > 30:
            z_ceil = 30
        if z_floor not in scale_table:
            z_floor = max([k for k in scale_table.keys() if k <= z_floor], default=0)
        if z_ceil not in scale_table:
            z_ceil = min([k for k in scale_table.keys() if k >= z_ceil], default=30)
        if z_floor == z_ceil:
            return scale_table.get(z_floor, 20000.0)

        s1, s2 = scale_table[z_floor], scale_table[z_ceil]
        log_s1, log_s2 = math.log(s1), math.log(s2)
        t = (z - z_floor) / (z_ceil - z_floor) if z_ceil != z_floor else 0.0
        interpolated_log_scale = log_s1 + t * (log_s2 - log_s1)
        interpolated_scale = math.exp(interpolated_log_scale)
        return interpolated_scale

    except (ValueError, TypeError, OverflowError):
        return 20000.0
