# 📱 Mobile IP Webcam Integration Guide

## 🚀 Quick Start

### Step 1: Setup Mobile Camera
1. **Install "IP Webcam" app** on your Android phone from Google Play Store
2. **Connect both phone and laptop** to the same WiFi network
3. **Open IP Webcam app** on your phone
4. **Scroll down and tap "Start server"**
5. **Note the IP address** displayed (e.g., `192.168.0.107:8080`)

### Step 2: Run Your Surveillance System
Choose one of these options:

#### Option 1: Automated Setup (Recommended)
```bash
python setup_mobile_surveillance.py
```

#### Option 2: GUI Version (Best for beginners)
```bash
python mobile_ip_webcam_gui.py
```

#### Option 3: Console Version (Advanced users)
```bash
python mobile_surveillance_system.py
```

## 🛡️ What Your System Detects

### 🔫 Weapon Detection
- Uses your custom trained model (`Object_detection/best.pt`)
- Detects weapons, guns, knives, and dangerous objects
- **Alert Generated**: Immediate red alert with sound

### 👥 Crowd Detection  
- Counts people in the camera view
- Monitors crowd density levels
- **Alert Thresholds**:
  - 5+ people: Medium alert
  - 10+ people: High alert  
  - 15+ people: Critical overcrowding alert

### 😡 Facial Expression Analysis
- Detects emotions: happy, sad, angry, fear, surprise, disgust, neutral
- **Suspicious Behavior Alert**: When angry/fear emotions detected with high confidence
- Tracks multiple faces simultaneously

### 🥊 Violence Detection (Framework Ready)
- Placeholder for violence detection model
- Can be integrated with your existing violence detection code
- Ready for PyTorch-based models

## 📧 Alert System Features

### 🚨 Real-Time Alerts
- **Visual Alerts**: Red boxes around detected threats
- **Audio Alerts**: Beep sounds when threats detected
- **Text Alerts**: Detailed messages in GUI
- **File Alerts**: Saves alert data and images to `alerts/` folder

### 📁 Alert File Generation
For each alert, the system creates:
- `alert_frame_YYYYMMDD_HHMMSS.jpg` - Screenshot of the threat
- `alert_data_YYYYMMDD_HHMMSS.json` - Detailed detection data
- `alert_message_YYYYMMDD_HHMMSS.txt` - Human-readable alert message

### ⏰ Alert Cooldown System
- Prevents spam alerts (10-second cooldown by default)
- Separate cooldowns for different threat types
- Configurable timing in code

## 🔧 Configuration Options

### IP Camera Settings
```python
# In the code, you can modify:
ip_webcam_url = "http://192.168.0.107:8080/video"  # Your mobile IP
backup_camera = 0  # Laptop camera fallback
frame_skip = 2  # Process every 2nd frame for performance
```

### Detection Thresholds
```python
thresholds = {
    "weapon_confidence": 0.6,    # Weapon detection sensitivity
    "crowd_size": 5,             # Minimum people for crowd alert
    "violence_confidence": 0.7,   # Violence detection threshold
    "suspicious_emotion": 0.8     # Emotion detection sensitivity
}
```

## 📱 Mobile IP Webcam Setup Details

### Finding Your Mobile IP
1. **Open IP Webcam app**
2. **Look for the IP address** at the bottom (usually `192.168.x.x:8080`)
3. **Test the connection** by opening `http://192.168.x.x:8080` in your laptop browser

### Common IP Patterns
- Home WiFi: `192.168.1.x` or `192.168.0.x`
- Office WiFi: `10.0.0.x` or `172.16.x.x`
- Mobile Hotspot: `192.168.43.x`

### Troubleshooting Connection Issues
1. **Same Network**: Ensure both devices on same WiFi
2. **Firewall**: Check if phone's firewall blocks connections
3. **App Settings**: In IP Webcam app, check "Local broadcasting" is enabled
4. **Router Settings**: Some routers block device-to-device communication
5. **Alternative**: Use mobile hotspot from phone, connect laptop to it

## 🖥️ GUI Interface Guide

### Main Controls
- **Connect Button**: Establishes connection to IP webcam
- **Start Monitoring**: Begins threat detection
- **Stop Monitoring**: Stops all detection
- **Save Frame**: Captures current frame to file

### Status Indicators
- **Camera Status**: Shows connection type (IP Webcam/Laptop Camera)
- **Weapons Detected**: Live count of weapons in view
- **People Count**: Number of people detected
- **Threat Level**: Overall threat assessment (Low/Medium/High)

### Alert Panel
- **Real-time alerts**: Scrolling text with timestamps
- **Color coding**: Green for normal, Red for threats
- **Clear button**: Removes old alert messages

## 🔄 Integration with Existing Models

### Your Existing Files Integration
The system automatically uses your existing models:

1. **Object Detection**: `Object_detection/best.pt` (Your weapon detection model)
2. **Crowd Detection**: `crowddetection/yolov8s.pt` (Your people counting model)  
3. **Violence Detection**: Can integrate with `violence/violence.py`
4. **Expression Detection**: Uses FER library (auto-downloads model)

### Performance Optimization
- **Frame Skipping**: Processes every 2nd/3rd frame for better performance
- **Multi-threading**: Separate threads for video capture and AI processing
- **Queue System**: Prevents frame dropping and ensures smooth operation
- **Memory Management**: Automatic cleanup to prevent memory leaks

## 📊 System Statistics

The system tracks:
- **Frames Processed**: Total frames analyzed
- **Alerts Generated**: Number of threat alerts
- **Detection Counts**: Individual detection statistics
- **Performance Metrics**: Processing speed and accuracy

## 🔐 Security Features

### Data Privacy
- All processing done locally (no cloud)
- Alert files saved only on your machine
- No data transmission outside your network

### File Security
- Alert files timestamped for easy organization
- JSON format for easy data analysis
- Image evidence for threat verification

## 🚀 Advanced Usage

### Custom Alert Actions
You can modify the code to:
- Send email notifications
- Upload alerts to cloud storage
- Integrate with security systems
- Send SMS alerts
- Control external devices (lights, sirens)

### Model Replacement
- Replace any AI model with your custom trained versions
- Add new detection categories
- Adjust confidence thresholds per use case
- Implement custom alert logic

## 🆘 Support & Troubleshooting

### Common Issues & Solutions

**"Camera not opening"**
- Check IP address is correct
- Verify both devices on same WiFi
- Try manual IP entry in GUI

**"No detections happening"**
- Ensure model files exist in correct folders
- Check detection confidence thresholds
- Verify sufficient lighting in camera view

**"GUI not responding"**
- Try console version instead
- Check Python and tkinter installation
- Close other applications using camera

**"High CPU usage"**
- Increase frame skip value
- Lower detection confidence
- Use smaller video resolution

### Getting Help
- Check log messages in GUI alert panel
- Look for error messages in console
- Verify all model files are present
- Test with laptop camera first, then switch to IP webcam

---

## 🎯 Your Complete Mobile Surveillance System is Ready!

You now have a professional surveillance system that:
- ✅ Connects to your mobile camera via WiFi
- ✅ Detects weapons, crowds, and suspicious behavior
- ✅ Generates real-time alerts with evidence
- ✅ Provides attractive GUI interface
- ✅ Saves all alert data for review
- ✅ Works with your existing AI models

**Start with**: `python setup_mobile_surveillance.py`