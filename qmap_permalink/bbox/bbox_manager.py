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
from .bbox_exporter import BBoxExporter


class BBoxManager:
    """BBOX Server統合マネージャー"""
    
    def __init__(self):
        """マネージャーを初期化"""
        self.process_manager = BBoxProcessManager()
        self.config_manager = BBoxConfig()
        self.exporter = BBoxExporter()
        
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
        status["export_dir"] = str(self.exporter.output_dir)
        return status
    
    def start_bbox_server(self, port: int = 8080, 
                         auto_export: bool = True) -> bool:
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
        
        # 自動エクスポート
        if auto_export:
            QgsMessageLog.logMessage(
                "📤 Auto-exporting data...",
                "QMapPermalink", Qgis.Info
            )
            self.export_and_configure()
        
        # 起動
        return self.process_manager.start(
            config_file=self.config_manager.config_path,
            port=port
        )
    
    def stop_bbox_server(self) -> bool:
        """BBOX Serverを停止"""
        return self.process_manager.stop()
    
    def export_and_configure(self, format: str = "GeoJSON") -> bool:
        """データをエクスポートして設定ファイルを生成
        
        Args:
            format: エクスポートフォーマット
            
        Returns:
            bool: 成功時True
        """
        try:
            # ベクターレイヤーをエクスポート
            exported_files = self.exporter.export_vector_layers(format=format)

            # 可能であれば、プロジェクト直下にコピーして
            # 設定ファイルにはプロジェクト基準の相対パスを書き込む
            try:
                from qgis.core import QgsProject
                proj_file = QgsProject.instance().fileName()
            except Exception:
                proj_file = None

            # Prefer using exporter output directory (usually plugins/bbox/data).
            # Historically we copied exports into the project directory and
            # wrote collection sources relative to the project. That caused
            # the BBOX server to be unable to resolve paths when the
            # server's config did not include the project_basedir. To avoid
            # that, do not copy files into the project by default — use the
            # exporter output location which is the canonical bbox/data.
            copied_files = exported_files
            
            if not exported_files:
                QgsMessageLog.logMessage(
                    "⚠️ No layers to export",
                    "QMapPermalink", Qgis.Warning
                )
                return False
            
            # 設定ファイル生成
            self.config_manager.config["collections"].clear()
            
            # 設定には、プロジェクト基準で相対化されるように
            # コピー済みファイル（あれば）を優先して渡す
            for file_path in (copied_files or exported_files):
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
        return self.exporter.get_export_summary()
    
    def cleanup(self):
        """クリーンアップ（プラグイン終了時）"""
        if self.process_manager.is_running():
            QgsMessageLog.logMessage(
                "🧹 Cleaning up: Stopping BBOX Server",
                "QMapPermalink", Qgis.Info
            )
            self.stop_bbox_server()
