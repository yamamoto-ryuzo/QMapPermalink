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
from qgis.PyQt.QtCore import QObject, pyqtSignal
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
    QGIS_SERVER_VERSION = "3.34.11"  # QGIS LTR version
    
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
        self.qgis_server_dir = os.path.join(self.bbox_root, 'qgis-server')
        
        print(f"BBox root directory: {self.bbox_root}")
        print(f"BBox bin directory: {self.bin_dir}")
        print(f"QGIS Server directory: {self.qgis_server_dir}")
        
        # サーバープロセス
        self.process: Optional[subprocess.Popen] = None
        self.current_port: Optional[int] = None
        
        # ディレクトリ作成
        for d in [self.bin_dir, self.config_dir, self.data_dir, self.qgis_server_dir]:
            os.makedirs(d, exist_ok=True)

        # プロジェクト読み込み後に設定を更新するためのフック
        try:
            from qgis.core import QgsProject
            self._qgs = QgsProject.instance()

            # Try to connect to several possible project-related signals.
            # QGIS API names vary; attempt multiple common signals and ignore
            # failures. Also provide a polling fallback if no signal is available.
            try:
                # emitted when a project is loaded from disk
                self._qgs.projectLoaded.connect(self._on_project_loaded)
            except Exception:
                pass
            try:
                # emitted after project is read (older API)
                self._qgs.readProject.connect(self._on_project_loaded)
            except Exception:
                pass
            try:
                # emitted when project is saved
                self._qgs.projectSaved.connect(self._on_project_saved)
            except Exception:
                pass

            # If no project file is currently available, start a short-lived
            # polling timer to detect when the user opens/saves a project and
            # then update the BBox config. This is a safe fallback across
            # QGIS versions.
            try:
                from qgis.PyQt.QtCore import QTimer
                if not self._qgs.fileName():
                    self._project_poll_timer = QTimer()
                    self._project_poll_timer.setInterval(1000)  # 1s
                    self._project_poll_timer.timeout.connect(self._check_project_file)
                    self._project_poll_timer.setSingleShot(False)
                    self._project_poll_timer.start()
                else:
                    self._project_poll_timer = None
            except Exception:
                self._project_poll_timer = None

        except Exception:
            self._qgs = None
            self._project_poll_timer = None
    
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
    
    def get_qgis_server_path(self) -> Optional[str]:
        """QGIS Server実行ファイルのパスを取得（存在する場合）
        
        以下の順序で検索:
        1. プラグインディレクトリ内（ダウンロード済みの場合）
        2. 現在実行中のQGIS Desktopのインストールディレクトリ
        
        OSGeo4Wパッケージの標準的なディレクトリ構造に対応:
        - apps/qgis-ltr/bin/qgis_mapserv.fcgi.exe
        - bin/qgis_mapserv.fcgi.exe
        - qgis_mapserv.fcgi.exe (直接配置)
        """
        if platform.system().lower() == 'windows':
            exe_name = 'qgis_mapserv.fcgi.exe'
        else:
            exe_name = 'qgis_mapserv.fcgi'
        
        # 1. プラグインディレクトリ内を検索
        paths_to_check = [
            os.path.join(self.qgis_server_dir, 'apps', 'qgis-ltr', 'bin', exe_name),
            os.path.join(self.qgis_server_dir, 'qgis-ltr', 'apps', 'qgis-ltr', 'bin', exe_name),
            os.path.join(self.qgis_server_dir, 'qgis-ltr', 'bin', exe_name),
            os.path.join(self.qgis_server_dir, 'bin', exe_name),
            os.path.join(self.qgis_server_dir, exe_name),
        ]
        
        for path in paths_to_check:
            if os.path.exists(path):
                print(f"Found QGIS Server at: {path}")
                return path
        
        # ディレクトリを再帰的に検索
        print(f"Searching for {exe_name} in {self.qgis_server_dir}...")
        try:
            for root, dirs, files in os.walk(self.qgis_server_dir):
                if exe_name in files:
                    found_path = os.path.join(root, exe_name)
                    print(f"Found QGIS Server via recursive search: {found_path}")
                    return found_path
        except Exception as e:
            print(f"Error during recursive search: {e}")
        
        # 2. 現在実行中のQGIS Desktopのインストールディレクトリを検索
        try:
            from qgis.core import QgsApplication
            qgis_prefix = QgsApplication.prefixPath()
            print(f"QGIS prefix path: {qgis_prefix}")
            
            # QGISインストールディレクトリから検索
            desktop_paths = [
                os.path.join(qgis_prefix, 'bin', exe_name),
                os.path.join(qgis_prefix, '..', 'bin', exe_name),
                os.path.join(qgis_prefix, 'apps', 'qgis-ltr', 'bin', exe_name),
                os.path.join(qgis_prefix, '..', 'apps', 'qgis-ltr', 'bin', exe_name),
            ]
            
            for path in desktop_paths:
                normalized_path = os.path.normpath(path)
                if os.path.exists(normalized_path):
                    print(f"Found QGIS Server in QGIS Desktop installation: {normalized_path}")
                    return normalized_path
        except Exception as e:
            print(f"Error searching QGIS Desktop installation: {e}")
        
        print(f"QGIS Server executable not found in: {self.qgis_server_dir} or QGIS Desktop installation")
        return None
    
    def is_qgis_server_available(self) -> bool:
        """QGIS Serverが利用可能か確認"""
        return self.get_qgis_server_path() is not None
    
    def is_running(self) -> bool:
        """サーバーが起動中か確認"""
        if self.process is None:
            return False
        
        # プロセスの生存確認
        return self.process.poll() is None
    
    def download_server(self, callback=None) -> bool:
        """BBoxとQGIS Serverの両方をダウンロード
        
        既にダウンロード済みのものはスキップします。
        
        Args:
            callback: 進捗コールバック (percent: int)
            
        Returns:
            bool: 必要なダウンロードが成功した場合True
        """
        try:
            print("Checking download status...")
            
            # 既存の状態を確認
            has_bbox = self.get_binary_path() is not None
            has_qgis_server = self.is_qgis_server_available()
            
            print(f"Current status - BBox: {has_bbox}, QGIS Server: {has_qgis_server}")
            
            bbox_success = True
            qgis_success = True
            
            # BBoxが無い場合のみダウンロード
            if not has_bbox:
                print("Downloading BBox...")
                self.status_changed.emit("Downloading BBox Server...")
                bbox_success = self._download_bbox(callback)
            else:
                print("BBox already exists, skipping BBox download...")
                print(f"Emitting progress: 50% (BBox skipped)")
                if callback:
                    callback(50)
                self.download_progress.emit(50)
            
            # QGIS Serverが無い場合のみダウンロード
            if not has_qgis_server:
                print("QGIS Server not found in plugin directory or QGIS Desktop installation")
                print("Downloading QGIS Server...")
                self.status_changed.emit("Downloading QGIS Server...")
                qgis_success = self._download_qgis_server(callback)
            else:
                print("QGIS Server already available (plugin dir or QGIS Desktop), skipping QGIS Server download...")
                print(f"Emitting progress: 100% (QGIS Server skipped)")
                if callback:
                    callback(100)
                self.download_progress.emit(100)
            
            # 両方成功または既存の場合
            if bbox_success and qgis_success:
                if not has_bbox or not has_qgis_server:
                    # 新規ダウンロードがあった場合
                    self.status_changed.emit("Download completed!")
                    QgsMessageLog.logMessage("Download completed successfully", 'QMapPermalink', Qgis.Success)
                else:
                    # 全てスキップされた場合
                    self.status_changed.emit("Already downloaded")
                    QgsMessageLog.logMessage("BBox and QGIS Server already exist", 'QMapPermalink', Qgis.Info)
                return True
            else:
                # エラーメッセージ
                error_msg = "Download failed: "
                if not bbox_success:
                    error_msg += "BBox "
                if not qgis_success:
                    error_msg += "QGIS Server"
                self.status_changed.emit(error_msg)
                QgsMessageLog.logMessage(error_msg, 'QMapPermalink', Qgis.Critical)
                return False
                
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            print(f"download_server() error: {error_msg}")
            import traceback
            traceback.print_exc()
            self.status_changed.emit(error_msg)
            QgsMessageLog.logMessage(error_msg, 'QMapPermalink', Qgis.Critical)
            return False
    
    def _download_bbox(self, callback=None) -> bool:
        """BBoxサーバーをダウンロード（内部メソッド）
        
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
                    # BBoxは0-50%の範囲で表示
                    percent = int((block_num * block_size * 50) / total_size)
                    
                    # ダウンロード済みサイズを計算
                    downloaded_mb = (block_num * block_size) / (1024 * 1024)
                    total_mb = total_size / (1024 * 1024)
                    
                    print(f"BBox download: {downloaded_mb:.1f}/{total_mb:.1f} MB ({percent}%)")
                    self.status_changed.emit(f"BBox Server: {downloaded_mb:.1f}/{total_mb:.1f} MB")
                    
                    if callback:
                        callback(min(percent, 50))
                    self.download_progress.emit(min(percent, 50))
            
            print(f"Starting urllib.request.urlretrieve...")
            urllib.request.urlretrieve(url, download_path, report_progress)
            print(f"Download completed, file size: {os.path.getsize(download_path)} bytes")
            
            # 解凍
            self.status_changed.emit("Extracting BBox Server...")
            print("Extracting BBox archive...")
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
            
            print("BBox download completed successfully")
            QgsMessageLog.logMessage("BBox Server downloaded successfully", 'QMapPermalink', Qgis.Success)
            return True
            
        except Exception as e:
            error_msg = f"BBox download failed: {str(e)}"
            print(f"_download_bbox() error: {error_msg}")
            import traceback
            traceback.print_exc()
            QgsMessageLog.logMessage(error_msg, 'QMapPermalink', Qgis.Critical)
            return False
    
    def _download_qgis_server(self, callback=None) -> bool:
        """QGIS Serverをダウンロード（内部メソッド）
        
        OSGeo4WパッケージからQGIS Server関連ファイルを抽出します。
        
        Args:
            callback: 進捗コールバック (percent: int)
            
        Returns:
            bool: 成功した場合True
        """
        try:
            print("=== Starting QGIS Server download from OSGeo4W ===")
            # ディレクトリが存在することを確認
            os.makedirs(self.qgis_server_dir, exist_ok=True)
            print(f"QGIS Server directory created: {self.qgis_server_dir}")
            
            # 初期進捗を発火（ダウンロード開始を通知）
            print("Emitting initial progress: 50%")
            if callback:
                callback(50)
            self.download_progress.emit(50)
            
            # OSGeo4W v2 QGIS LTR (3.34.x) のパッケージをダウンロード
            # QGIS Server は qgis-ltr パッケージに含まれている
            qgis_major_minor = ".".join(self.QGIS_SERVER_VERSION.split(".")[:2])  # "3.34"
            
            # OSGeo4W v2のミラーから必要なパッケージをダウンロード
            # qgis-ltr-server: QGIS Serverバイナリ (qgis_mapserv.fcgi.exe)のみ
            # 正しいパス: /qgis/qgis-ltr/qgis-ltr-server/
            packages = [
                {
                    'name': 'qgis-ltr-server',
                    'url': f'https://download.osgeo.org/osgeo4w/v2/x86_64/release/qgis/qgis-ltr/qgis-ltr-server/qgis-ltr-server-{self.QGIS_SERVER_VERSION}-1.tar.bz2',
                    'weight': 1.0  # 100%の進捗割当
                }
            ]
            
            base_progress = 50  # QGIS Serverは50-100%の範囲
            accumulated_progress = 0
            
            for pkg in packages:
                pkg_name = pkg['name']
                pkg_url = pkg['url']
                pkg_weight = pkg['weight']
                
                print(f"=== Package: {pkg_name} ===")
                print(f"URL: {pkg_url}")
                print(f"Weight: {pkg_weight}")
                self.status_changed.emit(f"Downloading {pkg_name}...")
                QgsMessageLog.logMessage(f"Downloading {pkg_name} from: {pkg_url}", 'QMapPermalink', Qgis.Info)
                
                # ダウンロード先
                filename = pkg_url.split('/')[-1]
                download_path = os.path.join(self.qgis_server_dir, filename)
                print(f"Download path: {download_path}")
                
                # 進捗レポート関数（各パッケージごとに範囲を調整）
                def report_progress(block_num, block_size, total_size):
                    if total_size > 0:
                        pkg_percent = (block_num * block_size * 100) / total_size
                        # 全体進捗 = 50 + (このパッケージまでの累積 + 現在のパッケージ進捗 * weight) * 50
                        total_percent = base_progress + int((accumulated_progress + (pkg_percent / 100) * pkg_weight) * 50)
                        
                        # ダウンロード済みサイズを計算
                        downloaded_mb = (block_num * block_size) / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        
                        print(f"{pkg_name} download: {downloaded_mb:.1f}/{total_mb:.1f} MB ({pkg_percent:.1f}%) - Overall: {total_percent}%")
                        self.status_changed.emit(f"{pkg_name}: {downloaded_mb:.1f}/{total_mb:.1f} MB")
                        
                        if callback:
                            callback(min(total_percent, 100))
                        self.download_progress.emit(min(total_percent, 100))
                
                # ダウンロード実行
                try:
                    print(f"Starting urlretrieve for {pkg_name}...")
                    print(f"Checking URL accessibility...")
                    # URLの存在確認
                    req = urllib.request.Request(pkg_url, method='HEAD')
                    try:
                        response = urllib.request.urlopen(req, timeout=10)
                        print(f"URL is accessible, status: {response.status}")
                        print(f"Content-Length: {response.headers.get('Content-Length', 'unknown')}")
                    except urllib.error.HTTPError as e:
                        print(f"HTTP Error: {e.code} - {e.reason}")
                        raise Exception(f"URL not found: {pkg_url} (HTTP {e.code})")
                    except Exception as e:
                        print(f"URL check failed: {str(e)}")
                        raise
                    
                    print(f"Starting actual download...")
                    urllib.request.urlretrieve(pkg_url, download_path, report_progress)
                    print(f"{pkg_name} download completed, file size: {os.path.getsize(download_path)} bytes")
                except Exception as e:
                    error_msg = f"Failed to download {pkg_name}: {str(e)}"
                    print(f"ERROR: {error_msg}")
                    QgsMessageLog.logMessage(error_msg, 'QMapPermalink', Qgis.Critical)
                    # ダウンロード失敗は致命的エラー
                    raise Exception(error_msg)
                
                # 解凍
                self.status_changed.emit(f"Extracting {pkg_name}...")
                print(f"Extracting {pkg_name} archive...")
                
                try:
                    import tarfile
                    print(f"Opening tar.bz2 file: {download_path}")
                    with tarfile.open(download_path, 'r:bz2') as tar_ref:
                        members = tar_ref.getmembers()
                        total_files = len(members)
                        print(f"Extracting {total_files} files from {pkg_name}...")
                        
                        # デバッグ: 最初の10ファイルを表示
                        print("First 10 files in archive:")
                        for i, member in enumerate(members[:10]):
                            print(f"  {member.name}")
                        
                        tar_ref.extractall(self.qgis_server_dir)
                    print(f"{pkg_name} extraction completed ({total_files} files)")
                    
                    # デバッグ: 展開後のディレクトリ構造を確認
                    print(f"Directory structure after extraction:")
                    for root, dirs, files in os.walk(self.qgis_server_dir):
                        level = root.replace(self.qgis_server_dir, '').count(os.sep)
                        indent = ' ' * 2 * level
                        print(f"{indent}{os.path.basename(root)}/")
                        subindent = ' ' * 2 * (level + 1)
                        for file in files[:5]:  # 最初の5ファイルのみ表示
                            print(f"{subindent}{file}")
                        if len(files) > 5:
                            print(f"{subindent}... and {len(files) - 5} more files")
                        if level > 2:  # 深すぎる場合は打ち切り
                            break
                    
                    # ダウンロードファイル削除
                    os.remove(download_path)
                    print(f"Removed archive: {download_path}")
                except Exception as e:
                    print(f"Warning: Failed to extract {pkg_name}: {str(e)}")
                    QgsMessageLog.logMessage(f"Failed to extract {pkg_name}: {str(e)}", 'QMapPermalink', Qgis.Warning)
                
                # 累積進捗更新
                accumulated_progress += pkg_weight
            
            # qgis_mapserv.fcgi.exeが存在するか確認
            qgis_exe = self.get_qgis_server_path()
            if qgis_exe and os.path.exists(qgis_exe):
                print(f"QGIS Server executable found: {qgis_exe}")
                QgsMessageLog.logMessage("QGIS Server downloaded successfully", 'QMapPermalink', Qgis.Success)
                if callback:
                    callback(100)
                self.download_progress.emit(100)
                return True
            else:
                # ダウンロードは成功したが、期待する場所にファイルが見つからない
                print(f"Warning: qgis_mapserv.fcgi.exe not found at expected location")
                # ディレクトリ内を検索
                for root, dirs, files in os.walk(self.qgis_server_dir):
                    for file in files:
                        if file == 'qgis_mapserv.fcgi.exe':
                            found_path = os.path.join(root, file)
                            print(f"Found qgis_mapserv.fcgi.exe at: {found_path}")
                            QgsMessageLog.logMessage(f"QGIS Server found at: {found_path}", 'QMapPermalink', Qgis.Success)
                            return True
                
                # 見つからない場合は警告
                print("Warning: QGIS Server binaries not found after extraction")
                QgsMessageLog.logMessage("QGIS Server binaries not found after extraction. Manual installation may be required.", 'QMapPermalink', Qgis.Warning)
                return False
            
        except Exception as e:
            error_msg = f"QGIS Server download failed: {str(e)}"
            print(f"_download_qgis_server() error: {error_msg}")
            import traceback
            traceback.print_exc()
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
        
        # Projects dir is still created for backward compatibility, but
        # we prefer using the actual project directory as project_basedir
        projects_dir = os.path.join(self.config_dir, 'projects')
        os.makedirs(projects_dir, exist_ok=True)

        # (project_dir will be determined after we resolve project_used_path)

        # プロジェクトのパス決定ロジック:
        # 1) 引数 `project` が与えられ、ファイルパスを指定している場合はそれを使う
        # 2) 可能なら現在開いている QGIS プロジェクトのパスを使う
        # 3) プロジェクトが未保存の場合は plugin 内に保存 (projects/current.qgs)
        project_saved = False
        project_used_path = None

        try:
            from qgis.core import QgsProject
        except Exception:
            QgsProject = None

        # 1) project がファイルパス文字列なら優先
        if project and isinstance(project, str) and os.path.exists(project):
            project_used_path = project

        # 2) project が QgsProject インスタンス
        if project and QgsProject and isinstance(project, QgsProject):
            qgs_project = project
            proj_file = qgs_project.fileName()
            if proj_file:
                project_used_path = proj_file

        # 3) 引数がない場合は現在のプロジェクトを試す
        if project_used_path is None and QgsProject:
            try:
                qgs_project = QgsProject.instance()
                proj_file = qgs_project.fileName()
                if proj_file:
                    project_used_path = proj_file
                else:
                    # プロジェクトが未保存の場合は自動保存せずエラー扱いにする
                    error_msg = "Current QGIS project is not saved. Please save the project before creating BBox config."
                    QgsMessageLog.logMessage(error_msg, 'QMapPermalink', Qgis.Critical)
                    self.status_changed.emit(error_msg)
                    return None
            except Exception:
                # QgsProject.instance() が取得できない環境ではエラー
                error_msg = "Failed to access current QGIS project."
                QgsMessageLog.logMessage(error_msg, 'QMapPermalink', Qgis.Critical)
                self.status_changed.emit(error_msg)
                return None

        # project_used_path が決まったらプロジェクトは "保存済み" とみなす
        if project_used_path:
            project_saved = True
        # Determine project directory (parent of project_used_path) if available
        project_dir = None
        if project_used_path:
            try:
                project_dir = os.path.dirname(os.path.abspath(project_used_path))
            except Exception:
                project_dir = None
        
        # プロジェクトディレクトリをスラッシュに統一
        projects_dir_normalized = projects_dir.replace('\\', '/')

        # 基本設定を生成
        config_lines = [
            "# BBOX Server Configuration",
            "# Generated by QMapPermalink",
            "",
            "[service]",
            'seeding = false',
            "",
            "[webserver]",
            f'server_addr = "127.0.0.1:{port}"',
            "worker_threads = 4",
            "",
            "[webserver.cors]",
            'allow_all_origins = true',
            ""
        ]
        
        # Map server設定を追加（QGISプロジェクトファイル配信用）
        if project_saved:
            # QGIS Serverのパスを取得
            qgis_server_path = self.get_qgis_server_path()
            qgis_server_dir = os.path.dirname(qgis_server_path) if qgis_server_path else ""

            # project_basedir: prefer actual project directory. If project_dir is
            # not available, treat this as an error (do not silently fall back).
            if project_dir:
                project_basedir_value = project_dir.replace('\\', '/')
            else:
                error_msg = (
                    "Failed to determine project directory. "
                    "Please save your QGIS project and try again."
                )
                QgsMessageLog.logMessage(error_msg, 'QMapPermalink', Qgis.Critical)
                try:
                    self.status_changed.emit(error_msg)
                except Exception:
                    pass
                return None

            config_lines.extend([
                "# Map Server (QGIS Backend)",
                "[mapserver]",
                'backend = "qgis_backend"',
                "",
                "[mapserver.qgis_backend]",
                f'project_basedir = "{project_basedir_value}"',
            ])

            # QGIS Serverが利用可能な場合は、exe_locationを追加
            if qgis_server_path:
                qgis_server_path_normalized = qgis_server_path.replace('\\', '/')
                config_lines.append(f'exe_location = "{qgis_server_path_normalized}"')
                QgsMessageLog.logMessage(
                    f"QGIS Server path configured: {qgis_server_path}",
                    'QMapPermalink', Qgis.Info
                )
            else:
                QgsMessageLog.logMessage(
                    "Warning: QGIS Server not found. Map server features may not work.",
                    'QMapPermalink', Qgis.Warning
                )

            # Ensure the backend section is explicitly enabled so bbox-server
            # recognizes and attempts to start the QGIS backend.
            config_lines.append('enabled = true')

            # Decide what to write for the QGS path. Prefer the project file
            # name relative to project_basedir when possible; otherwise use the
            # absolute project file path.
            try:
                proj_basename = os.path.basename(project_used_path)
            except Exception:
                proj_basename = None

            qgs_path_value = None
            try:
                # If project_basedir_value matches the project file's parent,
                # write only the basename so BBOX will resolve it relative to
                # project_basedir. Otherwise write the absolute path.
                if project_dir and proj_basename:
                    parent_norm = os.path.normpath(project_dir)
                    cfg_parent_norm = os.path.normpath(project_basedir_value)
                    if parent_norm == cfg_parent_norm:
                        qgs_path_value = proj_basename
                    else:
                        qgs_path_value = project_used_path.replace('\\', '/')
                else:
                    qgs_path_value = project_used_path.replace('\\', '/') if project_used_path else '/qgis'
            except Exception:
                qgs_path_value = project_used_path.replace('\\', '/') if project_used_path else '/qgis'

            config_lines.extend([
                "",
                "[mapserver.qgis_backend.qgs]",
                f'path = "{qgs_path_value}"',
                ""
            ])
        
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
            if not config_path:
                QgsMessageLog.logMessage("BBox config creation failed. Aborting start.", 'QMapPermalink', Qgis.Critical)
                return False
            
            # QGIS Server用の環境変数を準備
            env = os.environ.copy()
            qgis_server_path = self.get_qgis_server_path()
            
            if qgis_server_path:
                # QGIS Serverのベースディレクトリ
                qgis_server_base = os.path.dirname(os.path.dirname(qgis_server_path))  # .../apps/qgis-ltr
                qgis_root = os.path.dirname(qgis_server_base)  # .../apps
                
                # QGIS_PREFIX_PATH を設定（QGIS Serverが依存ファイルを見つけるため）
                env['QGIS_PREFIX_PATH'] = qgis_server_base
                
                # PATH に QGIS Server の bin ディレクトリを追加（DLL検索用）
                qgis_bin_dir = os.path.dirname(qgis_server_path)
                if 'PATH' in env:
                    env['PATH'] = f"{qgis_bin_dir};{env['PATH']}"
                else:
                    env['PATH'] = qgis_bin_dir
                
                print(f"QGIS Server environment configured:")
                print(f"  QGIS_PREFIX_PATH: {qgis_server_base}")
                print(f"  PATH (added): {qgis_bin_dir}")
                
                QgsMessageLog.logMessage(
                    f"QGIS Server environment configured: PREFIX={qgis_server_base}",
                    'QMapPermalink', Qgis.Info
                )
            
            # サーバー起動
            self.status_changed.emit(f"Starting BBOX Server on port {port}...")
            
            if platform.system().lower() == 'windows':
                # Windows: ウィンドウを表示しない
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                self.process = subprocess.Popen(
                    [exe_path, '--config', config_path, 'serve', config_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo,
                    cwd=self.plugin_dir,
                    env=env  # 環境変数を渡す
                )
            else:
                # Unix系
                self.process = subprocess.Popen(
                    [exe_path, '--config', config_path, 'serve', config_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.plugin_dir,
                    env=env  # 環境変数を渡す
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

    # ---- Project load/save handlers ----
    def _on_project_loaded(self, *args, **kwargs):
        """Called when a QGIS project is loaded; regenerate bbox config."""
        try:
            from qgis.core import QgsProject, QgsMessageLog, Qgis
            proj_file = QgsProject.instance().fileName()
            if proj_file:
                # regenerate config using the newly loaded project
                try:
                    self.create_config(self.current_port or self.BBOX_PORT, project=proj_file)
                    QgsMessageLog.logMessage('BBox config updated after project load', 'QMapPermalink', Qgis.Info)
                except Exception as e:
                    QgsMessageLog.logMessage(f'Failed to update BBox config after project load: {e}', 'QMapPermalink', Qgis.Warning)

                # stop polling if it was active
                try:
                    if getattr(self, '_project_poll_timer', None):
                        self._project_poll_timer.stop()
                        self._project_poll_timer = None
                except Exception:
                    pass
        except Exception:
            pass

    def _on_project_saved(self, *args, **kwargs):
        """Called when a QGIS project is saved; regenerate bbox config."""
        try:
            from qgis.core import QgsProject, QgsMessageLog, Qgis
            proj_file = QgsProject.instance().fileName()
            if proj_file:
                try:
                    self.create_config(self.current_port or self.BBOX_PORT, project=proj_file)
                    QgsMessageLog.logMessage('BBox config updated after project save', 'QMapPermalink', Qgis.Info)
                except Exception as e:
                    QgsMessageLog.logMessage(f'Failed to update BBox config after project save: {e}', 'QMapPermalink', Qgis.Warning)
        except Exception:
            pass

    def _check_project_file(self):
        """Polling fallback: check whether a project file has appeared."""
        try:
            from qgis.core import QgsProject
            if not self._qgs:
                self._qgs = QgsProject.instance()
            if self._qgs and self._qgs.fileName():
                # call loaded handler
                self._on_project_loaded()
        except Exception:
            pass
