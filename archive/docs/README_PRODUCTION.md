# 🛡️ Smart Surveillance System - Real-Time Threat Detection

A comprehensive, production-ready surveillance system powered by AI/ML for real-time threat detection and automated alerting.

## ✨ Features

### 🎯 **AI-Powered Detection**
- **Weapon Detection**: Custom-trained YOLOv8 model for weapons and dangerous objects
- **Crowd Analysis**: Real-time people counting with overcrowding alerts
- **Facial Expression Recognition**: Emotion analysis to detect suspicious behavior
- **Violence Detection**: Framework ready for violence/aggression detection
- **Multi-Model Integration**: Simultaneous processing with multiple AI models

### 📧 **Intelligent Alert System**
- **Email Notifications**: Automatic email alerts when threats detected
- **Configurable Thresholds**: Customizable confidence levels for each threat type
- **Alert Cooldowns**: Prevents spam alerts with intelligent timing
- **Detailed Reports**: Comprehensive threat information in alerts

### 🖥️ **Professional GUI**
- **Real-Time Dashboard**: Live video feed with detection overlays
- **Threat Status Panel**: Color-coded threat level indicators
- **System Statistics**: Performance metrics and detection analytics
- **Historical Data**: Alert history and trend analysis
- **Export Capabilities**: Generate detailed reports

### 📹 **Advanced Video Processing**
- **Multi-Source Support**: Webcam, IP cameras, video files
- **Automatic Failover**: Switches between camera sources automatically
- **Performance Optimization**: Multi-threaded processing for smooth performance
- **Recording Capabilities**: Optional video recording during alerts

## 🚀 Quick Start

### 1. **Automated Setup (Recommended)**
```bash
python setup_and_run.py
```
This script will:
- Check and install all required packages
- Verify model files
- Configure the system
- Launch the application

### 2. **Manual Setup**

#### Install Dependencies
```bash
pip install opencv-python ultralytics fer Pillow numpy psutil
```

#### Run the Application
Choose your preferred interface:

**Basic GUI (Recommended for beginners):**
```bash
python basic_surveillance_gui.py
```

**Advanced GUI (Full features):**
```bash
python main_surveillance_app.py
```

**Console Mode (No GUI):**
```bash
python integration.py
```

## 📋 System Requirements

### **Software Requirements**
- Python 3.8 or higher
- Windows 10/11 (tested), Linux, or macOS
- Webcam or IP camera access
- Internet connection (for email alerts)

### **Hardware Requirements**
- **Minimum**: 4GB RAM, dual-core processor
- **Recommended**: 8GB+ RAM, quad-core processor, GPU (optional)
- **Storage**: 2GB free space for models and logs

### **AI Models**
The system uses several AI models that should be placed in specific directories:

```
Smart_Servellance_System/
├── Object_detection/
│   └── best.pt                    # Custom weapon detection model
├── crowddetection/
│   ├── yolov8s.pt                # Crowd detection model
│   └── yolov8n.pt                # General object detection
└── facialexpression/
    └── (FER model auto-downloaded)
```

## ⚙️ Configuration

### **Email Alerts Setup**

1. **Enable Gmail 2-Factor Authentication**
2. **Generate App Password:**
   - Go to Google Account Settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. **Configure in Application:**
   - Click "Configure Email" in the GUI
   - Enter your Gmail address
   - Enter the App Password (not regular password)
   - Add recipient email addresses

### **Camera Configuration**

**Webcam:**
- Primary source: `0` (default camera)
- Secondary source: `1` (if multiple cameras)

**IP Camera:**
- Full URL: `http://192.168.1.100:8080/video`
- IP only: `192.168.1.100` (system adds default port)

**Mobile Camera (IP Webcam app):**
- Install "IP Webcam" app on phone
- Start server on same WiFi network
- Use displayed IP address in system

### **Threat Thresholds**

Customize detection sensitivity in `config_advanced.py`:

```python
THREAT_THRESHOLDS = {
    'WEAPON_CONFIDENCE': 0.6,          # Weapon detection threshold
    'VIOLENCE_CONFIDENCE': 0.75,       # Violence detection threshold
    'CROWD_DENSITY_HIGH': 15,           # High crowd density alert
    'CROWD_DENSITY_CRITICAL': 25,      # Critical overcrowding alert
    'SUSPICIOUS_EMOTION_THRESHOLD': 0.7 # Suspicious emotion threshold
}
```

## 🎮 Using the System

### **Main Interface Components**

1. **Video Feed Panel**
   - Live camera feed with detection overlays
   - Start/Stop monitoring controls
   - Camera source configuration

2. **Detection Results**
   - Real-time object, weapon, people, and expression counts
   - Individual detection confidence scores
   - Threat status indicators

