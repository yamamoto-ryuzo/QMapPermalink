"""
QGISからBBOX Server用へのデータエクスポートモジュール

QGISプロジェクトのレイヤーをBBOX Server互換形式でエクスポート
"""

from pathlib import Path
from typing import List, Optional, Dict
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRasterLayer,
    QgsVectorFileWriter, QgsCoordinateReferenceSystem,
    QgsMessageLog, Qgis
)


class BBoxExporter:
    """BBOX Server用エクスポーター"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """エクスポーターを初期化
        
        Args:
            output_dir: 出力先ディレクトリ（Noneの場合は自動設定）
        """
        if output_dir is None:
            try:
                # Prefer installed plugin location so sibling plugins/bbox is used
                import qmap_permalink as _pkg
                plugin_dir = Path(_pkg.__file__).resolve().parent
                plugins_root = plugin_dir.parent
                bbox_root = plugins_root / 'bbox'
                self.output_dir = bbox_root / 'data'
            except Exception:
                plugin_dir = Path(__file__).parent.parent
                self.output_dir = plugin_dir / "bbox" / "data"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        QgsMessageLog.logMessage(
            f"📁 Export directory: {self.output_dir}",
            "QMapPermalink", Qgis.Info
        )
    
    def export_vector_layers(self, 
                            format: str = "GeoJSON",
                            layer_filter: Optional[List[str]] = None) -> List[Path]:
        """ベクターレイヤーをエクスポート
        
        Args:
            format: 出力フォーマット（GeoJSON, GPKG）
            layer_filter: エクスポートするレイヤー名のリスト（Noneで全て）
            
        Returns:
            List[Path]: エクスポートされたファイルパスのリスト
        """
        exported = []
        project = QgsProject.instance()
        
        QgsMessageLog.logMessage(
            f"🚀 Exporting vector layers (format: {format})",
            "QMapPermalink", Qgis.Info
        )
        
        for layer in project.mapLayers().values():
            if not isinstance(layer, QgsVectorLayer):
                continue
            
            # フィルタチェック
            if layer_filter and layer.name() not in layer_filter:
                continue
            
            # レイヤー名をサニタイズ
            layer_name = self._sanitize_filename(layer.name())
            
            # フォーマット別の設定
            if format.upper() == "GEOJSON":
                output_file = self.output_dir / f"{layer_name}.geojson"
                driver_name = "GeoJSON"
            elif format.upper() in ("GPKG", "GEOPACKAGE"):
                output_file = self.output_dir / f"{layer_name}.gpkg"
                driver_name = "GPKG"
            else:
                QgsMessageLog.logMessage(
                    f"⚠️ Unsupported format: {format}",
                    "QMapPermalink", Qgis.Warning
                )
                continue
            
            # エクスポート実行
            try:
                options = QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = driver_name
                options.fileEncoding = "UTF-8"
                
                error = QgsVectorFileWriter.writeAsVectorFormatV3(
                    layer,
                    str(output_file),
                    QgsProject.instance().transformContext(),
                    options
                )
                
                if error[0] == QgsVectorFileWriter.NoError:
                    exported.append(output_file)
                    QgsMessageLog.logMessage(
                        f"✅ Exported: {layer.name()} -> {output_file.name}",
                        "QMapPermalink", Qgis.Info
                    )
                else:
                    QgsMessageLog.logMessage(
                        f"❌ Export failed: {layer.name()} - {error[1]}",
                        "QMapPermalink", Qgis.Critical
                    )
                    
            except Exception as e:
                QgsMessageLog.logMessage(
                    f"❌ Export error: {layer.name()} - {e}",
                    "QMapPermalink", Qgis.Critical
                )
        
        QgsMessageLog.logMessage(
            f"✅ Export completed: {len(exported)} files",
            "QMapPermalink", Qgis.Info
        )
        
        return exported
    
    def export_wmts_cache_to_mbtiles(self, 
                                     cache_dir: Path,
                                     output_name: str = "qmap_tiles") -> Optional[Path]:
        """WMTSキャッシュをMBTiles形式に変換
        
        Args:
            cache_dir: WMTSキャッシュディレクトリ
            output_name: 出力ファイル名（拡張子なし）
            
        Returns:
            Optional[Path]: 生成されたMBTilesファイルパス
        """
        output_file = self.output_dir / f"{output_name}.mbtiles"
        
        # TODO: 実装
        # WMTSキャッシュ（PNG/JPEGタイル）をMBTiles形式に変換
        # mbutil や専用ライブラリを使用
        
        QgsMessageLog.logMessage(
            f"⚠️ WMTS to MBTiles conversion not yet implemented",
            "QMapPermalink", Qgis.Warning
        )
        
        return None
    
    def _sanitize_filename(self, name: str) -> str:
        """ファイル名に使用できない文字をサニタイズ
        
        Args:
            name: 元のレイヤー名
            
        Returns:
            str: サニタイズされた名前
        """
        import re
        # 安全な文字のみ残す
        safe_name = re.sub(r'[^\w\-_]', '_', name)
        # 連続するアンダースコアを1つに
        safe_name = re.sub(r'_+', '_', safe_name)
        # 先頭・末尾のアンダースコアを削除
        safe_name = safe_name.strip('_')
        
        return safe_name or "layer"
    
    def get_export_summary(self) -> Dict[str, any]:
        """エクスポート可能なレイヤーのサマリーを取得
        
        Returns:
            dict: サマリー情報
        """
        project = QgsProject.instance()
        
        vector_layers = []
        raster_layers = []
        
        for layer in project.mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                vector_layers.append({
                    "name": layer.name(),
                    "type": layer.geometryType().name,
                    "feature_count": layer.featureCount(),
                    "crs": layer.crs().authid()
                })
            elif isinstance(layer, QgsRasterLayer):
                raster_layers.append({
                    "name": layer.name(),
                    "width": layer.width(),
                    "height": layer.height(),
                    "crs": layer.crs().authid()
                })
        
        return {
            "vector_layers": vector_layers,
            "raster_layers": raster_layers,
            "total_vector": len(vector_layers),
            "total_raster": len(raster_layers)
        }
