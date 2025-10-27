# 🛡️ Smart Surveillance System with User Authentication

A comprehensive AI-powered surveillance system with user authentication, automatic email alerts, and complete data logging. Perfect for academic projects and real-world security applications.

## 🌟 Key Features

### 🔐 **Complete User Authentication System**
- User registration and login with secure password hashing
- Session management with automatic tracking
- Individual user data isolation and privacy

### 📧 **Automatic Email Alerts**
- Instant email notifications to logged-in user when threats detected
- Gmail integration with App Password security
- Customizable alert templates for different threat types
- Email delivery tracking and confirmation

### 🧠 **AI-Powered Threat Detection**
- **Weapon Detection**: Identifies knives, guns, and dangerous objects
- **Crowd Detection**: Monitors for unusual gatherings or overcrowding
- **Emotion Analysis**: Detects suspicious facial expressions (anger, fear)
- **Real-time Processing**: Live threat assessment with confidence scoring

### 📱 **Mobile Integration**
- IP Webcam support for Android phones
- Remote camera monitoring capabilities
- WiFi-based camera connection
- Multiple camera source support

### 📊 **Complete Data Management**
- **User Management**: Registration, login tracking, session history
- **Detection Logging**: All threats logged with timestamps and confidence
- **System Analytics**: Comprehensive statistics and reporting
- **Data Export**: View and analyze all surveillance data

### 🔊 **Multi-Modal Alerts**
- **Sound Alerts**: Different beep patterns for different threat levels
- **Email Alerts**: Detailed threat information sent to user's email
- **Visual Alerts**: On-screen notifications with threat details
- **Logging Alerts**: Complete audit trail of all activities

## 📁 Project Structure

```
Smart_Surveillance_System/
├── authenticated_surveillance_system.py  # Main surveillance application
├── email_config_setup.py                # Email configuration manager
├── surveillance_data_viewer.py          # Data analytics and viewer
├── find_mobile_ip.py                   # IP camera discovery tool
├── setup_guide.py                      # Complete system setup
├── surveillance_data.db               # SQLite database (auto-created)
├── email_config.json                  # Email settings (auto-created)
└── README.md                          # This file
```

## 🚀 Quick Start Guide

### 1. **Run Setup (Recommended)**
```bash
python setup_guide.py
```
This interactive setup will:
- Check Python requirements
- Install necessary packages
- Configure email settings
- Create directory structure
- Provide complete usage instructions

### 2. **Start the Surveillance System**
```bash
python authenticated_surveillance_system.py
```
- First-time users: Register with email/password
- Returning users: Login with credentials  
- System automatically sends alerts to your email

### 3. **Configure Email (First Time)**
```bash
python email_config_setup.py
```
Follow the Gmail setup instructions:
1. Enable 2-Factor Authentication on Gmail
2. Generate App Password in Google Account settings
3. Use App Password (not regular Gmail password)

### 4. **View System Data**
```bash
python surveillance_data_viewer.py
```
Comprehensive data viewer showing:
- User accounts and session history
- Threat detection records
- System activity logs
- Real-time statistics

## 📱 Mobile IP Camera Setup

### Android Setup (IP Webcam App):
1. Install "IP Webcam" from Google Play Store
2. Open app and configure settings
3. Start server - note the IP address shown
4. Use format: `http://192.168.1.100:8080/video`
5. Enter this URL in the surveillance system

### iOS Setup (EpocCam or similar):
1. Install compatible IP camera app
2. Connect to same WiFi network
3. Get streaming URL from app
4. Enter URL in surveillance system

## 🗄️ Database Schema

The system uses SQLite with the following tables:

### Users Table
- `id`: Unique user identifier
- `email`: User email address (unique)
- `password_hash`: Securely hashed password
- `created_at`: Account creation timestamp
- `last_login`: Most recent login time

### Sessions Table  
- `id`: Session identifier
- `user_id`: Associated user
- `login_time`: Session start time
- `logout_time`: Session end time
- `duration_minutes`: Session length

### Detections Table
- `id`: Detection identifier
- `user_id`: User who was monitoring
- `session_id`: Associated session
- `detection_type`: Type of threat (WEAPON, CROWD, etc.)
- `confidence`: AI confidence score (0-1)
- `timestamp`: When threat was detected
- `description`: Detailed threat description
- `email_sent`: Whether alert email was sent

### System Logs Table
- `id`: Log entry identifier
- `user_id`: Associated user
- `action`: Action type (LOGIN, LOGOUT, DETECTION, etc.)
- `details`: Additional information
- `timestamp`: When action occurred

## 🚨 Threat Detection Details

### Weapon Detection
- **Models**: YOLOv8 trained on weapon datasets
- **Detects**: Knives, guns, sharp objects
- **Alert**: 🚨 Rapid beeping + immediate email
- **Confidence**: Requires >50% confidence to trigger

### Crowd Detection  
- **Models**: YOLOv8 person detection
- **Threshold**: >5 people in frame
- **Alert**: ⚠️ Steady beeping + email notification
- **Use Cases**: Monitoring occupancy, unauthorized gatherings