3. **Threat Status Panel**
   - Overall threat level (Low/Medium/High/Critical)
   - Individual threat type indicators
   - Color-coded status display

4. **System Statistics**
   - Performance metrics
   - Detection accuracy
   - Alert history and trends

5. **System Logs**
   - Real-time system messages
   - Error notifications
   - Alert notifications

### **Operating Workflow**

1. **System Startup**
   - Launch application
   - Configure camera sources
   - Test email configuration (optional)

2. **Start Monitoring**
   - Click "Start Monitoring"
   - System loads AI models
   - Video capture begins
   - Detection processing starts

3. **Threat Detection**
   - AI models analyze each frame
   - Threats identified based on thresholds
   - Alerts generated automatically
   - Email notifications sent

4. **Monitoring and Response**
   - Review real-time threat status
   - Check system logs for details
   - Export reports for analysis
   - Adjust thresholds if needed

## 🔧 Advanced Features

### **Multi-Threading Architecture**
- **Video Capture Thread**: Handles camera input
- **Processing Threads**: Run AI model inference
- **Alert Thread**: Manages email notifications
- **GUI Thread**: Updates user interface

### **Performance Optimization**
- Frame skipping for better performance
- GPU acceleration (if available)
- Memory management and cleanup
- Configurable processing intervals

### **Logging and Monitoring**
- Comprehensive logging to files
- Performance metrics tracking
- System health monitoring
- Export capabilities for analysis

### **Extensibility**
- Modular architecture for adding new models
- Plugin system for custom detections
- API ready for remote monitoring
- Database integration ready

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Video Input   │───▶│  Detection Engine │───▶│  Alert Manager  │
│  (Multi-Source) │    │   (AI Models)    │    │ (Email/Logging) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  GUI Interface  │    │  Video Processor │    │  Config Manager │
│  (Tkinter/UI)   │    │ (Multi-threaded) │    │ (Settings/Logs) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🛠️ Troubleshooting

### **Common Issues**

**Camera Not Opening:**
- Check camera permissions in Windows settings
- Try different camera indices (0, 1, 2)
- Verify IP camera URL and network connection
- Close other applications using the camera

**AI Models Not Loading:**
- Verify model files exist in correct directories
- Check file permissions
- Ensure sufficient disk space
- Review logs for specific error messages

**Email Alerts Not Working:**
- Verify Gmail App Password (not regular password)
- Check 2-Factor Authentication is enabled
- Confirm internet connection
- Test email configuration in GUI

**Performance Issues:**
- Reduce frame processing rate
- Lower detection confidence thresholds
- Close unnecessary applications
- Consider hardware upgrade

**GUI Not Responding:**
- Check Python and tkinter installation
- Try console mode instead
- Review error logs
- Restart application

### **Log Files**
System logs are saved in the `logs/` directory:
- `surveillance_YYYYMMDD.log`: Daily system logs
- Error details and performance metrics
- Alert history and notifications

### **Performance Monitoring**
Monitor system resources:
- CPU usage should be < 80%
- Memory usage monitored in status bar
- FPS displayed for performance tracking
- Processing time metrics available

## 📈 Future Enhancements

### **Planned Features**
- [ ] Mobile app for remote monitoring
- [ ] Database integration for long-term storage
- [ ] Advanced analytics dashboard
- [ ] Multiple camera zones
- [ ] Cloud integration
- [ ] Voice alerts
- [ ] Integration with security systems

### **Model Improvements**
- [ ] Enhanced violence detection
- [ ] Facial recognition capabilities
- [ ] Behavior pattern analysis
- [ ] Custom object training interface
- [ ] Real-time model updates

## 🤝 Support and Contributing

### **Getting Help**
- Check the troubleshooting section
- Review log files for error details
- Verify configuration settings
- Test with different camera sources

### **Reporting Issues**
When reporting issues, please include:
- Python version and OS
- Error messages from logs
- Steps to reproduce the problem
- System specifications

### **Contributing**
Contributions are welcome! Areas for improvement:
- New AI model integrations
- Performance optimizations
- Additional alert methods
- UI/UX enhancements
- Documentation improvements

## 📄 License

This project is open source. Please review the license file for usage terms.

## 🙏 Acknowledgments

- **YOLOv8**: Ultralytics for object detection models
- **FER**: Facial Expression Recognition library
- **OpenCV**: Computer vision framework
- **Tkinter**: GUI framework
- **Community**: Contributors and testers

---

## 🚨 Important Security Notes

1. **Email Credentials**: Store securely, use environment variables in production
2. **Camera Access**: Ensure proper permissions and network security
3. **Model Files**: Verify integrity of AI model files
4. **Network**: Use secure connections for IP cameras
5. **Privacy**: Comply with local privacy laws and regulations

---

**Smart Surveillance System v2.0** - Protecting what matters most with intelligent AI-powered monitoring.