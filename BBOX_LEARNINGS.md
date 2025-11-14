# BBOX Serverから学んだ最適化手法

## 概要

BBOX ServerはRustで実装された高性能OGC APIサーバーです。QMapPermalinkへの直接統合は推奨しませんが、その設計思想は参考になります。

## なぜBBOXバイナリ統合は推奨しないか

### 1. 配布の複雑さ
- 3プラットフォーム分のバイナリ（各30MB+）が必要
- QGISプラグインとしては過大（通常5-10MB）
- 自動更新の実装が困難

### 2. 機能の重複
QMapPermalinkは既に以下を持っています:
- ✅ WMS/WMTS サーバー (ポート8089)
- ✅ MBTiles キャッシング
- ✅ 並列タイル生成 (4スレッド)
- ✅ スタイル変更検出

BBOX Serverを追加すると:
- ポート競合 (8080 vs 8089)
- プロセス管理の複雑化
- 機能重複によるメンテナンス負荷

### 3. より良い代替案
BBOX Serverの**アルゴリズムとベストプラクティス**をPythonで実装する方が実用的。

---

## 学ぶべき優れた設計

### 1. MVT (Mapbox Vector Tiles) 最適化

#### ジオメトリ簡略化
```python
# ズームレベル別トレランス
tolerance = pixel_width / 2

# BBOX Serverの実装 (Rust)
# ST_AsMvtGeom(geom, bbox, tile_size, buffer, clip_geom)
```

**QMapPermalinkでの実装例:**
```python
def get_tolerance(self, zoom: int) -> float:
    n = 2.0 ** zoom
    pixel_width = 40075016.686 / (n * 256)
    return pixel_width / 2
```

#### バッファリング
```rust
// BBOX Server: 境界でのクリッピング防止
buffer_size: Option<u32>,  // デフォルト: 0-64 pixels
```

**用途:**
- タイル境界でジオメトリが切れるのを防ぐ
- ラベルやシンボルの表示品質向上

### 2. タイルキャッシング戦略

#### MBTiles 最適化
```rust
// 重複排除: blake3ハッシュでタイル内容を識別
let hash = blake3::hash(tile_data).to_hex();

// 正規化スキーマ
CREATE TABLE images (
    tile_id TEXT PRIMARY KEY,
    tile_data BLOB
);
CREATE TABLE map (
    zoom_level INTEGER,
    tile_column INTEGER,
    tile_row INTEGER,
    tile_id TEXT
);
```

**QMapPermalinkへの適用:**
- 既存のMBTilesキャッシュに重複排除を追加
- ディスク使用量を30-50%削減可能

#### バッチ書き込み
```rust
// BBOX Server: 200タイルまとめて書き込み
pipeline.batch(200).pump(TileBatchWriterPump {
    writer: tile_writer,
})
```

**QMapPermalinkでの実装:**
```python
# 現在: 1タイルずつ書き込み
# 改善: バッチ処理で高速化
def write_tile_batch(self, tiles: List[Tuple[int, int, int, bytes]]):
    with sqlite3.connect(self.mbtiles_path) as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO tiles VALUES (?, ?, ?, ?)",
            tiles
        )
```

### 3. PostGIS統合 (将来的な拡張)

#### ST_AsMvt の活用
```sql
-- BBOX Serverのクエリパターン
SELECT ST_AsMvtGeom(
    geom,
    ST_MakeEnvelope($1, $2, $3, $4, 3857),
    4096,  -- tile_size
    64,    -- buffer
    true   -- clip_geom
) AS geom
FROM layer_table
WHERE geom && ST_MakeEnvelope($1, $2, $3, $4, 3857)
```

**メリット:**
- PostGIS側でジオメトリ処理（高速）
- ネットワーク転送量削減
- QGISレンダリング負荷軽減

### 4. 並列処理

#### BBOX Serverのアプローチ
```rust
// 読み込み: 最大並列度
.map(tile_fn, Concurrency::concurrent_unordered(threads))

// 書き込み: S3は256並列、ファイルは制限なし
```

**QMapPermalinkの現状:**
```python
# 既に実装済み
self._prewarm_executor = ThreadPoolExecutor(max_workers=4)
```

**改善案:**
- 読み込みと書き込みで異なる並列度
- I/Oバウンド処理は高並列度可能

---

## 実装推奨度

| 機能 | 優先度 | 実装難易度 | 効果 |
|------|--------|----------|------|
| ジオメトリ簡略化 | ⭐⭐⭐ | 中 | 高 (転送量削減) |
| MBTiles重複排除 | ⭐⭐⭐ | 低 | 中 (ストレージ削減) |
| バッチ書き込み | ⭐⭐ | 低 | 中 (速度向上) |
| MVTサポート | ⭐⭐ | 高 | 高 (WebGL対応) |
| PostGIS統合 | ⭐ | 高 | 中 (大規模データ向け) |

---

## QMapPermalinkへの統合方針

### Phase 1: 既存機能の最適化
1. ✅ **MBTilesキャッシュの重複排除**
   - 実装: `qmap_wmts_service.py`
   - 期間: 1-2日

2. ✅ **バッチ書き込み**
   - 実装: タイル書き込みをバッファリング
   - 期間: 1日

### Phase 2: MVT機能追加
3. 🔲 **基本MVT生成**
   - 新規: `qmap_mvt_service.py`
   - 依存: `mapbox-vector-tile` パッケージ
   - 期間: 1週間

4. 🔲 **ジオメトリ簡略化**
   - QGISの `simplify()` API活用
   - ズームレベル別トレランス設定
   - 期間: 2-3日

### Phase 3: 高度な機能 (オプション)
5. 🔲 **PostGIS直接統合**
   - 大規模データセット向け
   - `ST_AsMvt` の活用
   - 期間: 1-2週間

---

## 参考リンク

- [BBOX Server GitHub](https://github.com/bbox-services/bbox)
- [BBOX Documentation](https://www.bbox.earth/)
- [Mapbox Vector Tile Spec](https://github.com/mapbox/vector-tile-spec)
- [PostGIS ST_AsMvt](https://postgis.net/docs/ST_AsMVT.html)

---

## 結論

**BBOXバイナリを統合するのではなく、その優れた設計思想を学んでQMapPermalinkをPythonで拡張することを推奨します。**

これにより:
- ✅ 配布が容易（QGISプラグインのまま）
- ✅ メンテナンス性が高い
- ✅ QGISとの統合が深い
- ✅ ユーザー体験が一貫している
