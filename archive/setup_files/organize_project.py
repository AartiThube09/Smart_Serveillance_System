#!/usr/bin/env python3
"""
📁 Project Structure Organizer
Moves backup and non-essential files to organized folders
"""

import os
import shutil
from pathlib import Path

def organize_project():
    """Organize project files into clean structure"""
    
    print("🧹 Organizing Smart Surveillance System Project...")
    
    # Define file movements
    file_moves = {
        # Alternative GUI files
        "backup_files/alternative_guis/": [
            "basic_surveillance_gui.py",
            "simple_surveillance_gui.py", 
            "surveillance_gui.py",
            "main_surveillance_app.py"
        ],
        
        # Modular system files
        "backup_files/modular_system/": [
            "config_advanced.py",
            "detection_engine.py",
            "alert_manager.py", 
            "video_capture.py",
            "start_here.py"
        ],
        
        # Legacy/old files
        "backup_files/legacy_files/": [
            "integration.py",
            "camera.py",
            "mobile_surveillance_system.py",
            "efficientdet-d0_240.tlt"
        ],
        
        # Documentation
        "docs/": [
            "README_PRODUCTION.md",
            "MOBILE_WEBCAM_GUIDE.md"
        ],
        
        # Test data
        "backup_files/test_data/": [
            "facialexpression/faceimg.jpg"
        ]
    }
    
    # Move files
    moved_count = 0
    for destination, files in file_moves.items():
        for file_path in files:
            if os.path.exists(file_path):
                try:
                    # Create parent directories if needed
                    dest_path = Path(destination) / Path(file_path).name
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Move file
                    shutil.move(file_path, str(dest_path))
                    print(f"✅ Moved: {file_path} → {dest_path}")
                    moved_count += 1
                except Exception as e:
                    print(f"❌ Failed to move {file_path}: {e}")
    
    # Move entire directories
    dir_moves = {
        "backup_files/legacy_projects/": [
            "smart-surv-system",
            "violence_detection_project"
        ]
    }
    
    for destination, dirs in dir_moves.items():
        for dir_path in dirs:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                try:
                    dest_path = Path(destination) / dir_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(dir_path, str(dest_path))
                    print(f"✅ Moved directory: {dir_path} → {dest_path}")
                    moved_count += 1
                except Exception as e:
                    print(f"❌ Failed to move directory {dir_path}: {e}")
    
    print(f"\n🎯 Organization complete! Moved {moved_count} items")
    
def create_project_readme():
    """Create a clean project README"""
    readme_content = """# 🛡️ Smart Surveillance System

A real-time AI-powered surveillance system with mobile IP webcam integration.

## 🚀 Quick Start

### Run the System
```bash
python mobile_ip_webcam_gui.py
```

### Find Mobile IP (if needed)
```bash
python find_mobile_ip.py
```

### Setup Helper
```bash
python setup_mobile_surveillance.py
```

## 📱 Mobile Setup

1. Install "IP Webcam" app on Android
2. Start server in the app
3. Note the IP address (e.g., 192.168.0.107:8080)
4. Enter IP in the surveillance system

## 🤖 AI Detection Features

- **Weapon Detection**: Custom-trained model
- **People Counting**: Crowd density monitoring
- **Facial Expression**: Emotion analysis
- **Real-time Alerts**: Visual and audio notifications

## 📁 Project Structure

```
Smart_Servellance_System/
├── mobile_ip_webcam_gui.py     # Main application
├── find_mobile_ip.py           # IP helper tool
├── setup_mobile_surveillance.py # Setup script
├── requirements.txt            # Dependencies
├── Object_detection/           # Weapon detection model
├── crowddetection/            # People detection model
├── facialexpression/          # Emotion detection
├── violence/                  # Violence detection
├── docs/                      # Documentation
└── backup_files/              # Alternative versions
```

## 📋 Requirements

- Python 3.8+
- OpenCV
- Ultralytics YOLO
- FER (Facial Expression Recognition)
- Tkinter (GUI)

## 🎯 System Features

✅ Mobile IP webcam integration  
✅ Multi-model AI detection  
✅ Real-time threat alerts  
✅ Professional GUI interface  
✅ Alert history and logging  
✅ Automatic camera fallback  

## 📖 Documentation

- Complete setup guide: `docs/MOBILE_WEBCAM_GUIDE.md`
- Production manual: `docs/README_PRODUCTION.md`
- Alternative versions: `backup_files/`

---
**Smart Surveillance System** - Advanced AI-powered security monitoring
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    print("✅ Created clean project README.md")

def show_final_structure():
    """Show the clean project structure"""
    print("\n" + "="*60)
    print("📁 CLEAN PROJECT STRUCTURE (What examiner will see)")
    print("="*60)
    
    structure = """
Smart_Servellance_System/
├── 📄 README.md                        # Clean project overview
├── 🚀 mobile_ip_webcam_gui.py         # Main application
├── 🔍 find_mobile_ip.py               # IP helper tool  
├── ⚙️ setup_mobile_surveillance.py    # Setup script
├── 📋 requirements.txt                # Dependencies
├── 🚫 .gitignore                      # Git ignore rules
│
├── 🤖 Object_detection/               # AI Models
│   ├── best.pt                       # Weapon detection model
│   └── objectdetection.py            # Reference code
│
├── 👥 crowddetection/                 # People Detection
│   ├── yolov8s.pt                   # Main model
│   ├── yolov8n.pt                   # Backup model
│   └── crowddetection.py            # Reference code
│
├── 😊 facialexpression/               # Emotion Detection
│   └── expression.py                 # Reference code
│
├── 🥊 violence/                       # Violence Detection
│   ├── label_map.txt                 # Model labels
│   └── violence.py                   # Reference code
│
├── 📚 docs/                           # Documentation
│   ├── MOBILE_WEBCAM_GUIDE.md        # Setup guide
│   └── README_PRODUCTION.md          # Full manual
│
└── 📦 backup_files/                   # Organized backups
    ├── alternative_guis/             # Other GUI versions
    ├── modular_system/               # Modular components
    ├── legacy_files/                 # Old files
    ├── legacy_projects/              # Old projects
    └── test_data/                    # Test files
"""
    
    print(structure)
    print("="*60)
    
    print("\n🎯 EXAMINER WILL SEE:")
    print("✅ Clean, professional project structure")
    print("✅ Main application clearly identified")
    print("✅ AI models properly organized")
    print("✅ Clear documentation")
    print("✅ Backup files hidden but available")
    
    print("\n📋 TO DEMONSTRATE:")
    print("1. Show README.md for project overview")
    print("2. Run: python mobile_ip_webcam_gui.py")
    print("3. Explain AI models in organized folders")
    print("4. Mention backup_files/ contains alternatives")

def main():
    """Main organization function"""
    print("🛡️ Smart Surveillance System - Project Organizer")
    print("=" * 50)
    
    # Confirm before organizing
    response = input("Organize project structure? This will move files around. (y/n): ")
    
    if response.lower().startswith('y'):
        organize_project()
        create_project_readme()
        show_final_structure()
        
        print("\n🎉 SUCCESS! Your project is now professionally organized!")
        print("📁 Backup files are in: backup_files/")
        print("📚 Documentation is in: docs/")
        print("🚀 Main app: mobile_ip_webcam_gui.py")
        
    else:
        print("Organization cancelled. No files were moved.")

if __name__ == "__main__":
    main()