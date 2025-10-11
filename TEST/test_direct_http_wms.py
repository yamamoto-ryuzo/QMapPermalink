#!/usr/bin/env python3
"""
シンプルなHTTPクライアントでWMSエンドポイントテスト
"""

import socket
import time

def send_http_request(host, port, request_path):
    """HTTPリクエストをソケット経由で送信"""
    try:
        # ソケット接続
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect((host, port))
        
        # HTTPリクエストを作成
        http_request = f"GET {request_path} HTTP/1.1\r\n"
        http_request += f"Host: {host}:{port}\r\n"
        http_request += "Connection: close\r\n"
        http_request += "\r\n"
        
        print(f"📡 Sending request: {request_path}")
        
        # リクエスト送信
        sock.sendall(http_request.encode('utf-8'))
        
        # レスポンス受信
        response_data = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk
        
        sock.close()
        
        # レスポンスを解析
        if b"\r\n\r\n" in response_data:
            header_part, body_part = response_data.split(b"\r\n\r\n", 1)
            header_text = header_part.decode('utf-8', errors='ignore')
            
            print(f"📄 Response headers:")
            for line in header_text.split('\r\n')[:5]:  # 最初の5行のみ表示
                print(f"   {line}")
            
            print(f"📊 Body size: {len(body_part)} bytes")
            
            # ステータスコードを確認
            status_line = header_text.split('\r\n')[0]
            if '200 OK' in status_line:
                print("✅ Request successful")
                if body_part and len(body_part) > 1000:
                    print("✅ Response has substantial content")
                    return True, body_part
                else:
                    print("⚠️ Response body is too small")
                    return False, body_part
            else:
                print(f"❌ Request failed: {status_line}")
                print(f"📄 Error body preview: {body_part[:200]}")
                return False, body_part
        else:
            print("❌ Invalid HTTP response")
            return False, b""
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False, b""

def test_wms_endpoints():
    """WMSエンドポイントをテスト"""
    host = "localhost"
    port = 8089
    
    print("🚀 WMSエンドポイント直接テスト")
    
    # 1. 標準WMSリクエスト
    print("\n1️⃣ 標準WMSリクエストテスト")
    wms_path = "/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=test&STYLES=&CRS=EPSG:3857&BBOX=15559350,4273995,15561350,4275995&WIDTH=512&HEIGHT=512&FORMAT=image/png"
    success, body = send_http_request(host, port, wms_path)
    if success:
        print("✅ 標準WMSリクエスト成功")
    
    time.sleep(1)  # サーバーへの負荷軽減
    
    # 2. パーマリンクパラメータリクエスト
    print("\n2️⃣ パーマリンクパラメータリクエストテスト")
    permalink_path = "/wms?x=15560350.158668&y=4274995.922363&scale=21280.2&crs=EPSG:3857&rotation=0.00&width=512&height=512"
    success, body = send_http_request(host, port, permalink_path)
    if success:
        print("✅ パーマリンクパラメータリクエスト成功")
        # 結果をファイルに保存
        with open("permalink_wms_result.png", "wb") as f:
            f.write(body)
        print("💾 結果を permalink_wms_result.png に保存しました")
    else:
        print("❌ パーマリンクパラメータリクエスト失敗")
    
    time.sleep(1)
    
    # 3. 最小パーマリンクパラメータ
    print("\n3️⃣ 最小パーマリンクパラメータテスト")
    minimal_path = "/wms?x=15560350&y=4274995&scale=20000"
    success, body = send_http_request(host, port, minimal_path)
    if success:
        print("✅ 最小パーマリンクパラメータリクエスト成功")
    else:
        print("❌ 最小パーマリンクパラメータリクエスト失敗")

if __name__ == "__main__":
    try:
        test_wms_endpoints()
    except KeyboardInterrupt:
        print("\n⏹️ テスト中断")
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()