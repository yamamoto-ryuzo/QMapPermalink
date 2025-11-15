# -*- coding: utf-8 -*-
"""
BBOX Server Manager

高速Rustサーバーの管理（ダウンロード、起動、停止）
"""

import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import tarfile
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from qgis.PyQt.QtCore import QObject, pyqtSignal, QTimer
from qgis.core import QgsMessageLog, Qgis, QgsTask


class BBoxServerManager(QObject):
    """BBOX Rustサーバー管理クラス
    
    Signals:
        server_started: サーバー起動完了
        server_stopped: サーバー停止完了
        download_progress: ダウンロード進捗 (int: 0-100)
        status_changed: ステータス変更 (str)
    """
    
    server_started = pyqtSignal(int)  # port
    server_stopped = pyqtSignal()
    download_progress = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    
    BBOX_VERSION = "0.6.2"
    BBOX_PORT = 8080  # デフォルトポート (OGC API専用、標準サーバーは8089)
    
    def __init__(self, plugin_dir: str):
        super().__init__()
        self.plugin_dir = plugin_dir
        
        # BBoxサーバー専用ディレクトリ（プラグインと同階層）
        # プラグイン更新時に削除されないように独立させる
        plugins_root = os.path.dirname(plugin_dir)  # .../plugins/
        self.bbox_root = os.path.join(plugins_root, 'bbox')
        
        self.bin_dir = os.path.join(self.bbox_root, 'bin')
        self.config_dir = os.path.join(self.bbox_root, 'config')
        self.data_dir = os.path.join(self.bbox_root, 'data')
        
        print(f"BBox root directory: {self.bbox_root}")
        print(f"BBox bin directory: {self.bin_dir}")
        
        # サーバープロセス
        self.process: Optional[subprocess.Popen] = None
        self.current_port: Optional[int] = None
        
        # ヘルスチェック用タイマー
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self._check_health)
        
        # ディレクトリ作成
        for d in [self.bin_dir, self.config_dir, self.data_dir]:
            os.makedirs(d, exist_ok=True)
        for d in [self.bin_dir, self.config_dir, self.data_dir]:
            os.makedirs(d, exist_ok=True)
    
    def get_platform_info(self) -> Tuple[str, str]:
        """プラットフォーム情報を取得
        
        Returns:
            (platform_name, extension): 例: ("x86_64-pc-windows-msvc", "zip")
        """
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == 'windows':
            return ('x86_64-pc-windows-msvc', 'zip')
        elif system == 'linux':
            return ('x86_64-unknown-linux-gnu', 'tar.gz')
        elif system == 'darwin':
            if machine == 'arm64':
                return ('aarch64-apple-darwin', 'tar.gz')
            else:
                return ('x86_64-apple-darwin', 'tar.gz')
        else:
            raise RuntimeError(f"Unsupported platform: {system}")
    
    def get_executable_name(self) -> str:
        """実行ファイル名を取得"""
        if platform.system().lower() == 'windows':
            return 'bbox-server.exe'
        return 'bbox-server'
    
    def get_executable_path(self) -> Optional[str]:
        """BBOX実行ファイルのパスを取得（存在する場合）"""
        exe_name = self.get_executable_name()
        exe_path = os.path.join(self.bin_dir, exe_name)
        
        if os.path.exists(exe_path):
            return exe_path
        return None
    
    def is_available(self) -> bool:
        """BBoxサーバーが利用可能か確認"""
        return self.get_executable_path() is not None
    
    def get_binary_path(self) -> Optional[str]:
        """バイナリパスを取得（get_executable_pathのエイリアス）"""
        return self.get_executable_path()
    
    def is_running(self) -> bool:
        """サーバーが起動中か確認"""
        if self.process is None:
            return False
        
        # プロセスの生存確認
        return self.process.poll() is None
    
    def download_server(self, callback=None) -> bool:
        """サーバーバイナリをダウンロード
        
        Args:
            callback: 進捗コールバック (percent: int)
            
        Returns:
            bool: 成功した場合True
        """
        try:
            print("BBoxServerManager.download_server() started")
            # ディレクトリが存在することを確認
            os.makedirs(self.bin_dir, exist_ok=True)
            os.makedirs(self.config_dir, exist_ok=True)
            os.makedirs(self.data_dir, exist_ok=True)
            print(f"Directories created: bin={self.bin_dir}")
            
            platform_name, ext = self.get_platform_info()
            print(f"Platform: {platform_name}, Extension: {ext}")
            filename = f"bbox-server-{platform_name}.{ext}"
            url = f"https://github.com/bbox-services/bbox/releases/download/v{self.BBOX_VERSION}/{filename}"
            print(f"Download URL: {url}")
            
            self.status_changed.emit(f"Downloading BBOX Server v{self.BBOX_VERSION}...")
            QgsMessageLog.logMessage(f"Downloading from: {url}", 'QMapPermalink', Qgis.Info)
            
            # ダウンロード
            download_path = os.path.join(self.bin_dir, filename)
            print(f"Download path: {download_path}")
            QgsMessageLog.logMessage(f"Download path: {download_path}", 'QMapPermalink', Qgis.Info)
            
            def report_progress(block_num, block_size, total_size):
                if total_size > 0:
                    percent = int((block_num * block_size * 100) / total_size)
                    print(f"Download progress: {percent}%")
                    if callback:
                        callback(min(percent, 100))
                    self.download_progress.emit(min(percent, 100))
            
            print(f"Starting urllib.request.urlretrieve...")
            urllib.request.urlretrieve(url, download_path, report_progress)
            print(f"Download completed, file size: {os.path.getsize(download_path)} bytes")
            
            # 解凍
            self.status_changed.emit("Extracting...")
            print("Extracting archive...")
            QgsMessageLog.logMessage(f"Extracting to: {self.bin_dir}", 'QMapPermalink', Qgis.Info)
            if ext == 'zip':
                print("Extracting ZIP file...")
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    zip_ref.extractall(self.bin_dir)
                print("ZIP extraction completed")
            else:  # tar.gz
                print("Extracting tar.gz file...")
                with tarfile.open(download_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(self.bin_dir)
                print("tar.gz extraction completed")
            
            # ダウンロードファイル削除
            print(f"Removing downloaded archive: {download_path}")
            os.remove(download_path)
            
            # 実行権限付与 (Unix系)
            exe_path = self.get_executable_path()
            print(f"Executable path: {exe_path}")
            if exe_path and platform.system().lower() != 'windows':
                print("Setting executable permissions...")
                os.chmod(exe_path, 0o755)
            
            self.status_changed.emit("Download completed!")
            print("BBoxServerManager.download_server() completed successfully")
            QgsMessageLog.logMessage("BBOX Server downloaded successfully", 'QMapPermalink', Qgis.Success)
            return True
            
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            print(f"BBoxServerManager.download_server() error: {error_msg}")
            import traceback
            traceback.print_exc()
            self.status_changed.emit(error_msg)
            QgsMessageLog.logMessage(error_msg, 'QMapPermalink', Qgis.Critical)
            return False
    
    def create_config(self, port: int = None, project=None) -> str:
        """設定ファイルを生成
        
        Args:
            port: ポート番号（Noneの場合はデフォルト）
            project: QGISプロジェクト（レイヤー情報取得用）
            
        Returns:
            str: 設定ファイルパス
        """
        if port is None:
            port = self.BBOX_PORT
        
        config_path = os.path.join(self.config_dir, 'bbox.toml')
        
        # 基本設定を生成
        config_lines = [
            "# BBOX Server Configuration",
            "# Generated by QMapPermalink",
            "",
            "[webserver]",
            f'server_addr = "127.0.0.1:{port}"',
            "worker_threads = 4",
            "",
            "# Static file serving",
            "[[assets.static]]",
            f'dir = "{self.data_dir.replace(os.sep, "/")}"',
            'path = "/assets"',
            ""
        ]
        
        # QGISプロジェクトからレイヤー情報を取得
        if project:
            from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer, QgsWkbTypes
            
            # プロジェクトインスタンスの取得
            if isinstance(project, QgsProject):
                qgs_project = project
            else:
                qgs_project = QgsProject.instance()
            
            # GeoPackageファイルをデータソースとして追加
            gpkg_files = set()
            for layer in qgs_project.mapLayers().values():
                if isinstance(layer, QgsVectorLayer) and layer.isValid():
                    source = layer.source()
                    # GeoPackageファイルのパスを抽出
                    if '.gpkg' in source.lower():
                        gpkg_path = source.split('|')[0]  # "|layername=..." を除去
                        if os.path.exists(gpkg_path):
                            gpkg_files.add(gpkg_path)
            
            # GeoPackageデータソースを追加
            for idx, gpkg_path in enumerate(sorted(gpkg_files)):
                # パスをスラッシュに統一
                gpkg_path_normalized = gpkg_path.replace('\\', '/')
                
                config_lines.extend([
                    f"[[datasource]]",
                    f'name = "gpkg_{idx}"',
                    f'[datasource.gpkg]',
                    f'path = "{gpkg_path_normalized}"',
                    ""
                ])
            
            QgsMessageLog.logMessage(
                f"BBOX config generated with {len(gpkg_files)} GeoPackage datasources",
                'QMapPermalink', Qgis.Info
            )
        
        config_content = "\n".join(config_lines)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"BBOX config saved: {config_path}")
        print("=== BBOX Config Content ===")
        print(config_content)
        print("=== End of Config ===")
        
        QgsMessageLog.logMessage(
            f"BBOX config saved: {config_path}",
            'QMapPermalink', Qgis.Info
        )
        
        return config_path
    
    def start_server(self, port: int = None, project=None) -> bool:
        """サーバーを起動
        
        Args:
            port: ポート番号（Noneの場合はデフォルト）
            project: QGISプロジェクト（レイヤー情報取得用）
            
        Returns:
            bool: 起動成功した場合True
        """
        if self.is_running():
            QgsMessageLog.logMessage("BBOX Server is already running", 'QMapPermalink', Qgis.Warning)
            return False
        
        exe_path = self.get_executable_path()
        if not exe_path:
            QgsMessageLog.logMessage("BBOX Server not found. Please download first.", 'QMapPermalink', Qgis.Critical)
            return False
        
        try:
            if port is None:
                port = self.BBOX_PORT
            
            # 設定ファイル生成（QGISプロジェクト情報を含む）
            config_path = self.create_config(port, project)
            
            # サーバー起動
            self.status_changed.emit(f"Starting BBOX Server on port {port}...")
            
            if platform.system().lower() == 'windows':
                # Windows: ウィンドウを表示しない
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                self.process = subprocess.Popen(
                    [exe_path, '--config', config_path, 'serve'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo,
                    cwd=self.plugin_dir
                )
            else:
                # Unix系
                self.process = subprocess.Popen(
                    [exe_path, '--config', config_path, 'serve'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.plugin_dir
                )
            
            self.current_port = port
            
            # プロセス起動直後の出力を確認（デバッグ用）
            import time
            time.sleep(0.5)  # 短時間待機
            
            if self.process.poll() is not None:
                # プロセスが既に終了している
                stdout, stderr = self.process.communicate()
                error_msg = f"BBOX Server failed to start. Exit code: {self.process.returncode}"
                if stderr:
                    error_msg += f"\nStderr: {stderr.decode('utf-8', errors='ignore')}"
                if stdout:
                    error_msg += f"\nStdout: {stdout.decode('utf-8', errors='ignore')}"
                print(error_msg)
                QgsMessageLog.logMessage(error_msg, 'QMapPermalink', Qgis.Critical)
                self.process = None
                return False
            
            # 起動ログを出力
            print(f"BBOX Server process started with PID: {self.process.pid}")
            print(f"Command: {exe_path} --config {config_path} serve")
            QgsMessageLog.logMessage(f"BBOX Server process started with PID: {self.process.pid}", 'QMapPermalink', Qgis.Info)
            
            # ヘルスチェック開始
            self.health_timer.start(5000)  # 5秒ごと
            
            self.status_changed.emit(f"BBOX Server started on port {port}")
            self.server_started.emit(port)
            QgsMessageLog.logMessage(f"BBOX Server started on port {port}", 'QMapPermalink', Qgis.Success)
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to start BBOX Server: {str(e)}"
            self.status_changed.emit(error_msg)
            QgsMessageLog.logMessage(error_msg, 'QMapPermalink', Qgis.Critical)
            return False
    
    def stop_server(self) -> bool:
        """サーバーを停止
        
        Returns:
            bool: 停止成功した場合True
        """
        if not self.is_running():
            return True
        
        try:
            self.status_changed.emit("Stopping BBOX Server...")
            
            # ヘルスチェック停止
            self.health_timer.stop()
            
            # プロセス終了
            self.process.terminate()
            
            # 最大5秒待機
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 強制終了
                self.process.kill()
                self.process.wait()
            
            self.process = None
            self.current_port = None
            
            self.status_changed.emit("BBOX Server stopped")
            self.server_stopped.emit()
            QgsMessageLog.logMessage("BBOX Server stopped", 'QMapPermalink', Qgis.Info)
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to stop BBOX Server: {str(e)}"
            self.status_changed.emit(error_msg)
            QgsMessageLog.logMessage(error_msg, 'QMapPermalink', Qgis.Critical)
            return False
    
    def _check_health(self):
        """サーバーのヘルスチェック"""
        if not self.is_running():
            self.health_timer.stop()
            self.status_changed.emit("BBOX Server stopped")
            return
        
        # HTTP経由でヘルスチェック
        if self.current_port:
            try:
                import urllib.request
                health_url = f"http://localhost:{self.current_port}/"
                response = urllib.request.urlopen(health_url, timeout=2)
                if response.status == 200:
                    QgsMessageLog.logMessage(
                        f"BBOX Server health check OK (port {self.current_port})",
                        'QMapPermalink', Qgis.Info
                    )
            except Exception as e:
                QgsMessageLog.logMessage(
                    f"BBOX Server health check failed: {e}",
                    'QMapPermalink', Qgis.Warning
                )
    
    def test_connection(self) -> bool:
        """サーバー接続テスト
        
        Returns:
            bool: 接続成功時True
        """
        if not self.current_port:
            return False
        
        try:
            import urllib.request
            test_url = f"http://localhost:{self.current_port}/"
            print(f"Testing BBox server connection: {test_url}")
            
            response = urllib.request.urlopen(test_url, timeout=5)
            content = response.read().decode('utf-8')
            
            print(f"BBox server response status: {response.status}")
            print(f"BBox server response (first 200 chars): {content[:200]}")
            
            QgsMessageLog.logMessage(
                f"✅ BBOX Server connection test successful (port {self.current_port})",
                'QMapPermalink', Qgis.Success
            )
            return True
            
        except Exception as e:
            error_msg = f"❌ BBOX Server connection test failed: {e}"
            print(error_msg)
            QgsMessageLog.logMessage(error_msg, 'QMapPermalink', Qgis.Critical)
            return False
            self.server_stopped.emit()
            return
        
        # 簡易ヘルスチェック（HTTPリクエストは省略）
        try:
            import urllib.request
            url = f"http://127.0.0.1:{self.current_port}/health"
            req = urllib.request.Request(url, method='GET')
            urllib.request.urlopen(req, timeout=2)
        except:
            # ヘルスチェック失敗は警告のみ
            pass
    
    def get_server_url(self) -> Optional[str]:
        """サーバーURLを取得
        
        Returns:
            str: サーバーURL、停止中の場合None
        """
        if self.is_running() and self.current_port:
            return f"http://127.0.0.1:{self.current_port}"
        return None
    
    def cleanup(self):
        """クリーンアップ"""
        self.stop_server()
        self.health_timer.stop()
