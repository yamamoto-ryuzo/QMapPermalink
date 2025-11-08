#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QGIS Server Manager for Plugin
プラグインからQGIS Serverを自動起動・管理
"""
import sys
import os
import subprocess
import socket
from pathlib import Path


class QGISServerManager:
    """QGIS Serverの起動と管理を行うクラス"""
    
    def __init__(self):
        self.process = None
        self.port = None
        self.project_file = None
        
    def find_qgis_server_exe(self):
        """現在実行中のQGISからQGIS Server実行ファイルのパスを検出
        
        Returns:
            str: QGIS Server実行ファイルのパス、見つからない場合はNone
        """
        try:
            # 現在のPythonインタープリタのパスからQGISインストールディレクトリを推測
            python_exe = sys.executable
            
            # パターン1: OSGeo4W環境
            # 例: C:\OSGeo4W\apps\Python312\python.exe
            # →  C:\OSGeo4W\apps\qgis\bin\qgis_mapserv.fcgi.exe
            if 'OSGeo4W' in python_exe:
                osgeo_root = None
                path_parts = Path(python_exe).parts
                for i, part in enumerate(path_parts):
                    if part.lower() == 'osgeo4w':
                        osgeo_root = Path(*path_parts[:i+1])
                        break
                
                if osgeo_root:
                    qgis_server = osgeo_root / 'apps' / 'qgis' / 'bin' / 'qgis_mapserv.fcgi.exe'
                    if qgis_server.exists():
                        return str(qgis_server)
            
            # パターン2: Standalone QGIS
            # 例: C:\Program Files\QGIS 3.44.3\apps\Python312\python.exe
            # →  C:\Program Files\QGIS 3.44.3\bin\qgis_mapserv.fcgi.exe
            if 'QGIS' in python_exe or 'qgis' in python_exe.lower():
                qgis_root = None
                path_parts = Path(python_exe).parts
                for i, part in enumerate(path_parts):
                    if 'qgis' in part.lower():
                        qgis_root = Path(*path_parts[:i+1])
                        break
                
                if qgis_root:
                    qgis_server = qgis_root / 'bin' / 'qgis_mapserv.fcgi.exe'
                    if qgis_server.exists():
                        return str(qgis_server)
            
            # パターン3: 環境変数からQGIS_PREFIX_PATHを取得
            qgis_prefix = os.environ.get('QGIS_PREFIX_PATH')
            if qgis_prefix:
                qgis_server = Path(qgis_prefix) / 'bin' / 'qgis_mapserv.fcgi.exe'
                if qgis_server.exists():
                    return str(qgis_server)
            
            # Linux/macOS の場合
            if sys.platform != 'win32':
                # よくあるパス
                common_paths = [
                    '/usr/lib/cgi-bin/qgis_mapserv.fcgi',
                    '/usr/local/lib/cgi-bin/qgis_mapserv.fcgi',
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        return path
            
            return None
            
        except Exception as e:
            print(f"Error detecting QGIS Server: {e}")
            return None
    
    def find_available_port(self, start_port=8090, end_port=8100):
        """利用可能なポートを検索
        
        Args:
            start_port: 開始ポート番号
            end_port: 終了ポート番号
            
        Returns:
            int: 利用可能なポート番号、見つからない場合はNone
        """
        for port in range(start_port, end_port + 1):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        return None
    
    def start_server(self, project_file, port=None):
        """QGIS Serverを起動
        
        Args:
            project_file: QGISプロジェクトファイルのパス
            port: 使用するポート番号（Noneの場合は自動検出）
            
        Returns:
            tuple: (成功フラグ, ポート番号 or エラーメッセージ)
        """
        try:
            # すでに起動している場合は停止
            if self.process:
                self.stop_server()
            
            # QGIS Server実行ファイルを検出
            qgis_server_exe = self.find_qgis_server_exe()
            if not qgis_server_exe:
                return False, "QGIS Server executable not found. Please install QGIS Server."
            
            # プロジェクトファイルの存在確認
            if not os.path.exists(project_file):
                return False, f"Project file not found: {project_file}"
            
            # ポートを確定
            if port is None:
                port = self.find_available_port()
                if port is None:
                    return False, "No available port found (8090-8100)"
            else:
                # 指定されたポートが使用可能か確認
                test_port = self.find_available_port(port, port)
                if test_port is None:
                    # 別のポートを探す
                    port = self.find_available_port()
                    if port is None:
                        return False, f"Port {port} is in use and no alternative found"
            
            # ラッパースクリプトのパス
            wrapper_script = os.path.join(
                os.path.dirname(__file__),
                'qgis_server_wrapper.py'
            )
            
            if not os.path.exists(wrapper_script):
                return False, f"Wrapper script not found: {wrapper_script}"
            
            # QGIS Serverを起動
            self.process = subprocess.Popen(
                [sys.executable, wrapper_script, qgis_server_exe, project_file, str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            self.port = port
            self.project_file = project_file
            
            return True, port
            
        except Exception as e:
            return False, f"Failed to start QGIS Server: {str(e)}"
    
    def stop_server(self):
        """QGIS Serverを停止
        
        Returns:
            bool: 成功フラグ
        """
        try:
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                
                self.process = None
                self.port = None
                self.project_file = None
                return True
            return False
            
        except Exception as e:
            print(f"Error stopping QGIS Server: {e}")
            return False
    
    def is_running(self):
        """QGIS Serverが起動しているか確認
        
        Returns:
            bool: 起動している場合はTrue
        """
        if self.process:
            return self.process.poll() is None
        return False
    
    def get_status(self):
        """QGIS Serverのステータスを取得
        
        Returns:
            dict: ステータス情報
        """
        return {
            'running': self.is_running(),
            'port': self.port,
            'project_file': self.project_file
        }
