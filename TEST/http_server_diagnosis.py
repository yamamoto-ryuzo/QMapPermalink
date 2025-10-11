#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMapPermalink HTTPサーバー診断ツール

HTTPサーバーの現在の状態、利用可能なポート、
プラグインの設定状況を診断します。
"""

import socket
import urllib.request
import urllib.error
import json
import time

def check_port_availability(port):
    """指定ポートが使用可能かチェック"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0  # 0 = 接続成功（ポートが使用中）
    except Exception:
        sock.close()
        return False

def test_qmap_server(port):
    """QMapPermalinkサーバーかどうかテスト"""
    endpoints_to_test = ['/qgis-map', '/qgis-image', '/qgis-png']
    qmap_responses = {}
    
    for endpoint in endpoints_to_test:
        try:
            url = f"http://localhost:{port}{endpoint}"
            req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req, timeout=3) as response:
                content = response.read(100).decode('utf-8', errors='ignore')  # 最初の100文字のみ
                qmap_responses[endpoint] = {
                    'status': response.getcode(),
                    'content_type': response.headers.get('Content-Type', 'N/A'),
                    'is_qmap': 'QMap Permalink' in content or 'qgis' in content.lower()
                }
        except urllib.error.HTTPError as e:
            qmap_responses[endpoint] = {
                'status': e.code,
                'content_type': 'N/A',
                'is_qmap': False
            }
        except Exception:
            qmap_responses[endpoint] = {
                'status': 'timeout/error',
                'content_type': 'N/A', 
                'is_qmap': False
            }
    
    return qmap_responses

def diagnose_server_status():
    """サーバー状態の総合診断"""
    print("🔍 QMapPermalink HTTPサーバー診断")
    print("=" * 60)
    
    # ポート範囲スキャン
    print("📡 ポートスキャン (8089-8098)")
    print("-" * 30)
    
    active_ports = []
    qmap_servers = []
    
    for port in range(8089, 8099):
        if check_port_availability(port):
            active_ports.append(port)
            print(f"  🟢 ポート {port}: 使用中")
            
            # QMapサーバーかテスト
            qmap_responses = test_qmap_server(port)
            
            # QMapPermalinkサーバーかどうか判定
            qmap_indicators = 0
            for endpoint, response in qmap_responses.items():
                if response['is_qmap'] or response['status'] == 404:  # 404も正常なQMapレスポンス
                    qmap_indicators += 1
            
            if qmap_indicators >= 1:  # 1つでもQMapらしいレスポンスがあれば
                qmap_servers.append((port, qmap_responses))
                print(f"    ✅ QMapPermalinkサーバーと判定")
            else:
                print(f"    ❓ 他のHTTPサーバー")
                
        else:
            print(f"  ⚪ ポート {port}: 未使用")
    
    # QMapPermalinkサーバー詳細情報
    if qmap_servers:
        print(f"\n🎯 発見されたQMapPermalinkサーバー: {len(qmap_servers)}個")
        print("=" * 60)
        
        for port, responses in qmap_servers:
            print(f"\n📍 ポート {port} - QMapPermalinkサーバー")
            print("-" * 40)
            
            for endpoint, response in responses.items():
                status = response['status']
                content_type = response['content_type']
                is_qmap = "✅" if response['is_qmap'] else "❌"
                
                if status == 200:
                    print(f"  {endpoint:12} ✅ {status} ({content_type}) {is_qmap}")
                elif status == 404:
                    print(f"  {endpoint:12} 🚫 {status} (Not Found) - 期待される")
                else:
                    print(f"  {endpoint:12} ⚠️ {status} ({content_type})")
            
            # v1.9.7の改善点をチェック
            png_status = responses.get('/qgis-png', {}).get('status', 'unknown')
            if png_status == 404:
                print(f"  💡 v1.9.7改善: PNGエンドポイントが正常に削除されています")
            elif png_status == 200:
                print(f"  ⚠️ 旧版: PNGエンドポイントがまだ存在します（パフォーマンス問題の原因）")
    
    else:
        print(f"\n❌ QMapPermalinkサーバーが見つかりません")
        print("=" * 60)
        print("🔧 対処方法:")
        print("  1. QGISを起動")
        print("  2. プラグインメニューからQMapPermalinkを有効化")
        print("  3. QMapPermalinkパネルでHTTPサーバーを起動")
        print("  4. 最新版 v1.9.7 プラグインを使用（PNG問題修正版）")
    
    # サーバー使用状況サマリー
    print(f"\n📊 ポート使用状況サマリー")
    print("=" * 60)
    print(f"🔍 スキャン範囲: 8089-8098 (10ポート)")
    print(f"🟢 使用中: {len(active_ports)}ポート")
    print(f"🎯 QMapPermalink: {len(qmap_servers)}サーバー")
    print(f"⚪ 利用可能: {10 - len(active_ports)}ポート")
    
    if active_ports:
        print(f"🟢 使用中ポート: {', '.join(map(str, active_ports))}")
    
    # 推奨アクション
    print(f"\n💡 推奨アクション")
    print("=" * 60)
    
    if qmap_servers:
        # 最初のQMapサーバーを使用
        recommended_port = qmap_servers[0][0]
        print(f"✅ QMapPermalinkサーバー発見: ポート {recommended_port}")
        print("🌐 ブラウザでテスト:")
        print(f"  - OpenLayersマップ: http://localhost:{recommended_port}/qgis-map?lat=35.681236&lon=139.767125&z=16")
        print(f"  - QGIS実画像:     http://localhost:{recommended_port}/qgis-image?lat=35.681236&lon=139.767125&z=16")
        
        # v1.9.7かどうかチェック  
        png_removed = qmap_servers[0][1].get('/qgis-png', {}).get('status') == 404
        if png_removed:
            print(f"🎉 v1.9.7以降: PNG削除済み（パフォーマンス改善版）")
        else:
            print(f"⚠️ 旧版検出: v1.9.7への更新を推奨（PNG問題修正）")
    else:
        print("🚀 QGISでQMapPermalinkプラグインを起動してください")
        print("📦 最新版プラグイン: c:\\github\\QMapPermalink\\dist\\qmap_permalink_1.9.7.zip")

if __name__ == "__main__":
    diagnose_server_status()