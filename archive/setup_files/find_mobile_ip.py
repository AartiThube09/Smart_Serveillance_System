#!/usr/bin/env python3
"""
📱 IP Webcam Helper - Find Your Mobile IP Address
Helps you identify the correct IP for your mobile camera
"""

import socket

def get_local_ip():
    """Get this computer's IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "Unable to determine"

def scan_network_for_cameras():
    """Scan local network for potential IP webcam devices"""
    local_ip = get_local_ip()
    if local_ip == "Unable to determine":
        return []
    
    # Get network range (assume /24 subnet)
    ip_parts = local_ip.split('.')
    network_base = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
    
    print(f"Scanning network {network_base}.x for IP webcam servers...")
    
    potential_cameras = []
    
    # Common IP webcam ports
    common_ports = [8080, 8081, 4747, 8000]
    
    # Scan last 50 IPs in the range (most common for DHCP)
    for i in range(100, 150):
        test_ip = f"{network_base}.{i}"
        
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((test_ip, port))
                sock.close()
                
                if result == 0:
                    potential_cameras.append(f"http://{test_ip}:{port}/video")
                    print(f"✅ Found potential camera at {test_ip}:{port}")
                    
            except Exception:
                continue
    
    return potential_cameras

def show_ip_instructions():
    """Show detailed instructions for finding mobile IP"""
    local_ip = get_local_ip()
    
    print("="*60)
    print("📱 HOW TO FIND YOUR MOBILE IP WEBCAM ADDRESS")
    print("="*60)
    print()
    print("METHOD 1: Check IP Webcam App")
    print("-" * 30)
    print("1. Open 'IP Webcam' app on your Android phone")
    print("2. Scroll down and tap 'Start server'")
    print("3. Look at the bottom of the screen")
    print("4. You'll see something like: 'Access your camera at: http://192.168.0.107:8080'")
    print("5. Use this EXACT address in the surveillance system")
    print()
    
    print("METHOD 2: Check WiFi Settings")
    print("-" * 30)
    print("1. Go to WiFi settings on your phone")
    print("2. Tap on the connected WiFi network")
    print("3. Look for 'IP address' - usually starts with 192.168")
    print("4. Add ':8080/video' to the end")
    print("   Example: if IP is 192.168.1.105, use http://192.168.1.105:8080/video")
    print()
    
    print("METHOD 3: Common IP Patterns")
    print("-" * 30)
    print(f"Your laptop IP: {local_ip}")
    if local_ip.startswith("192.168.0"):
        print("Try these common mobile IPs:")
        print("  - http://192.168.0.105:8080/video")
        print("  - http://192.168.0.106:8080/video") 
        print("  - http://192.168.0.107:8080/video")
        print("  - http://192.168.0.108:8080/video")
    elif local_ip.startswith("192.168.1"):
        print("Try these common mobile IPs:")
        print("  - http://192.168.1.105:8080/video")
        print("  - http://192.168.1.106:8080/video")
        print("  - http://192.168.1.107:8080/video")
        print("  - http://192.168.1.108:8080/video")
    else:
        network = '.'.join(local_ip.split('.')[:-1])
        print(f"Try these IPs in your network ({network}.x):")
        for i in [105, 106, 107, 108, 109, 110]:
            print(f"  - http://{network}.{i}:8080/video")
    print()
    
    print("TROUBLESHOOTING TIPS")
    print("-" * 30)
    print("❌ If connection fails:")
    print("  1. Make sure both devices are on the SAME WiFi network")
    print("  2. Check if your phone's firewall is blocking connections")
    print("  3. Try restarting the IP Webcam app")
    print("  4. Try using mobile hotspot from phone, connect laptop to it")
    print("  5. Some routers block device-to-device communication")
    print()
    
    print("✅ Test your IP:")
    print("  Open your browser and go to: http://YOUR_PHONE_IP:8080")
    print("  You should see the IP Webcam interface")
    print("="*60)

def main():
    """Main function"""
    print("📱 IP Webcam Helper Tool")
    print("=" * 30)
    
    local_ip = get_local_ip()
    print(f"Your laptop IP address: {local_ip}")
    print()
    
    choice = input("What would you like to do?\n1. Show IP finding instructions\n2. Scan network for cameras\n3. Test an IP address\n\nChoice (1-3): ").strip()
    
    if choice == "1":
        show_ip_instructions()
        
    elif choice == "2":
        print("Scanning network for IP webcam servers...")
        cameras = scan_network_for_cameras()
        
        if cameras:
            print(f"\n✅ Found {len(cameras)} potential camera(s):")
            for camera in cameras:
                print(f"  - {camera}")
            print("\nTry these URLs in your surveillance system!")
        else:
            print("\n❌ No IP webcam servers found on the network")
            print("Make sure:")
            print("  1. IP Webcam app is running on your phone")
            print("  2. Both devices are on the same WiFi network")
            
    elif choice == "3":
        test_ip = input("Enter IP address to test (e.g., 192.168.0.107): ").strip()
        if test_ip:
            test_url = f"http://{test_ip}:8080/video"
            print(f"Testing: {test_url}")
            
            try:
                import urllib.request
                urllib.request.urlopen(test_url, timeout=5)
                print("✅ IP webcam server is responding!")
                print(f"Use this URL: {test_url}")
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                print("Check if:")
                print("  1. IP Webcam app is running")
                print("  2. IP address is correct")
                print("  3. Both devices on same WiFi")
    
    else:
        show_ip_instructions()
    
    print("\n🚀 Now run your surveillance system with:")
    print("python mobile_ip_webcam_gui.py")

if __name__ == "__main__":
    main()