"""
BBOX Server統合マネージャー

QMapPermalinkとBBOX Serverの統合を管理する中心クラス
プロセス管理、設定生成、データエクスポートを統括
"""

from pathlib import Path
from typing import Optional, Dict, Any
from qgis.core import QgsMessageLog, Qgis

from .bbox_process import BBoxProcessManager
from .bbox_config import BBoxConfig
# Note: BBoxExporter removed. Plugin no longer performs automatic export.


class BBoxManager:
    """BBOX Server統合マネージャー"""
    
    def __init__(self):
        """マネージャーを初期化"""
        self.process_manager = BBoxProcessManager()
        self.config_manager = BBoxConfig()
        # Exporter removed per project policy; exporter functionality
        # disabled to avoid automatic copying/format conversion.
        
        QgsMessageLog.logMessage(
            "🎯 BBOX Manager initialized",
            "QMapPermalink", Qgis.Info
        )
    
    def is_bbox_available(self) -> bool:
        """BBOX Serverが利用可能かチェック"""
        return self.process_manager.is_available()
    
    def get_status(self) -> Dict[str, Any]:
        """全体のステータスを取得"""
        status = self.process_manager.get_status()
        status["config_path"] = str(self.config_manager.config_path)
        status["export_dir"] = None
        return status
    
    def start_bbox_server(self, port: int = 8080,
                         auto_export: bool = False) -> bool:
        """BBOX Serverを起動
        
        Args:
            port: ポート番号
            auto_export: 起動前に自動エクスポートするか
            
        Returns:
            bool: 起動成功時True
        """
        if not self.is_bbox_available():
            QgsMessageLog.logMessage(
                "❌ BBOX Server not available. Please download it first.",
                "QMapPermalink", Qgis.Critical
            )
            return False
        
        # 自動エクスポートはデフォルトで無効（データの複製を避けるため）。
        # エクスポートが必要な場合は明示的に auto_export=True を渡すか、
        # `export_and_configure(force_export=True)` を呼んでください。
        if auto_export:
            QgsMessageLog.logMessage(
                "📤 Auto-exporting data...",
                "QMapPermalink", Qgis.Info
            )
            self.export_and_configure(force_export=True)
        
        # 起動: プロジェクト基準ディレクトリがある場合はそれを作業ディレクトリとして渡す
        proj_cwd = None
        try:
            proj_cwd = self.config_manager.project_basedir
        except Exception:
            proj_cwd = None

        return self.process_manager.start(
            config_file=self.config_manager.config_path,
            port=port,
            cwd=proj_cwd
        )
    
    def stop_bbox_server(self) -> bool:
        """BBOX Serverを停止"""
        return self.process_manager.stop()
    
    def export_and_configure(self, format: str = "GeoJSON", force_export: bool = False) -> bool:
        """データをエクスポートして設定ファイルを生成
        
        Args:
            format: エクスポートフォーマット
            force_export: True の場合は必ずエクスポートを行う。False の場合は
                          既存の出力ファイルを利用して設定を生成する（コピーは行わない）。
        Returns:
            bool: 成功時True
        """
        try:
            # エクスポート方針:
            # - デフォルトでは自動コピー/自動エクスポートを行わない（データ肥大・サイロ化を防ぐ）。
            # - 既に `self.exporter.output_dir` にあるファイル（*.geojson, *.gpkg）を利用して
            #   設定ファイルを生成する。
            # - 明示的にファイルを生成したい場合は `force_export=True` を指定する。
            if force_export:
                # Exporter functionality has been removed. Explicit export
                # is no longer supported by the plugin to avoid automatic
                # copying and format conversion. Developers must prepare
                # project files (GeoJSON/GPKG/MBTiles) manually.
                QgsMessageLog.logMessage(
                    "⚠️ Automatic export is disabled. Prepare files manually or reintroduce exporter.",
                    "QMapPermalink", Qgis.Warning
                )
                return False
            else:
                # 既存の出力ファイルを収集（コピーは行わない）
                from pathlib import Path
                exported_files = []

                # 1) プロジェクトルートに配置されたファイルを優先して探す
                proj_dir = None
                try:
                    from qgis.core import QgsProject
                    proj_file = QgsProject.instance().fileName()
                    if proj_file:
                        proj_dir = Path(proj_file).resolve().parent
                except Exception:
                    proj_dir = None

                if proj_dir is not None:
                    # Search recursively under the project directory so files
                    # placed in subfolders (e.g. project_root/data/) are found.
                    for ext in ('.geojson', '.gpkg', '.mbtiles'):
                        exported_files.extend(list(proj_dir.rglob(f'*{ext}')))

                # 2) プラグインの（従来の）デフォルト出力先も念のため確認
                #    (BBoxExporter removed; replicate its default location)
                plugin_dir = Path(__file__).parent.parent
                outdir = plugin_dir / 'bbox' / 'data'
                if outdir.exists():
                    for ext in ('.geojson', '.gpkg', '.mbtiles'):
                        exported_files.extend(list(outdir.glob(f'*{ext}')))

                # 重複除去、Path オブジェクトのリスト化
                exported_files = list(dict.fromkeys(exported_files))

                if not exported_files:
                    QgsMessageLog.logMessage(
                        "⚠️ No exported files found in project root or bbox data directory.\n" \
                        "    To generate files automatically, call export_and_configure(force_export=True),\n" \
                        "    or place GeoJSON/GPKG/MBTiles files under your project root and retry.",
                        "QMapPermalink", Qgis.Warning
                    )
                    return False
            
            # 設定ファイル生成
            self.config_manager.config["collections"].clear()

            # If possible, prefer project-local files: set project_basedir so
            # generated TOML references project-root-relative paths when
            # appropriate. This lets users organize their data under the
            # project directory freely.
            try:
                from qgis.core import QgsProject
                proj_file = QgsProject.instance().fileName()
                if proj_file:
                    proj_dir = Path(proj_file).resolve().parent
                    self.config_manager.project_basedir = proj_dir
            except Exception:
                # No project info available; leave project_basedir unset
                pass

            # 生成する設定には出力ディレクトリ内のファイルをそのまま参照する（コピーしない）
            for file_path in exported_files:
                layer_name = Path(file_path).stem
                self.config_manager.add_collection(
                    name=layer_name,
                    source=Path(file_path),
                    srs="EPSG:4326"
                )
            
            # 保存
            config_path = self.config_manager.save()
            
            QgsMessageLog.logMessage(
                f"✅ Export and configuration completed\n"
                f"   Files: {len(exported_files)}\n"
                f"   Config: {config_path}",
                "QMapPermalink", Qgis.Info
            )
            
            return True
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"❌ Export and configure failed: {e}",
                "QMapPermalink", Qgis.Critical
            )
            return False
    
    def sync_to_bbox(self) -> bool:
        """QGISプロジェクトの変更をBBOX Serverに同期
        
        Returns:
            bool: 同期成功時True
        """
        was_running = self.process_manager.is_running()
        
        # 実行中なら一時停止
        if was_running:
            QgsMessageLog.logMessage(
                "⏸️ Stopping BBOX Server for sync...",
                "QMapPermalink", Qgis.Info
            )
            self.stop_bbox_server()
        
        # エクスポート＆設定更新
        success = self.export_and_configure()
        
        # 再起動
        if was_running and success:
            QgsMessageLog.logMessage(
                "▶️ Restarting BBOX Server...",
                "QMapPermalink", Qgis.Info
            )
            self.start_bbox_server(auto_export=False)
        
        return success
    
    def get_export_summary(self) -> Dict[str, Any]:
        """エクスポート可能なデータのサマリーを取得"""
        # Since the in-plugin exporter was removed, provide a summary of
        # candidate files that can be used as collections. This inspects
        # the QGIS project directory (recursively) and the legacy plugin
        # data directory and returns found files.
        from pathlib import Path

        summary = {"candidate_files": [], "count": 0}
        try:
            proj_dir = None
            try:
                from qgis.core import QgsProject
                proj_file = QgsProject.instance().fileName()
                if proj_file:
                    proj_dir = Path(proj_file).resolve().parent
            except Exception:
                proj_dir = None

            candidates = []
            if proj_dir is not None:
                for ext in ('.geojson', '.gpkg', '.mbtiles'):
                    candidates.extend(list(proj_dir.rglob(f'*{ext}')))

            # Also check the plugin's bbox/data directory as a fallback
            plugin_dir = Path(__file__).parent.parent
            outdir = plugin_dir / 'bbox' / 'data'
            if outdir.exists():
                for ext in ('.geojson', '.gpkg', '.mbtiles'):
                    candidates.extend(list(outdir.glob(f'*{ext}')))

            # Deduplicate while preserving order
            candidates = list(dict.fromkeys(candidates))
            summary["candidate_files"] = [str(p) for p in candidates]
            summary["count"] = len(candidates)
            return summary
        except Exception as e:
            QgsMessageLog.logMessage(
                f"⚠️ Failed to collect export summary: {e}",
                "QMapPermalink", Qgis.Warning
            )
            return summary
    
    def cleanup(self):
        """クリーンアップ（プラグイン終了時）"""
        if self.process_manager.is_running():
            QgsMessageLog.logMessage(
                "🧹 Cleaning up: Stopping BBOX Server",
                "QMapPermalink", Qgis.Info
            )
            self.stop_bbox_server()
