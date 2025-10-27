#!/usr/bin/env python3
"""
🚀 Mobile IP Webcam Setup Script
Quick setup and launch for mobile surveillance system
"""

import os
import sys
import subprocess
import socket

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'opencv-python',
        'ultralytics', 
        'fer',
        'Pillow'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'opencv-python':
                import cv2
            elif package == 'ultralytics':
                from ultralytics import YOLO
            elif package == 'fer':
                from fer import FER
            elif package == 'Pillow':
                from PIL import Image
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_packages(packages):
    """Install missing packages"""
    if not packages:
        return True
    
    print(f"Installing missing packages: {', '.join(packages)}")
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    
    return True

def check_models():
    """Check if AI model files exist"""
    model_files = [
        "Object_detection/best.pt",
        "crowddetection/yolov8s.pt"
    ]
    
    missing_models = []
    existing_models = []
    
    for model in model_files:
        if os.path.exists(model):
            existing_models.append(model)
            print(f"✅ Found: {model}")
        else:
            missing_models.append(model)
            print(f"❌ Missing: {model}")
    
    return existing_models, missing_models

def get_local_ip():
    """Get local IP address"""
    try:
        # Connect to a remote server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "Unable to determine"

def setup_ip_webcam_instructions():
    """Show IP webcam setup instructions"""
    local_ip = get_local_ip()
    
    print("\n" + "="*60)
    print("📱 MOBILE IP WEBCAM SETUP INSTRUCTIONS")
    print("="*60)
    print("1. Install 'IP Webcam' app on your Android phone")
    print("2. Open the app and scroll down to 'Start server'")
    print("3. Note the IP address shown (something like 192.168.x.x:8080)")
    print("4. Make sure your phone and laptop are on the same WiFi network")
    print(f"5. Your laptop's IP address is: {local_ip}")
    print("\n🔧 COMMON IP WEBCAM URLS:")
    print("   http://192.168.0.107:8080/video")
    print("   http://192.168.1.100:8080/video") 
    print("   http://10.0.0.5:8080/video")
    print("\n⚠️ TROUBLESHOOTING:")
    print("   - Make sure both devices are on same WiFi")
    print("   - Check if phone's firewall allows connections")
    print("   - Try different IP addresses in your network range")
    print("   - If it fails, the system will use laptop camera as backup")
    print("="*60)

def main():
    """Main setup function"""
    print("🛡️ Mobile IP Webcam Surveillance System - Setup")
    print("="*50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Check required packages
    print("\n📦 Checking required packages...")
    missing = check_requirements()
    
    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        install = input("Install missing packages? (y/n): ").lower().startswith('y')
        
        if install:
            if not install_packages(missing):
                print("❌ Package installation failed")
                return
        else:
            print("⚠️ Some features may not work without required packages")
    else:
        print("✅ All required packages are installed")
    
    # Check AI models
    print("\n🤖 Checking AI model files...")
    existing, missing_models = check_models()
    
    if missing_models:
        print(f"\n⚠️ Missing model files: {', '.join(missing_models)}")
        print("The system will work with available models only.")
        print("To get full functionality, ensure all model files are in place.")
    
    # Show IP webcam setup instructions
    setup_ip_webcam_instructions()
    
    # Ask which version to run
    print("\n🚀 CHOOSE INTERFACE:")
    print("1. GUI Version (Recommended) - User-friendly interface")
    print("2. Console Version - Terminal-based")
    print("3. Basic GUI - Simple interface (if main GUI has issues)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    try:
        if choice == "1":
            print("\n🚀 Starting Mobile IP Webcam GUI...")
            import mobile_ip_webcam_gui
            mobile_ip_webcam_gui.main()
            
        elif choice == "2":
            print("\n🚀 Starting Console Version...")
            import mobile_surveillance_system
            mobile_surveillance_system.main()
            
        elif choice == "3":
            print("\n🚀 Starting Basic GUI...")
            import basic_surveillance_gui
            # Run basic GUI with modifications for IP webcam
            print("Starting basic surveillance with IP webcam support...")
            os.system("python basic_surveillance_gui.py")
            
        else:
            print("Invalid choice. Starting GUI version...")
            import mobile_ip_webcam_gui
            mobile_ip_webcam_gui.main()
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all files are in the correct directory")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("Try running the basic GUI or console version")

if __name__ == "__main__":
    main()