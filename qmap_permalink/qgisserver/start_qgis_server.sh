#!/bin/bash
# QGIS Server を起動してWMSサービスを高速化
# QGISが既に起動している環境でも動作します

# QGIS インストールパス
QGIS_PREFIX_PATH="${QGIS_PREFIX_PATH:-/usr}"

# プロジェクトファイル
if [ -z "$1" ]; then
    echo "Usage: $0 <project_file.qgs> [port]"
    echo "Example: $0 myproject.qgs 8090"
    echo ""
    echo "This script starts QGIS Server for fast WMS service."
    echo "Use a different port from the plugin (default plugin port: 8089)"
    exit 1
fi

PROJECT_FILE="$1"
SERVER_PORT="${2:-8090}"

# プロジェクトファイルの存在確認
if [ ! -f "$PROJECT_FILE" ]; then
    echo "ERROR: Project file not found: $PROJECT_FILE"
    exit 1
fi

# 絶対パスに変換
PROJECT_FILE_ABS="$(realpath "$PROJECT_FILE")"

echo "========================================"
echo "QGIS Server Launcher for WMS"
echo "========================================"
echo "Project: $PROJECT_FILE_ABS"
echo "Port: $SERVER_PORT"
echo "========================================"
echo ""

# QGIS Server実行ファイルを探す
QGIS_SERVER_EXE=""
for path in \
    "${QGIS_PREFIX_PATH}/lib/cgi-bin/qgis_mapserv.fcgi" \
    "/usr/lib/cgi-bin/qgis_mapserv.fcgi" \
    "/usr/local/lib/cgi-bin/qgis_mapserv.fcgi"; do
    if [ -x "$path" ]; then
        QGIS_SERVER_EXE="$path"
        echo "Found QGIS Server: $QGIS_SERVER_EXE"
        break
    fi
done

if [ -z "$QGIS_SERVER_EXE" ]; then
    echo "ERROR: QGIS Server executable not found"
    echo "Please install QGIS Server or set QGIS_PREFIX_PATH"
    exit 1
fi

# QGIS Server環境変数
export QGIS_SERVER_LOG_LEVEL=0
export QGIS_SERVER_LOG_STDERR=1
export MAX_CACHE_LAYERS=100
export QGIS_SERVER_CACHE_SIZE=50000000

# Pythonラッパースクリプトを実行
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting QGIS Server with Python HTTP wrapper..."
echo ""
echo "Access WMS at:"
echo "  http://localhost:${SERVER_PORT}/?SERVICE=WMS&REQUEST=GetCapabilities"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 "$SCRIPT_DIR/qgis_server_wrapper.py" "$QGIS_SERVER_EXE" "$PROJECT_FILE_ABS" "$SERVER_PORT"
