# Email Configuration for Smart Surveillance System
# Fill in your email details here

EMAIL_CONFIG = {
    # Gmail SMTP settings (for other email providers, adjust accordingly)
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    
    # Your email credentials
    "sender_email": "your_email@gmail.com",  # Replace with your email
    "sender_password": "your_app_password",   # Replace with your Gmail app password
    
    # Who should receive alerts
    "recipient_email": "alert_recipient@gmail.com",  # Replace with recipient email
    
    # Alert settings
    "send_alerts": True,  # Set to False to disable email alerts
    "alert_cooldown": 30,  # Minimum seconds between alerts for same threat type
}

# Detection Thresholds
DETECTION_THRESHOLDS = {
    "weapon_confidence": 0.5,      # Minimum confidence for weapon detection
    "violence_confidence": 0.7,    # Minimum confidence for violence detection
    "overcrowd_limit": 15,          # Number of people to trigger overcrowd alert
    "suspicious_emotion_threshold": 0.7,  # Minimum confidence for suspicious emotions
}

# Camera Settings
CAMERA_SETTINGS = {
    "default_source": 0,           # Default camera (0 for webcam, or IP camera URL)
    "frame_width": 640,
    "frame_height": 480,
    "fps": 30,
}

# GUI Settings
GUI_SETTINGS = {
    "window_title": "Smart Surveillance System",
    "window_size": "1400x900",
    "update_interval": 100,        # GUI update interval in milliseconds
    "log_max_lines": 1000,        # Maximum lines in log before clearing
}