#!/usr/bin/env python3
"""
🚀 Smart Surveillance System - Complete Setup Guide
Automated setup and user guide for the surveillance system
"""

import sys
import subprocess
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"🛡️  {title}")
    print("="*60)

def print_step(step_num, description):
    """Print formatted step"""
    print(f"\n📋 Step {step_num}: {description}")
    print("-" * 50)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    print(f"✅ Python version OK: {version.major}.{version.minor}.{version.micro}")
    return True

def install_requirements():
    """Install required packages"""
    requirements = [
        'opencv-python',
        'ultralytics',
        'fer',
        'pillow',
        'tkinter',  # Usually comes with Python
    ]
    
    print("Installing required packages...")
    for package in requirements:
        try:
            if package == 'tkinter':
                # tkinter comes with Python, skip installation
                continue
            
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    
    return True

def create_directory_structure():
    """Create necessary directories"""
    directories = [
        "logs",
        "data",
        "screenshots",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def main():
    """Main setup function"""
    print_header("SMART SURVEILLANCE SYSTEM SETUP")
    
    # Step 1: Check Python version
    print_step(1, "Checking Python Version")
    if not check_python_version():
        input("Press Enter to exit...")
        return
    
    # Step 2: Install requirements
    print_step(2, "Installing Required Packages")
    install_choice = input("Install required packages? (y/N): ").strip().lower()
    if install_choice == 'y':
        if not install_requirements():
            print("❌ Package installation failed!")
            input("Press Enter to exit...")
            return
    
    # Step 3: Create directories
    print_step(3, "Creating Directory Structure")
    create_directory_structure()
    
    # Step 4: Email configuration
    print_step(4, "Email Configuration (Optional)")
    print("For email alerts, you need to configure Gmail settings.")
    email_choice = input("Configure email now? (y/N): ").strip().lower()
    if email_choice == 'y':
        try:
            import email_config_setup
            email_config_setup.main()
        except ImportError:
            print("❌ Email configuration module not found")
    
    # Step 5: System overview
    print_header("SYSTEM OVERVIEW")
    
    print("""
🛡️ SMART SURVEILLANCE SYSTEM COMPONENTS:

1. 📱 AUTHENTICATED SURVEILLANCE SYSTEM (authenticated_surveillance_system.py)
   - User login/registration system
   - Automatic email alerts to logged-in user
   - Complete activity logging
   - IP webcam integration
   - AI-powered threat detection
   
2. 📧 EMAIL CONFIGURATION (email_config_setup.py)
   - Gmail setup with app passwords
   - Email alert templates
   - Test email functionality
   
3. 📊 DATA VIEWER (surveillance_data_viewer.py)
   - View all user activities
   - Monitor threat detections
   - System statistics and analytics
   - Export data capabilities

4. 🔍 IP WEBCAM FINDER (find_mobile_ip.py)
   - Find mobile IP webcam addresses
   - Test camera connections
   
FEATURES:
✅ User Authentication (Login/Register)
✅ Automatic Email Alerts to User
✅ Complete Data Logging (Users, Sessions, Detections, Logs)
✅ AI Threat Detection (Weapons, Crowds, Emotions)
✅ Mobile IP Camera Integration
✅ Sound Alerts with Different Patterns
✅ Real-time Statistics and Monitoring
✅ Professional Data Viewer
✅ Secure Password Storage
✅ Session Management
""")
    
    # Step 6: Usage instructions
    print_header("USAGE INSTRUCTIONS")
    
    print("""
🚀 HOW TO USE THE SYSTEM:

1. START THE MAIN SYSTEM:
   python authenticated_surveillance_system.py
   
   - First-time users will see a login screen
   - Register with your email and password
   - Login to access the surveillance system
   - System will automatically send alerts to your email

2. CONFIGURE EMAIL (First Time Only):
   python email_config_setup.py
   
   - Follow Gmail setup instructions
   - Get App Password from Google
   - Test email configuration

3. VIEW SYSTEM DATA:
   python surveillance_data_viewer.py
   
   - Monitor all user activities
   - View threat detection history
   - Check system statistics
   - Export data for analysis

4. FIND MOBILE CAMERAS:
   python find_mobile_ip.py
   
   - Discover IP webcam addresses
   - Test camera connections
   - Get connection URLs

📱 MOBILE IP WEBCAM SETUP:
1. Install "IP Webcam" app on Android
2. Start the app and note the IP address
3. Use URL format: http://192.168.1.100:8080/video
4. Enter this URL in the surveillance system

🚨 THREAT DETECTION:
- WEAPONS: High-priority alerts with rapid beeps
- CROWDS: Medium-priority alerts with steady beeps  
- SUSPICIOUS EMOTIONS: Low-priority alerts with single beep
- ALL detections automatically email the logged-in user

📊 DATA STORAGE:
- All activities stored in surveillance_data.db
- User sessions tracked with login/logout times
- Threat detections logged with confidence scores
- System actions recorded for audit trail
- Email delivery status tracked
""")
    
    # Step 7: Security notes
    print_header("SECURITY & PRIVACY NOTES")
    
    print("""
🔐 SECURITY FEATURES:
✅ Passwords hashed with SHA-256
✅ Session management with automatic timeout
✅ SQLite database for local data storage
✅ Email credentials stored locally only
✅ No cloud data transmission (privacy-first)

⚠️  IMPORTANT SECURITY TIPS:
1. Use strong passwords (8+ characters)
2. Keep email app passwords secure
3. Regularly backup surveillance_data.db
4. Monitor system logs for unusual activity
5. Update system regularly
""")
    
    # Step 8: Troubleshooting
    print_header("TROUBLESHOOTING")
    
    print("""
🔧 COMMON ISSUES & SOLUTIONS:

1. "Camera connection failed"
   ✅ Check IP address and port
   ✅ Ensure mobile and computer on same WiFi
   ✅ Try different camera apps

2. "Email alerts not working"  
   ✅ Run email_config_setup.py
   ✅ Use Gmail App Password (not regular password)
   ✅ Check Gmail 2-factor authentication

3. "AI models not loading"
   ✅ Check internet connection for model download
   ✅ Ensure sufficient disk space
   ✅ Install required packages

4. "Database errors"
   ✅ Check file permissions
   ✅ Backup and recreate database
   ✅ Run as administrator if needed

5. "Performance issues"
   ✅ Close other applications
   ✅ Use lower resolution cameras
   ✅ Reduce detection frequency
""")
    
    print_header("SETUP COMPLETE!")
    
    print("""
🎉 CONGRATULATIONS! Your Smart Surveillance System is ready!

🚀 NEXT STEPS:
1. Run: python authenticated_surveillance_system.py
2. Register your account
3. Connect your IP camera
4. Start monitoring threats
5. Check your email for alerts!

📞 SUPPORT:
- Check surveillance_data_viewer.py for system analytics
- Review logs in the system for troubleshooting
- All data stored locally for privacy

🛡️ STAY SAFE AND SECURE! 🛡️
""")
    
    input("\nPress Enter to finish setup...")

if __name__ == "__main__":
    main()