### Emotion Analysis
- **Models**: FER (Facial Expression Recognition)
- **Detects**: High anger (>70%) or fear (>70%)
- **Alert**: 🔍 Single beep + email alert
- **Privacy**: Processes emotions, not identity

## 📧 Email Alert System

### Gmail Configuration Required:
1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account Settings
   - Security → App passwords
   - Select "Mail" and generate password
   - Use this 16-character password (NOT your regular Gmail password)

### Alert Email Contains:
- **Threat Type**: WEAPON, CROWD, SUSPICIOUS_EMOTION
- **Description**: Detailed threat information
- **Timestamp**: Exact time of detection
- **User Info**: Who was monitoring
- **Session Info**: Current monitoring session
- **Confidence Score**: AI detection confidence
- **Recommended Actions**: Security response guidelines

## 🔐 Security Features

### Password Security
- SHA-256 password hashing
- No plain text password storage
- Secure session management

### Data Privacy
- All data stored locally (no cloud transmission)
- SQLite database with local file access only  
- User data isolation and access control

### Email Security
- App Password authentication (more secure than regular passwords)
- TLS encryption for email transmission
- Local credential storage only

## 📊 System Analytics

The data viewer (`surveillance_data_viewer.py`) provides:

### User Analytics
- Total registered users
- Session history and duration
- Activity patterns and statistics

### Detection Analytics  
- Threat detection frequency by type
- Confidence score distributions
- Time-based threat patterns
- Email delivery success rates

### System Health
- Database size and performance
- Recent activity monitoring
- Error tracking and reporting
- Session management statistics

## 🔧 Troubleshooting

### Common Issues:

**Camera Connection Failed**
```
✅ Check IP address format: http://192.168.1.100:8080/video
✅ Ensure devices on same WiFi network
✅ Try different IP camera apps
✅ Check firewall settings
```

**Email Alerts Not Working**
```  
✅ Run email_config_setup.py for configuration
✅ Use Gmail App Password, not regular password
✅ Enable 2-Factor Authentication on Gmail
✅ Check spam folder for test emails
```

**AI Models Not Loading**
```
✅ Ensure internet connection for first-time model download
✅ Check available disk space (models ~100MB each)
✅ Install required packages: pip install ultralytics fer
```

**Database Errors**
```
✅ Check file permissions on surveillance_data.db
✅ Ensure write access to project directory
✅ Run as administrator if needed
```

**Performance Issues**
```
✅ Close other resource-intensive applications
✅ Use lower resolution camera settings
✅ Reduce detection frequency in settings
```

## 🎯 Academic Project Notes

### For Students/Examiners:
- **Complete Authentication System**: Professional login/registration
- **Real Database Integration**: SQLite with proper schema design
- **Email Integration**: Real-world alert system implementation  
- **AI Model Integration**: Multiple ML models working together
- **Clean Code Structure**: Well-organized, documented codebase
- **Data Analytics**: Comprehensive reporting and statistics
- **Security Best Practices**: Password hashing, session management
- **User Experience**: Professional GUI with intuitive design

### Key Technical Skills Demonstrated:
- **Database Design**: SQLite schema with relationships
- **Web Integration**: Email SMTP, IP camera protocols
- **AI/ML Integration**: YOLO, facial expression recognition
- **GUI Development**: tkinter professional interfaces
- **Security Implementation**: Authentication, password hashing
- **Data Management**: CRUD operations, analytics
- **Error Handling**: Comprehensive exception management
- **Documentation**: Complete user guides and code comments

## 📞 Support & Maintenance

### System Monitoring:
- Check `surveillance_data_viewer.py` for system health
- Monitor email delivery success rates
- Review session logs for unusual activity

### Data Backup:
- Regularly backup `surveillance_data.db`
- Export detection data for long-term storage
- Keep email configuration secure

### Updates & Maintenance:
- Update AI models periodically for better accuracy
- Monitor system performance and optimize as needed
- Review and update email alert templates

## 🏆 System Benefits

### For Personal Use:
- **Home Security**: Monitor home while away
- **Business Security**: Office or shop surveillance  
- **Event Monitoring**: Party or gathering oversight
- **Remote Monitoring**: Check on property remotely

### For Academic Projects:
- **Complete System**: Full-stack application development
- **Real-world Application**: Practical security implementation
- **Technical Depth**: Database, AI, networking integration
- **Professional Quality**: Enterprise-level features and security

### For Learning:
- **Python Development**: Advanced programming concepts
- **Database Design**: Relational database implementation
- **AI Integration**: Machine learning model deployment
- **Security Practices**: Authentication and data protection
- **User Interface**: Professional GUI development

---

## 🎉 Conclusion

This Smart Surveillance System represents a complete, production-ready application that combines:
- **Advanced AI** for threat detection
- **Secure user authentication** for privacy
- **Automatic email alerts** for immediate notification  
- **Comprehensive data logging** for analytics
- **Professional user interface** for ease of use
- **Mobile integration** for flexibility
- **Academic excellence** for educational value

Perfect for academic projects, personal security, or as a foundation for commercial surveillance applications.

**🛡️ Stay Safe and Secure! 🛡️**