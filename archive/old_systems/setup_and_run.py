"""
Smart Surveillance System - Quick Setup and Run Script
Run this to automatically set up and launch the surveillance system
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
import json

def install_package(package):
    """Install a Python package"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        return True
    except subprocess.CalledProcessError:
        return False

def check_and_install_requirements():
    """Check and install required packages"""
    required_packages = {
        'opencv-python': 'OpenCV for computer vision',
        'ultralytics': 'YOLOv8 for object detection',
        'fer': 'Facial Expression Recognition',
        'Pillow': 'Image processing',
        'numpy': 'Numerical computing',
        'psutil': 'System monitoring'
    }
    
    print("🔍 Checking required packages...")
    missing_packages = []
    
    for package, description in required_packages.items():
        try:
            if package == 'opencv-python':
                import cv2
            elif package == 'ultralytics':
                import ultralytics
            elif package == 'fer':
                import fer
            elif package == 'Pillow':
                from PIL import Image
            elif package == 'numpy':
                import numpy
            elif package == 'psutil':
                import psutil
            
            print(f"✅ {description}: Available")
            
        except ImportError:
            print(f"❌ {description}: Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        
        for package in missing_packages:
            print(f"Installing {package}...")
            if install_package(package):
                print(f"✅ {package} installed successfully")
            else:
                print(f"❌ Failed to install {package}")
                return False
    
    print("✅ All required packages are available!")
    return True

def check_model_files():
    """Check if model files exist"""
    model_files = {
        'Object_detection/best.pt': 'Custom object detection model',
        'crowddetection/yolov8s.pt': 'Crowd detection model',
        'crowddetection/yolov8n.pt': 'General object detection model'
    }
    
    print("\n🤖 Checking AI model files...")
    missing_models = []
    
    for model_path, description in model_files.items():
        if os.path.exists(model_path):
            print(f"✅ {description}: Found")
        else:
            print(f"⚠️ {description}: Missing ({model_path})")
            missing_models.append(model_path)
    
    if missing_models:
        print(f"\n⚠️ Missing model files: {len(missing_models)}")
        print("Some AI features may not work until models are added.")
        print("The system will still run with available models.")
    else:
        print("✅ All model files found!")
    
    return missing_models

def create_default_config():
    """Create default configuration if needed"""
    try:
        # Check if config files exist and are importable
        from config_advanced import EMAIL_CONFIG, MODELS
        print("✅ Configuration files loaded successfully")
        return True
    except ImportError as e:
        print(f"⚠️ Configuration issue: {e}")
        return False

def setup_environment():
    """Set up environment variables"""
    env_vars = {
        'SENDER_EMAIL': 'your_email@gmail.com',
        'SENDER_PASSWORD': 'your_app_password', 
        'RECIPIENT_EMAILS': 'alert_recipient@gmail.com',
        'EMAIL_ENABLED': 'False'
    }
    
    print("\n⚙️ Environment setup:")
    for var, default in env_vars.items():
        if var not in os.environ:
            os.environ[var] = default
            print(f"Set {var} to default value")
        else:
            print(f"✅ {var} already configured")

def show_setup_summary():
    """Show setup summary and instructions"""
    print("\n" + "="*60)
    print("🛡️ SMART SURVEILLANCE SYSTEM - SETUP COMPLETE")
    print("="*60)
    
    print("\n📋 SYSTEM STATUS:")
    print("✅ Required packages installed")
    print("✅ Configuration files loaded")
    print("✅ Environment variables set")
    
    missing_models = check_model_files()
    if missing_models:
        print(f"⚠️ {len(missing_models)} AI model files missing")
    else:
        print("✅ All AI model files found")
    
    print("\n🚀 HOW TO RUN THE SYSTEM:")
    print("1. Basic GUI:           python basic_surveillance_gui.py")
    print("2. Advanced GUI:        python main_surveillance_app.py")
    print("3. Console Mode:        python integration.py")
    
    print("\n📧 EMAIL ALERT SETUP:")
    print("1. Open the main application")
    print("2. Click 'Configure Email' button")
    print("3. Enter your Gmail credentials:")
    print("   - Use Gmail App Password (not regular password)")
    print("   - Enable 2-Factor Authentication first")
    print("4. Test email configuration")
    
    print("\n📹 CAMERA SETUP:")
    print("- Webcam: Use '0' (or 1, 2 for additional cameras)")
    print("- IP Camera: Use full URL like 'http://192.168.1.100:8080/video'")
    print("- IP Phone: Use IP address like '192.168.1.100'")
    
    print("\n🔧 TROUBLESHOOTING:")
    print("- Check logs in the 'logs' folder")
    print("- Verify camera permissions in Windows settings")
    print("- Ensure models are in correct directories")
    print("- Check internet connection for email alerts")
    
    print("\n" + "="*60)

def launch_application():
    """Launch the surveillance application"""
    print("\n🚀 Which version would you like to run?")
    print("1. Basic GUI (Recommended for first-time users)")
    print("2. Advanced GUI (Full-featured)")
    print("3. Console Mode (No GUI)")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                print("🚀 Starting Basic GUI...")
                os.system(f'{sys.executable} basic_surveillance_gui.py')
                break
            elif choice == '2':  
                print("🚀 Starting Advanced GUI...")
                os.system(f'{sys.executable} main_surveillance_app.py')
                break
            elif choice == '3':
                print("🚀 Starting Console Mode...")
                os.system(f'{sys.executable} integration.py')
                break
            elif choice == '4':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-4.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

def main():
    """Main setup function"""
    print("🛡️ Smart Surveillance System - Automated Setup")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"❌ Python {sys.version_info.major}.{sys.version_info.minor} detected")
        print("Python 3.8 or higher is required!")
        input("Press Enter to exit...")
        return
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Step 1: Install requirements
    if not check_and_install_requirements():
        print("❌ Failed to install required packages")
        input("Press Enter to exit...")
        return
    
    # Step 2: Check model files
    check_model_files()
    
    # Step 3: Setup configuration
    if not create_default_config():
        print("❌ Configuration setup failed")
        input("Press Enter to exit...")
        return
    
    # Step 4: Setup environment
    setup_environment()
    
    # Step 5: Show summary
    show_setup_summary()
    
    # Step 6: Launch application
    launch_choice = input("\nWould you like to launch the application now? (y/n): ").lower()
    if launch_choice == 'y':
        launch_application()
    else:
        print("\n✅ Setup complete! You can run the system anytime using the commands shown above.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        input("Press Enter to exit...")