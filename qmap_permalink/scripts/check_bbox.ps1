# check_bbox.ps1
# bbox-server.exe を一般的なプラグインパスで検索する簡易スクリプト
# 注意: PowerShell では ".=" は無効です。代わりに "=" または "+=" を使います。

$searchPaths = @()
$searchPaths += Join-Path $env:APPDATA 'QGIS\QGIS3\profiles\portable\python\plugins'
$searchPaths += Join-Path $env:APPDATA 'QGIS\QGIS3\profiles\default\python\plugins'
$searchPaths += Join-Path $env:APPDATA 'QGIS\QGIS3\profiles\portable\python\plugins\bbox\bin'
$searchPaths += Join-Path $env:APPDATA 'QGIS\QGIS3\profiles\default\python\plugins\bbox\bin'
# リポジトリ直下で実行する可能性があるため、相対パスも追加
$searchPaths += Join-Path (Get-Location) 'qmap_permalink\bbox\bin'

# 存在するパスだけに絞る
$searchPaths = $searchPaths | Where-Object { Test-Path $_ }

Write-Host "Checking these paths:`n$($searchPaths -join "`n")`n"

$found = @()
foreach ($p in $searchPaths) {
    $items = Get-ChildItem -Path $p -Recurse -Filter 'bbox-server.exe' -ErrorAction SilentlyContinue
    if ($items) { $found += $items | Select-Object -ExpandProperty FullName }
}

if ($found.Count -gt 0) {
    Write-Host "Found bbox-server.exe:" -ForegroundColor Green
    $found | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "No bbox-server.exe found in the checked locations." -ForegroundColor Yellow
    Write-Host "If you want to search more broadly, run:`n  Get-ChildItem -Path $env:APPDATA\QGIS -Recurse -Filter 'bbox-server.exe' -ErrorAction SilentlyContinue | Select-Object FullName" -ForegroundColor DarkYellow
}
