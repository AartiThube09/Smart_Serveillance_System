"""
Smart Surveillance System Launcher
Simple script to launch the surveillance system
"""

import sys
import subprocess
import os

def check_requirements():
    """Check if required packages are installed"""
    required_packages = ['cv2', 'tkinter', 'PIL', 'fer', 'ultralytics']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'tkinter':
                import tkinter
            elif package == 'PIL':
                from PIL import Image
            elif package == 'fer':
                from fer import FER
            elif package == 'ultralytics':
                from ultralytics import YOLO
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_requirements():
    """Install missing requirements"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements_gui.txt'])
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages. Please install manually.")
        return False

def main():
    print("🛡️ Smart Surveillance System Launcher")
    print("=" * 50)
    
    # Check if requirements file exists
    if not os.path.exists('requirements_gui.txt'):
        print("❌ requirements_gui.txt not found!")
        print("Please make sure you're running this from the project directory.")
        return
    
    # Check requirements
    missing = check_requirements()
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        choice = input("Would you like to install them automatically? (y/n): ")
        if choice.lower() == 'y':
            if not install_requirements():
                return
        else:
            print("Please install the missing packages manually:")
            print(f"pip install -r requirements_gui.txt")
            return
    
    # Check model files
    model_files = [
        'Object_detection/best.pt',
        'crowddetection/yolov8s.pt'
    ]
    
    missing_models = []
    for model_file in model_files:
        if not os.path.exists(model_file):
            missing_models.append(model_file)
    
    if missing_models:
        print("⚠️  Missing model files:")
        for model in missing_models:
            print(f"   - {model}")
        print("The system will run but some features may not work.")
        input("Press Enter to continue anyway...")
    
    # Launch options
    print("\nSelect launch mode:")
    print("1. GUI Mode (Recommended)")
    print("2. Integrated Mode (GUI with console fallback)")
    print("3. Console Mode Only")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-4): ")
            
            if choice == '1':
                print("Starting GUI mode...")
                os.system(f'{sys.executable} surveillance_gui.py')
                break
            elif choice == '2':
                print("Starting integrated mode...")
                os.system(f'{sys.executable} integrated_surveillance.py')
                break
            elif choice == '3':
                print("Starting console mode...")
                os.system(f'{sys.executable} integration.py')
                break
            elif choice == '4':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 1-4.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()