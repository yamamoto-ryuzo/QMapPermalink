#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QGIS Server HTTP Wrapper
FastCGI形式のQGIS ServerをHTTPサーバーとしてラップします
"""
import sys
import os
import subprocess
import http.server
import socketserver
import urllib.parse
from io import BytesIO
import threading
import socket

class QGISServerHandler(http.server.BaseHTTPRequestHandler):
    """QGIS ServerへのリクエストをFastCGI経由で転送"""
    
    def __init__(self, *args, qgis_server_exe=None, project_file=None, **kwargs):
        self.qgis_server_exe = qgis_server_exe
        self.project_file = project_file
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """GETリクエストを処理"""
        try:
            # パスとクエリを解析
            parsed = urllib.parse.urlparse(self.path)
            query = parsed.query
            
            # QGIS Serverを実行
            result = self._call_qgis_server(query)
            
            if result:
                # 成功レスポンス
                content_type, body = result
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', len(body))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(body)
            else:
                # エラーレスポンス
                self.send_error(500, "QGIS Server error")
                
        except Exception as e:
            print(f"Error handling request: {e}")
            self.send_error(500, str(e))
    
    def _call_qgis_server(self, query_string):
        """QGIS Serverを呼び出してレスポンスを取得"""
        try:
            # 環境変数を設定
            env = os.environ.copy()
            env['QUERY_STRING'] = query_string
            env['REQUEST_METHOD'] = 'GET'
            env['QGIS_PROJECT_FILE'] = self.project_file
            
            # QGIS Serverを実行
            proc = subprocess.Popen(
                [self.qgis_server_exe],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = proc.communicate(timeout=30)
            
            if stderr:
                print(f"QGIS Server stderr: {stderr.decode('utf-8', errors='ignore')}")
            
            # レスポンスをパース
            return self._parse_fcgi_response(stdout)
            
        except subprocess.TimeoutExpired:
            print("QGIS Server timeout")
            proc.kill()
            return None
        except Exception as e:
            print(f"Error calling QGIS Server: {e}")
            return None
    
    def _parse_fcgi_response(self, data):
        """FastCGIレスポンスからHTTPレスポンスを抽出"""
        try:
            # ヘッダーとボディを分離
            parts = data.split(b'\r\n\r\n', 1)
            if len(parts) != 2:
                parts = data.split(b'\n\n', 1)
            
            if len(parts) == 2:
                headers_data, body = parts
            else:
                # ヘッダーが見つからない場合は全体をボディとして扱う
                headers_data = b''
                body = data
            
            # Content-Typeを抽出
            content_type = 'text/xml; charset=utf-8'  # デフォルト
            if headers_data:
                headers_text = headers_data.decode('utf-8', errors='ignore')
                for line in headers_text.split('\n'):
                    if line.lower().startswith('content-type:'):
                        content_type = line.split(':', 1)[1].strip()
                        break
            
            return content_type, body
            
        except Exception as e:
            print(f"Error parsing response: {e}")
            return 'text/plain', b'Error parsing response'
    
    def log_message(self, format, *args):
        """ログメッセージをカスタマイズ"""
        print(f"{self.address_string()} - {format % args}")


def create_handler_class(qgis_server_exe, project_file):
    """ハンドラークラスを生成"""
    def handler(*args, **kwargs):
        QGISServerHandler(*args, qgis_server_exe=qgis_server_exe, 
                         project_file=project_file, **kwargs)
    return handler


def find_available_port(start_port, end_port):
    """利用可能なポートを検索"""
    for port in range(start_port, end_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None


def main():
    """メイン関数"""
    if len(sys.argv) < 3:
        print("Usage: python qgis_server_wrapper.py <qgis_server_exe> <project_file> [port]")
        sys.exit(1)
    
    qgis_server_exe = sys.argv[1]
    project_file = sys.argv[2]
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8090
    
    # ファイルの存在確認
    if not os.path.exists(qgis_server_exe):
        print(f"ERROR: QGIS Server executable not found: {qgis_server_exe}")
        sys.exit(1)
    
    if not os.path.exists(project_file):
        print(f"ERROR: Project file not found: {project_file}")
        sys.exit(1)
    
    # ポートが使用中の場合は別のポートを探す
    available_port = find_available_port(port, port + 10)
    if available_port is None:
        print(f"ERROR: No available port found in range {port}-{port+10}")
        sys.exit(1)
    
    if available_port != port:
        print(f"WARNING: Port {port} is in use, using port {available_port} instead")
        port = available_port
    
    # ハンドラークラスを作成
    handler = create_handler_class(qgis_server_exe, project_file)
    
    # HTTPサーバーを起動
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"QGIS Server HTTP Wrapper started on port {port}")
            print(f"Project: {project_file}")
            print(f"")
            print(f"WMS GetCapabilities:")
            print(f"  http://localhost:{port}/?SERVICE=WMS&REQUEST=GetCapabilities")
            print(f"")
            print(f"Example GetMap:")
            print(f"  http://localhost:{port}/?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0")
            print(f"  &LAYERS=<layer>&CRS=EPSG:3857&BBOX=<bbox>&WIDTH=800&HEIGHT=600&FORMAT=image/png")
            print(f"")
            print(f"Press Ctrl+C to stop")
            print("")
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
