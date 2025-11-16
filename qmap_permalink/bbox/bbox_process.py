"""
BBOX Serverプロセス管理モジュール

BBOX Serverバイナリの起動・停止・監視を担当
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Optional, Dict, Any
from qgis.core import QgsMessageLog, Qgis


class BBoxProcessManager:
    """BBOX Serverプロセス管理クラス"""
    
    def __init__(self):
        """プロセスマネージャーを初期化"""
        self.process: Optional[subprocess.Popen] = None
        self.bbox_binary: Optional[Path] = None
        # Determine plugin root and bbox root so we can set cwd when starting
        plugin_dir = Path(__file__).parent.parent
        try:
            plugins_root = plugin_dir.parent
            self.bbox_root = plugins_root / 'bbox'
        except Exception:
            self.bbox_root = plugin_dir / 'bbox'

        self._find_bbox_binary()
        
    def _find_bbox_binary(self) -> Optional[Path]:
        """BBOX Serverバイナリを検索
        
        検索順序:
        1. qmap_permalink/bbox/bin/
        2. 環境変数 PATH
        3. システム標準パス
        """
        # プラグインディレクトリ
        plugin_dir = Path(__file__).parent.parent
        
        # プラットフォーム別のバイナリ名
        if platform.system() == "Windows":
            binary_name = "bbox-server.exe"
        else:
            binary_name = "bbox-server"
        
        # 1. プラグイン内のbin/を確認
        local_binary = plugin_dir / "bbox" / "bin" / binary_name
        if local_binary.exists():
            self.bbox_binary = local_binary
            QgsMessageLog.logMessage(
                f"✅ BBOX Server found: {local_binary}",
                "QMapPermalink", Qgis.Info
            )
            return local_binary

        # 1b. プラグインの親ディレクトリ（plugins/）にある別プラグイン 'bbox' の bin/ を確認
        try:
            plugins_root = plugin_dir.parent
            alt_binary = plugins_root / 'bbox' / 'bin' / binary_name
            if alt_binary.exists():
                self.bbox_binary = alt_binary
                QgsMessageLog.logMessage(
                    f"✅ BBOX Server found in sibling plugin: {alt_binary}",
                    "QMapPermalink", Qgis.Info
                )
                return alt_binary
        except Exception:
            # issue in path resolution - ignore and continue search
            pass
        
        # 2. PATH環境変数を確認
        import shutil
        path_binary = shutil.which(binary_name)
        if path_binary:
            self.bbox_binary = Path(path_binary)
            QgsMessageLog.logMessage(
                f"✅ BBOX Server found in PATH: {path_binary}",
                "QMapPermalink", Qgis.Info
            )
            return self.bbox_binary
        
        # 3. 見つからない
        QgsMessageLog.logMessage(
            "⚠️ BBOX Server binary not found. Please run download script.",
            "QMapPermalink", Qgis.Warning
        )
        return None
    
    def is_available(self) -> bool:
        """BBOX Serverが利用可能かチェック"""
        return self.bbox_binary is not None and self.bbox_binary.exists()
    
    def is_running(self) -> bool:
        """BBOX Serverが実行中かチェック"""
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def start(self, config_file: Optional[Path] = None, port: int = 8080, cwd: Optional[Path] = None) -> bool:
        """BBOX Serverを起動
        
        Args:
            config_file: 設定ファイルパス（オプション）
            port: ポート番号
            
        Returns:
            bool: 起動成功時True
        """
        if not self.is_available():
            QgsMessageLog.logMessage(
                "❌ Cannot start: BBOX Server binary not found",
                "QMapPermalink", Qgis.Critical
            )
            return False
        
        if self.is_running():
            QgsMessageLog.logMessage(
                "⚠️ BBOX Server is already running",
                "QMapPermalink", Qgis.Warning
            )
            return False
        
        try:
            # 起動コマンドを構築
            cmd = [str(self.bbox_binary)]
            
            if config_file and config_file.exists():
                cmd.extend(["-c", str(config_file)])
            
            cmd.append("serve")
            
            # 環境変数でポート設定
            env = os.environ.copy()
            env["BBOX_WEBSERVER_PORT"] = str(port)
            
            QgsMessageLog.logMessage(
                f"🚀 Starting BBOX Server: {' '.join(cmd)}",
                "QMapPermalink", Qgis.Info
            )
            
            # プロセス起動
            proc_cwd = None
            try:
                # If caller provided a cwd (e.g. project_basedir), prefer it.
                if cwd is not None:
                    proc_cwd = str(cwd)
                else:
                    # Fallback: Prefer starting the server from the sibling 'bbox' plugin root so
                    # relative paths in the config (e.g. 'data/...') resolve correctly.
                    if hasattr(self, 'bbox_root') and self.bbox_root and self.bbox_root.exists():
                        proc_cwd = str(self.bbox_root)
            except Exception:
                proc_cwd = None

            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                cwd=proc_cwd,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            QgsMessageLog.logMessage(
                f"✅ BBOX Server started (PID: {self.process.pid}, Port: {port})",
                "QMapPermalink", Qgis.Info
            )
            
            return True
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"❌ Failed to start BBOX Server: {e}",
                "QMapPermalink", Qgis.Critical
            )
            return False
    
    def stop(self) -> bool:
        """BBOX Serverを停止
        
        Returns:
            bool: 停止成功時True
        """
        if not self.is_running():
            QgsMessageLog.logMessage(
                "⚠️ BBOX Server is not running",
                "QMapPermalink", Qgis.Warning
            )
            return False
        
        try:
            QgsMessageLog.logMessage(
                f"🛑 Stopping BBOX Server (PID: {self.process.pid})",
                "QMapPermalink", Qgis.Info
            )
            
            self.process.terminate()
            
            # 最大5秒待機
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 強制終了
                self.process.kill()
                self.process.wait()
            
            self.process = None
            
            QgsMessageLog.logMessage(
                "✅ BBOX Server stopped",
                "QMapPermalink", Qgis.Info
            )
            
            return True
            
        except Exception as e:
            QgsMessageLog.logMessage(
                f"❌ Failed to stop BBOX Server: {e}",
                "QMapPermalink", Qgis.Critical
            )
            return False
    
    def get_version(self) -> Optional[str]:
        """BBOX Serverのバージョンを取得"""
        if not self.is_available():
            return None
        
        try:
            result = subprocess.run(
                [str(self.bbox_binary), "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception as e:
            QgsMessageLog.logMessage(
                f"⚠️ Failed to get version: {e}",
                "QMapPermalink", Qgis.Warning
            )
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """BBOX Serverの状態を取得
        
        Returns:
            dict: 状態情報
        """
        return {
            "available": self.is_available(),
            "running": self.is_running(),
            "binary_path": str(self.bbox_binary) if self.bbox_binary else None,
            "version": self.get_version(),
            "pid": self.process.pid if self.is_running() else None
        }
