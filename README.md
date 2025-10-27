# Smart Surveillance System

A real-time AI-powered surveillance system with mobile IP webcam integration.

## Quick Start

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

## Mobile Setup

1. Install "IP Webcam" app on Android
2. Start server in the app
3. Note the IP address (e.g., 192.168.0.107:8080)
4. Enter IP in the surveillance system

## AI Detection Features

- **Weapon Detection**: Custom-trained model
- **People Counting**: Crowd density monitoring
- **Facial Expression**: Emotion analysis
- **Real-time Alerts**: Visual and audio notifications

## Project Structure

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

## Requirements

- Python 3.8+
- OpenCV
- Ultralytics YOLO
- FER (Facial Expression Recognition)
- Tkinter (GUI)

## System Features

- Mobile IP webcam integration  
- Multi-model AI detection  
- Real-time threat alerts  
- Professional GUI interface  
- Alert history and logging  
- Automatic camera fallback  

## Documentation

- Complete setup guide: `docs/MOBILE_WEBCAM_GUIDE.md`
- Production manual: `docs/README_PRODUCTION.md`
- Alternative versions: `backup_files/`

---
**Smart Surveillance System** - Advanced AI-powered security monitoring
