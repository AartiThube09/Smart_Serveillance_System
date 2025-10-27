#!/usr/bin/env python3
"""
🗂️ Smart Surveillance System - File Organizer
Organizes all files into clean directory structure
"""

import os
import shutil
from pathlib import Path
import json

def organize_surveillance_project():
    """Organize the surveillance project files"""
    
    print("🗂️ ORGANIZING SMART SURVEILLANCE SYSTEM FILES")
    print("=" * 60)
    
    # Create organized directory structure
    directories = {
        "archive/": "Old versions and backup files",
        "archive/old_systems/": "Previous system versions", 
        "archive/documentation/": "Old documentation files",
        "archive/setup_files/": "Setup and configuration helpers",
        "archive/database_files/": "Database and data files",
        "configs/": "Configuration files",
        "data/": "Database and user data",
        "AI_models/": "AI detection models and related files"
    }
    
    # Create directories
    for dir_path, description in directories.items():
        os.makedirs(dir_path, exist_ok=True)
        print(f"📁 Created: {dir_path} - {description}")
    
    # Files to keep in root directory (ESSENTIAL FILES ONLY)
    keep_in_root = {
        "ultimate_surveillance_system.py": "✅ MAIN SYSTEM - Complete surveillance application",
        "mobile_ip_webcam_gui.py": "✅ BACKUP SYSTEM - Working IP webcam version",
        "requirements.txt": "✅ DEPENDENCIES - Required Python packages",
        "README.md": "✅ MAIN README - Project documentation", 
        ".gitignore": "✅ GIT CONFIG - Version control settings",
        "FINAL_SYSTEM_SUMMARY.md": "✅ SYSTEM GUIDE - Complete feature summary"
    }
    
    # Files to move to specific locations
    file_moves = {
        # Archive old systems
        "archive/old_systems/": [
            "authenticated_surveillance_system.py",
            "integrated_surveillance.py", 
            "perfect_all_in_one_system.py",
            "simple_authenticated_system.py",
            "setup_and_run.py",
            "setup_mobile_surveillance.py"
        ],
        
        # Archive documentation
        "archive/documentation/": [
            "COMPLETE_GUIDE.md",
            "COMPLETE_SYSTEM_README.md", 
            "HOW_TO_RUN.md",
            "PERFECT_SYSTEM_GUIDE.md",
            "FINAL_USER_GUIDE.md",
            "README_GUI.md",
            "ULTIMATE_SYSTEM_GUIDE.md"
        ],
        
        # Archive setup files
        "archive/setup_files/": [
            "alert_system_guide.py",
            "config.py",
            "email_config_setup.py",
            "find_mobile_ip.py",
            "launcher.py", 
            "organize_project.py",
            "requirements_gui.txt",
            "run_surveillance.bat",
            "setup_guide.py",
            "surveillance_data_viewer.py",
            "test_components.py"
        ],
        
        # Move config files
        "configs/": [
            "email_config.json"
        ],
        
        # Move database files
        "data/": [
            "surveillance_data.db",
            "surveillance_system.db"
        ],
        
        # Move AI model directories to organized location
        "AI_models/": [
            "crowddetection",
            "facialexpression", 
            "Object_detection",
            "violence"
        ]
    }
    
    print("\n📦 MOVING FILES TO ORGANIZED STRUCTURE...")
    print("-" * 60)
    
    # Move files to their designated locations
    moved_count = 0
    for destination, files in file_moves.items():
        for file_item in files:
            source_path = Path(file_item)
            dest_path = Path(destination) / source_path.name
            
            if source_path.exists():
                try:
                    if source_path.is_dir():
                        if dest_path.exists():
                            shutil.rmtree(dest_path)
                        shutil.move(str(source_path), str(dest_path))
                        print(f"📁 Moved directory: {file_item} → {destination}")
                    else:
                        shutil.move(str(source_path), str(dest_path))
                        print(f"📄 Moved file: {file_item} → {destination}")
                    moved_count += 1
                except Exception as e:
                    print(f"❌ Error moving {file_item}: {e}")
    
    # Handle special directories
    special_moves = {
        "archive/": ["backup_files", "docs", "alerts", "__pycache__"]
    }
    
    for destination, dirs in special_moves.items():
        for dir_name in dirs:
            source_path = Path(dir_name)
            if source_path.exists():
                dest_path = Path(destination) / source_path.name
                try:
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.move(str(source_path), str(dest_path))
                    print(f"📁 Moved: {dir_name} → {destination}")
                    moved_count += 1
                except Exception as e:
                    print(f"❌ Error moving {dir_name}: {e}")
    
    print(f"\n✅ ORGANIZATION COMPLETE!")
    print(f"📊 Total files/directories moved: {moved_count}")
    
    # Show final structure
    print("\n🗂️ FINAL CLEAN ROOT DIRECTORY:")
    print("=" * 60)
    
    remaining_files = []
    for item in os.listdir("."):
        if os.path.isfile(item):
            remaining_files.append(item)
    
    # Show essential files kept in root
    for file_name, description in keep_in_root.items():
        if os.path.exists(file_name):
            file_size = os.path.getsize(file_name)
            print(f"✅ {file_name:<35} - {description}")
    
    # Show any unexpected files still in root
    unexpected_files = [f for f in remaining_files if f not in keep_in_root.keys()]
    if unexpected_files:
        print(f"\n⚠️ UNEXPECTED FILES IN ROOT (may need manual review):")
        for file_name in unexpected_files:
            print(f"   📄 {file_name}")
    
    # Show organized directory structure 
    print(f"\n📁 ORGANIZED DIRECTORIES:")
    print("-" * 60)
    
    for dir_path, description in directories.items():
        if os.path.exists(dir_path):
            file_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
            dir_count = len([d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d))])
            print(f"📁 {dir_path:<25} - {description}")
            print(f"   📊 Contains: {file_count} files, {dir_count} directories")
    
    # Create organization report
    create_organization_report(keep_in_root, directories)
    
    print(f"\n🎉 PROJECT SUCCESSFULLY ORGANIZED!")
    print(f"📋 Report saved as: PROJECT_ORGANIZATION_REPORT.md")
    print(f"\n🚀 TO RUN YOUR SYSTEM:")
    print(f"   python ultimate_surveillance_system.py")

