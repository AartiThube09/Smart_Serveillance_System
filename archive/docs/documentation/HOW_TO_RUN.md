# 🛡️ Smart Surveillance System - Quick Start Guide

## 📋 **How to Run the Project**

### **Option 1: Basic GUI (Recommended for beginners)**
```bash
python basic_surveillance_gui.py
```
- ✅ Simple and reliable
- ✅ No complex dependencies required upfront
- ✅ Built-in email testing
- ✅ Easy camera setup

### **Option 2: Enhanced Console Version**
```bash
python integration.py
```
- ✅ Works without GUI
- ✅ Shows detections in video window
- ✅ Press 'q' to quit

### **Option 3: Windows Batch File**
```bash
run_surveillance.bat
```
- ✅ Double-click to run
- ✅ Automatic startup

### **Option 4: Interactive Launcher**
```bash
python start_here.py
```
- ✅ Guided setup process
- ✅ Checks all requirements

---

## 🚀 **Quick Setup (3 Steps)**

### **Step 1: Start the GUI**
```bash
python basic_surveillance_gui.py
```

### **Step 2: Setup Camera**
- Enter camera source in the text field:
  - `0` for default webcam
  - `1`, `2`, etc. for other cameras
  - `http://192.168.1.100:8080/video` for IP cameras
- Click **"▶️ Start Camera"**

### **Step 3: Configure Email Alerts (Optional)**
- Enter your Gmail address
- Enter Gmail App Password (not regular password!)
- Enter recipient email for alerts
- Click **"📧 Test Email"** to verify

---

## 📧 **Email Setup Guide**

### **Getting Gmail App Password:**
1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Enable **2-Factor Authentication**
3. Go to **Security** → **App passwords**
4. Generate password for **"Mail"**
5. Use this 16-character password (not your regular Gmail password)

---

## 🔧 **Troubleshooting**

### **Camera Issues:**
- **Problem**: Camera won't start
- **Solution**: Try different numbers (0, 1, 2) or check camera permissions

### **Email Issues:**
- **Problem**: Email test fails
- **Solution**: Use Gmail App Password, not regular password

### **Python Issues:**
- **Problem**: Import errors
- **Solution**: Install packages:
  ```bash
  pip install opencv-python Pillow
  ```

### **Model Issues:**
- **Problem**: AI detection not working
- **Solution**: Models will load automatically or you can add your trained models

---

## 📁 **Project Structure**

```
Smart_Servellance_System/
├── basic_surveillance_gui.py    ← START HERE (Beginner-friendly)
├── integration.py               ← Console version
├── start_here.py                ← Interactive guide
├── run_surveillance.bat         ← Windows launcher
├── Object_detection/
│   └── best.pt                  ← Your object detection model
├── crowddetection/
│   └── yolov8s.pt              ← Crowd detection model
└── facialexpression/
    └── expression.py            ← Expression detection
```

---

## 🎯 **Features**

- **🎥 Live Video Feed**: Real-time camera monitoring
- **📧 Email Alerts**: Automatic threat notifications
- **🎨 Modern GUI**: Clean, professional interface
- **🔍 AI Detection**: Object, crowd, and expression detection
- **⚙️ Easy Configuration**: Simple setup process
- **💾 System Logging**: Track all system events

---

## 💡 **Tips**

1. **Start Simple**: Use `basic_surveillance_gui.py` first
2. **Test Email**: Always test email before relying on alerts
3. **Camera Sources**: Try different camera numbers if one doesn't work
4. **Models**: Your trained models will be integrated automatically
5. **Performance**: Close other applications for better performance

---

## 🆘 **Need Help?**

1. Run `python start_here.py` for interactive guidance
2. Check the system log in the GUI for error messages
3. Try the console version if GUI has issues
4. Ensure camera permissions are enabled in Windows

---

**🎉 You're ready to go! Start with: `python basic_surveillance_gui.py`**