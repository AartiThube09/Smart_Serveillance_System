# 🛡️ Smart Surveillance System - GUI Version

A comprehensive surveillance system with real-time detection capabilities and email alerts.

## ✨ Features

- **Real-time Object Detection**: Detects weapons, people, and various objects
- **Violence Detection**: Identifies violent activities (to be implemented)
- **Crowd Analysis**: Monitors crowd density and overcrowding
- **Facial Expression Recognition**: Analyzes emotions and suspicious behavior
- **Email Alerts**: Automatic email notifications when threats are detected
- **Attractive GUI**: Modern, user-friendly interface
- **Multi-threading**: Efficient processing without blocking the UI
- **Configurable**: Easy setup for different camera sources

## 📋 Requirements

- Python 3.8 or higher
- Webcam or IP camera
- Internet connection (for email alerts)
- Gmail account with App Password (for email alerts)

## 🚀 Installation

### 1. Clone or Download the Repository

```bash
git clone <your-repo-url>
cd Smart_Servellance_System
```

### 2. Install Dependencies

```bash
pip install -r requirements_gui.txt
```

**Note**: If you encounter issues with tkinter on Linux, install it using:
```bash
sudo apt-get install python3-tk
```

### 3. Download Model Files

Make sure you have the following model files in their respective directories:
- `Object_detection/best.pt` - Your trained object detection model
- `crowddetection/yolov8s.pt` - YOLO model for crowd detection
- Violence detection model (to be added)

### 4. Configure Email Settings

Edit `config.py` and update the email configuration:

```python
EMAIL_CONFIG = {
    "sender_email": "your_email@gmail.com",
    "sender_password": "your_app_password",  # Gmail App Password
    "recipient_email": "alert_recipient@gmail.com",
}
```

**Setting up Gmail App Password:**
1. Go to your Google Account settings
2. Enable 2-Factor Authentication
3. Go to Security → App passwords
4. Generate a new app password for "Mail"
5. Use this password in the configuration

## 🎮 Usage

### GUI Mode (Recommended)

```bash
python surveillance_gui.py
```

### Integrated Mode (GUI + Console fallback)

```bash
python integrated_surveillance.py
```

### Console Mode Only (Fallback)

```bash
python integration.py
```

## 🖥️ GUI Interface

### Main Components:

1. **Video Feed Panel**: 
   - Live camera feed with detection overlays
   - Start/Stop camera controls
   - Camera source configuration

2. **Detection Results Panel**:
   - Real-time detection status
   - Threat level indicators
   - Statistics display

3. **Email Configuration**:
   - Email credentials setup
   - Test email functionality
   - Alert status

4. **System Logs**:
   - Real-time system messages
   - Alert notifications
   - Error tracking

### Controls:

- **▶️ Start Camera**: Begin surveillance
- **⏹️ Stop Camera**: Stop surveillance
- **Test Email**: Verify email configuration
- **Camera Field**: Enter camera source (0 for webcam, IP for network camera)

## 📧 Email Alerts

The system automatically sends email alerts when threats are detected:

- **Weapon Detection**: When dangerous objects are identified
- **Violence Detection**: When violent behavior is detected
- **Overcrowding**: When crowd density exceeds safe limits
- **Suspicious Behavior**: When concerning facial expressions are detected

### Email Alert Features:
- Automatic threat detection
- Detailed threat information
- Timestamp and location data
- Configurable alert intervals

## 🔧 Configuration

### Camera Sources:

- **Webcam**: Use `0` (default), `1`, `2`, etc.
- **IP Camera**: Use full URL like `http://192.168.1.100:8080/video`
- **Video File**: Use file path like `C:/videos/test.mp4`

### Detection Thresholds:

Edit `config.py` to adjust sensitivity:

```python
DETECTION_THRESHOLDS = {
    "weapon_confidence": 0.5,
    "violence_confidence": 0.7,
    "overcrowd_limit": 15,
    "suspicious_emotion_threshold": 0.7,
}
```

## 🛠️ Troubleshooting

### Common Issues:

1. **Camera not opening**:
   - Check camera permissions
   - Try different camera indices (0, 1, 2)
   - Verify IP camera URL

2. **Model not loading**:
   - Check if model files exist in correct directories
   - Verify file permissions
   - Check if CUDA is available for GPU models

3. **Email not sending**:
   - Verify Gmail App Password (not regular password)
   - Check internet connection
   - Ensure less secure app access is enabled

4. **GUI not starting**:
   - Install tkinter: `pip install tk`
   - System will fallback to console mode automatically

### Performance Tips:

- Use GPU acceleration if available
- Reduce camera resolution for better performance
- Adjust detection confidence thresholds
- Close other resource-intensive applications

## 📁 Project Structure

```
Smart_Servellance_System/
├── surveillance_gui.py          # Main GUI application
├── integrated_surveillance.py   # Integrated launcher
├── integration.py               # Original console version
├── config.py                   # Configuration settings
├── requirements_gui.txt        # Python dependencies
├── Object_detection/
│   ├── best.pt                # Object detection model
│   └── objectdetection.py     # Object detection module
├── crowddetection/
│   ├── yolov8s.pt            # Crowd detection model
│   └── crowddetection.py     # Crowd detection module
├── facialexpression/
│   └── expression.py         # Facial expression module
└── violence/
    └── violence.py            # Violence detection module
```

## 🔮 Future Enhancements

- [ ] Complete violence detection implementation
- [ ] Add database logging
- [ ] Implement user authentication
- [ ] Add mobile app notifications
- [ ] Include video recording during alerts
- [ ] Add multiple camera support
- [ ] Implement advanced analytics dashboard

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is open source. Please check the license file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the configuration guide

---

**⚠️ Important Security Note**: Keep your email credentials secure and use environment variables in production deployments.