def create_organization_report(kept_files, directories):
    """Create a report of the organization"""
    
    report = f"""# 🗂️ Smart Surveillance System - Organization Report

## 📁 Project Structure

### ✅ Essential Files (Kept in Root Directory):
"""
    
    for file_name, description in kept_files.items():
        if os.path.exists(file_name):
            report += f"- **{file_name}** - {description}\n"
    
    report += f"""
### 📂 Organized Directories:
"""
    
    for dir_path, description in directories.items():
        if os.path.exists(dir_path):
            file_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
            dir_count = len([d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d))])
            report += f"- **{dir_path}** - {description}\n"
            report += f"  - Contains: {file_count} files, {dir_count} directories\n"
    
    report += f"""
## 🚀 How to Use Your Organized System:

### Main System:
```bash
python ultimate_surveillance_system.py
```

### Backup System:
```bash
python mobile_ip_webcam_gui.py
```

### File Locations:
- **Main Files**: Root directory (clean and minimal)
- **Old Systems**: `archive/old_systems/` 
- **Documentation**: `archive/documentation/`
- **Setup Tools**: `archive/setup_files/`
- **AI Models**: `AI_models/` (organized by type)
- **Configurations**: `configs/`
- **Database**: `data/`

## 📋 Organization Benefits:
- ✅ Clean root directory with only essential files
- ✅ All old versions safely archived
- ✅ Documentation organized and accessible
- ✅ AI models properly categorized
- ✅ Configuration files in dedicated folder
- ✅ Database files centrally located
- ✅ Easy to maintain and navigate

---
*Organization completed on: {Path().absolute()}*
*Report generated by: Smart Surveillance File Organizer*
"""
    
    with open("PROJECT_ORGANIZATION_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    try:
        organize_surveillance_project()
    except KeyboardInterrupt:
        print("\n\n❌ Organization cancelled by user")
    except Exception as e:
        print(f"\n❌ Organization failed: {e}")