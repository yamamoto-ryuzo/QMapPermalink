import sys
import urllib.request
import urllib.parse

def test_wms_server():
    """WMSサーバーの基本的なテスト"""
    
    base_url = "http://localhost:8089/wms"
    
    print("🧪 WMS Server Test")
    print("=" * 50)
    
    # Test 1: GetCapabilities
    print("\n1. Testing GetCapabilities...")
    capabilities_url = f"{base_url}?SERVICE=WMS&REQUEST=GetCapabilities"
    
    try:
        with urllib.request.urlopen(capabilities_url, timeout=10) as response:
            status = response.getcode()
            content_type = response.getheader('Content-Type')
            content_length = response.getheader('Content-Length')
            data = response.read().decode('utf-8')
            
            print(f"   Status: {status}")
            print(f"   Content-Type: {content_type}")
            print(f"   Content-Length: {content_length}")
            print(f"   Response preview: {data[:200]}...")
            
            if "WMS_Capabilities" in data:
                print("   ✅ GetCapabilities SUCCESS")
            else:
                print("   ❌ GetCapabilities FAILED - Not valid WMS XML")
                
    except Exception as e:
        print(f"   ❌ GetCapabilities ERROR: {e}")
    
    # Test 2: GetMap
    print("\n2. Testing GetMap...")
    getmap_params = {
        'SERVICE': 'WMS',
        'REQUEST': 'GetMap',
        'FORMAT': 'image/png',
        'WIDTH': '256',
        'HEIGHT': '256',
        'LAYERS': 'map',
        'CRS': 'EPSG:3857',
        'BBOX': '-20037508,-20037508,20037508,20037508'
    }
    
    getmap_url = f"{base_url}?" + urllib.parse.urlencode(getmap_params)
    
    try:
        with urllib.request.urlopen(getmap_url, timeout=10) as response:
            status = response.getcode()
            content_type = response.getheader('Content-Type')
            content_length = response.getheader('Content-Length')
            data = response.read()
            
            print(f"   Status: {status}")
            print(f"   Content-Type: {content_type}")
            print(f"   Content-Length: {content_length}")
            print(f"   Data size: {len(data)} bytes")
            
            # PNG signature check
            png_signature = b'\x89PNG\r\n\x1a\n'
            if data.startswith(png_signature):
                print("   ✅ GetMap SUCCESS - Valid PNG image")
                
                # Test for actual vs placeholder image
                if len(data) > 1000:  # Real images are usually larger
                    print("   ✅ Appears to be REAL image (size > 1KB)")
                else:
                    print("   ⚠️  Appears to be PLACEHOLDER image (size < 1KB)")
            else:
                print("   ❌ GetMap FAILED - Not a PNG image")
                print(f"   Response preview: {data[:100]}")
                
    except Exception as e:
        print(f"   ❌ GetMap ERROR: {e}")

    # Test 3: Invalid request
    print("\n3. Testing invalid request...")
    invalid_url = f"{base_url}?SERVICE=WMS&REQUEST=InvalidRequest"
    
    try:
        with urllib.request.urlopen(invalid_url, timeout=10) as response:
            status = response.getcode()
            content_type = response.getheader('Content-Type')
            data = response.read().decode('utf-8')
            
            print(f"   Status: {status}")
            print(f"   Content-Type: {content_type}")
            
            if "ServiceExceptionReport" in data:
                print("   ✅ Error handling SUCCESS - Proper WMS exception")
            else:
                print("   ⚠️  Error handling PARTIAL - Not standard WMS exception")
                
    except urllib.error.HTTPError as e:
        print(f"   ✅ Error handling SUCCESS - HTTP error {e.code}")
    except Exception as e:
        print(f"   ❌ Error handling ERROR: {e}")

    print("\n" + "=" * 50)
    print("🏁 Test completed")

if __name__ == "__main__":
    test_wms_server()