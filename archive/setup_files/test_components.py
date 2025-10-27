"""
Simple test script to verify GUI components work
"""

import tkinter as tk
from tkinter import messagebox
import sys

def test_basic_gui():
    """Test basic tkinter functionality"""
    try:
        root = tk.Tk()
        root.title("GUI Test")
        root.geometry("400x300")
        
        label = tk.Label(root, text="✅ GUI Test Successful!", 
                        font=('Arial', 16), fg='green')
        label.pack(pady=50)
        
        def show_message():
            messagebox.showinfo("Test", "GUI components working!")
        
        button = tk.Button(root, text="Test Button", command=show_message,
                          bg='lightblue', font=('Arial', 12))
        button.pack(pady=20)
        
        close_button = tk.Button(root, text="Close", command=root.quit,
                               bg='lightcoral', font=('Arial', 12))
        close_button.pack(pady=10)
        
        print("✅ Basic GUI test window created")
        print("Close the window to continue...")
        
        root.mainloop()
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        return False

def test_opencv():
    """Test OpenCV import"""
    try:
        import cv2
        print(f"✅ OpenCV version: {cv2.__version__}")
        return True
    except ImportError:
        print("❌ OpenCV not available")
        return False

def test_other_packages():
    """Test other required packages"""
    packages = {
        'PIL': 'Pillow',
        'ultralytics': 'YOLO',
        'fer': 'Facial Expression Recognition'
    }
    
    results = {}
    for package, name in packages.items():
        try:
            if package == 'PIL':
                from PIL import Image
            elif package == 'ultralytics':
                from ultralytics import YOLO
            elif package == 'fer':
                from fer import FER
            
            print(f"✅ {name} available")
            results[package] = True
        except ImportError:
            print(f"❌ {name} not available")
            results[package] = False
    
    return results

def main():
    print("🧪 Smart Surveillance System - Component Test")
    print("=" * 50)
    
    # Test Python version
    if sys.version_info < (3, 8):
        print(f"❌ Python {sys.version_info.major}.{sys.version_info.minor} detected")
        print("Python 3.8 or higher required")
        return
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} OK")
    
    # Test packages
    opencv_ok = test_opencv()
    package_results = test_other_packages()
    
    print("\n" + "=" * 50)
    print("COMPONENT TEST SUMMARY:")
    print("=" * 50)
    
    if opencv_ok:
        print("✅ OpenCV: Ready")
    else:
        print("❌ OpenCV: Missing")
    
    for package, status in package_results.items():
        status_text = "Ready" if status else "Missing"
        icon = "✅" if status else "❌"
        print(f"{icon} {package}: {status_text}")
    
    # Test GUI
    print("\n📱 Testing GUI components...")
    gui_ok = test_basic_gui()
    
    print("\n" + "=" * 50)
    print("FINAL RESULTS:")
    print("=" * 50)
    
    all_ready = opencv_ok and all(package_results.values()) and gui_ok
    
    if all_ready:
        print("🎉 ALL COMPONENTS READY!")
        print("You can now run the Smart Surveillance System")
        print("\nTo start:")
        print("1. Run: python surveillance_gui.py")
        print("2. Or use: python launcher.py")
    else:
        print("⚠️ SOME COMPONENTS MISSING")
        print("Please install missing packages:")
        print("pip install -r requirements_gui.txt")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()