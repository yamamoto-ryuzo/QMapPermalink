"""
BBOX Server ダウンロードヘルパースクリプト（プラグイン内蔵版）

QGISプラグインからBBOX Serverバイナリをダウンロード
"""

import os
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen
from qgis.core import QgsMessageLog, Qgis, QgsTask
from qgis.PyQt.QtCore import pyqtSignal


class BBoxDownloadTask(QgsTask):
    """BBOX Serverダウンロードタスク"""
    
    finished = pyqtSignal(bool, str)
    
    def __init__(self, version: str = "v0.6.2"):
        super().__init__("Download BBOX Server", QgsTask.CanCancel)
        self.version = version
        self.error_message = ""
        
    def run(self) -> bool:
        """ダウンロード実行"""
        try:
            # プラットフォーム判定
            import platform
            system = platform.system()
            
            if system == "Windows":
                platform_name = "x86_64-pc-windows-msvc"
                file_name = f"bbox-server-{platform_name}.zip"
            elif system == "Linux":
                platform_name = "x86_64-unknown-linux-gnu"
                file_name = f"bbox-server-{platform_name}.tar.gz"
            elif system == "Darwin":  # macOS
                if platform.machine() == "arm64":
                    platform_name = "aarch64-apple-darwin"
                else:
                    platform_name = "x86_64-apple-darwin"
                file_name = f"bbox-server-{platform_name}.tar.gz"
            else:
                self.error_message = f"Unsupported platform: {system}"
                return False
            
            # ダウンロードURL
            url = f"https://github.com/bbox-services/bbox/releases/download/{self.version}/{file_name}"
            
            QgsMessageLog.logMessage(
                f"📥 Downloading: {url}",
                "QMapPermalink", Qgis.Info
            )
            
            # ダウンロード先
            plugin_dir = Path(__file__).parent
            bin_dir = plugin_dir / "bbox" / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            
            # 一時ファイルにダウンロード
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file_name).suffix) as tmp_file:
                tmp_path = tmp_file.name
                
                with urlopen(url) as response:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    chunk_size = 8192
                    
                    while True:
                        if self.isCanceled():
                            return False
                        
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        
                        tmp_file.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.setProgress(progress)
            
            # 解凍
            QgsMessageLog.logMessage(
                "📦 Extracting...",
                "QMapPermalink", Qgis.Info
            )
            
            if file_name.endswith('.zip'):
                # Windows: ZIP
                with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                    zip_ref.extractall(bin_dir)
            else:
                # Linux/macOS: tar.gz
                import tarfile
                with tarfile.open(tmp_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(bin_dir)
            
            # 一時ファイル削除
            os.remove(tmp_path)
            
            QgsMessageLog.logMessage(
                f"✅ BBOX Server downloaded to: {bin_dir}",
                "QMapPermalink", Qgis.Info
            )
            
            return True
            
        except Exception as e:
            self.error_message = str(e)
            QgsMessageLog.logMessage(
                f"❌ Download failed: {e}",
                "QMapPermalink", Qgis.Critical
            )
            return False
    
    def finished(self, result: bool):
        """完了時のコールバック"""
        if result:
            QgsMessageLog.logMessage(
                "🎉 Download completed successfully",
                "QMapPermalink", Qgis.Info
            )
        else:
            QgsMessageLog.logMessage(
                f"❌ Download failed: {self.error_message}",
                "QMapPermalink", Qgis.Critical
            )


def download_bbox_server(version: str = "v0.6.2") -> BBoxDownloadTask:
    """BBOX Serverをダウンロード
    
    Args:
        version: ダウンロードするバージョン
        
    Returns:
        BBoxDownloadTask: ダウンロードタスク
    """
    from qgis.core import QgsApplication
    
    task = BBoxDownloadTask(version)
    QgsApplication.taskManager().addTask(task)
    
    return task
