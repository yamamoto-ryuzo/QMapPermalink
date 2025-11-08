@echo off
REM QGIS Server を起動してWMSサービスを高速化
REM QGISが既に起動している環境でも動作します

setlocal

REM QGIS インストールパス（環境に応じて調整）
set QGIS_PREFIX_PATH=C:\Program Files\QGIS 3.44.3
set OSGEO4W_ROOT=C:\OSGeo4W

REM プロジェクトファイル（引数または環境変数から）
if "%~1"=="" (
    echo Usage: %~nx0 ^<project_file.qgs^> [port]
    echo Example: %~nx0 myproject.qgs 8090
    echo.
    echo This script starts QGIS Server for fast WMS service.
    echo Use a different port from the plugin (default plugin port: 8089)
    exit /b 1
)

set PROJECT_FILE=%~1
set SERVER_PORT=%~2

if "%SERVER_PORT%"=="" set SERVER_PORT=8090

REM プロジェクトファイルの存在確認
if not exist "%PROJECT_FILE%" (
    echo ERROR: Project file not found: %PROJECT_FILE%
    exit /b 1
)

REM 絶対パスに変換
for %%i in ("%PROJECT_FILE%") do set "PROJECT_FILE_ABS=%%~fi"

echo ========================================
echo QGIS Server Launcher for WMS
echo ========================================
echo Project: %PROJECT_FILE_ABS%
echo Port: %SERVER_PORT%
echo ========================================
echo.

REM OSGeo4W環境の設定
if exist "%OSGEO4W_ROOT%\bin\o4w_env.bat" (
    echo Using OSGeo4W installation...
    call "%OSGEO4W_ROOT%\bin\o4w_env.bat"
    set "QGIS_SERVER_EXE=%OSGEO4W_ROOT%\apps\qgis\bin\qgis_mapserv.fcgi.exe"
) else if exist "%QGIS_PREFIX_PATH%\bin\qgis_mapserv.fcgi.exe" (
    echo Using QGIS standalone installation...
    set PATH=%QGIS_PREFIX_PATH%\bin;%PATH%
    set "QGIS_SERVER_EXE=%QGIS_PREFIX_PATH%\bin\qgis_mapserv.fcgi.exe"
) else (
    echo ERROR: QGIS Server executable not found
    echo Please edit this script and set QGIS_PREFIX_PATH or OSGEO4W_ROOT
    exit /b 1
)

REM QGIS Server環境変数
set QGIS_SERVER_LOG_LEVEL=0
set QGIS_SERVER_LOG_STDERR=1
set MAX_CACHE_LAYERS=100
set QGIS_SERVER_CACHE_SIZE=50000000

REM FastCGIラッパーとしてPythonを使用
echo Starting QGIS Server with Python HTTP wrapper...
echo.
echo Access WMS at:
echo   http://localhost:%SERVER_PORT%/?SERVICE=WMS^&REQUEST=GetCapabilities
echo.
echo Press Ctrl+C to stop the server
echo.

REM Pythonラッパースクリプトを実行
python "%~dp0qgis_server_wrapper.py" "%QGIS_SERVER_EXE%" "%PROJECT_FILE_ABS%" %SERVER_PORT%

endlocal
