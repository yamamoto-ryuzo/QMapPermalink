#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove verbose INFO logs from Python files"""

import re
import os

def remove_info_logs(file_path):
    """Remove verbose INFO logs while keeping important ones"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    skip_next = False
    
    for i, line in enumerate(lines):
        # 重要なログは残す(サーバー起動/停止)
        if '🚀 QMap Permalink' in line or 'HTTPサーバーが停止しました' in line or 'QMap Permalink HTTPサーバーが停止しました' in line:
            new_lines.append(line)
            continue
        
        # INFOレベルの詳細ログを削除
        if 'Qgis.Info' in line and 'QgsMessageLog.logMessage' in line:
            # 削除対象のパターン
            skip_patterns = [
                '📡', '🌐', '📍', 'ℹ️', '🔒', '📐', '🔄', '🎯', '✅',
                '🔍', '📊', '🗺️', '🌍', 'WFS layers returned',
                'Bookmark', 'navigation_data', 'Permalink', 'BBOX'
            ]
            if any(pattern in line for pattern in skip_patterns):
                continue
        
        new_lines.append(line)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    return len(lines) - len(new_lines)

# ファイルリスト
files = [
    r'c:\github\QMapPermalink\qmap_permalink\qmap_permalink_server_manager.py',
    r'c:\github\QMapPermalink\qmap_permalink\qmap_wms_service.py',
    r'c:\github\QMapPermalink\qmap_permalink\qmap_wmts_service.py',
    r'c:\github\QMapPermalink\qmap_permalink\qmap_wfs_service.py',
]

for file_path in files:
    if os.path.exists(file_path):
        removed = remove_info_logs(file_path)
        print(f'{os.path.basename(file_path)}: {removed} lines removed')
    else:
        print(f'{file_path}: NOT FOUND')

print('\nDone!')
