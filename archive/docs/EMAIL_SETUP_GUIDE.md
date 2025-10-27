# 📧 Email Alert Setup Guide

## 🚀 Quick Setup for Gmail

### Step 1: Enable 2-Factor Authentication
1. Go to your Google Account settings
2. Click on "Security" in the left sidebar
3. Enable "2-Step Verification" if not already enabled

### Step 2: Generate App Password
1. In Security settings, find "App passwords"
2. Click "Generate" and select "Mail" as the app
3. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)
4. **Important**: Use this App Password, NOT your regular Gmail password

### Step 3: Configure in Surveillance System
1. Click "📧 Configure Email" button in the surveillance system
2. Enter your Gmail address (e.g., `yourname@gmail.com`)
3. Enter the App Password (16 characters from Step 2)
4. Add recipient email addresses (one per line)
5. Check "Enable Email Alerts"
6. Click "🧪 Test Email" to verify setup
7. Click "💾 Save Configuration"

## 📧 What You'll Receive

When threats are detected, you'll get emails with:

### 📋 Email Content:
- **Subject**: "🚨 SECURITY ALERT - Smart Surveillance System"
- **Timestamp**: When the threat was detected
- **Threat Details**: What was detected (weapons, crowds, suspicious behavior)
- **Evidence Photo**: Screenshot of the threat
- **Action Required**: Immediate response guidelines

### 🚨 Alert Types:
- **🔫 Weapon Detection**: Immediate high-priority alert
- **👥 Overcrowding**: When people count exceeds threshold
- **😠 Suspicious Behavior**: Angry/fearful facial expressions detected

## ⚙️ Configuration Options

### 📨 Multiple Recipients
Add multiple email addresses to notify:
- Security team
- Management
- Emergency contacts

### 🔔 Alert Frequency
- **Cooldown Period**: 10 seconds between similar alerts
- **Smart Filtering**: Prevents email spam while ensuring critical alerts

### 📁 Local Backup
All alerts are also saved locally in the `alerts/` folder:
- Alert screenshots
- Detection data (JSON format)
- Alert messages (text format)

## 🛠️ Troubleshooting

### ❌ Common Issues:

**"Login Failed" Error:**
- Make sure you're using App Password, not regular password
- Verify 2-Factor Authentication is enabled
- Check internet connection

**"Test Email Failed":**
- Double-check Gmail address spelling
- Ensure App Password is correct (16 characters)
- Try generating a new App Password

**"No Email Received":**
- Check spam/junk folder
- Verify recipient email address
- Test with different email provider

### ✅ Success Indicators:
- Green "Email Alerts: Enabled" status in GUI
- Successful test email received
- "📧 Email alert sent successfully!" in system logs

## 🔒 Security Notes

- App Passwords are safer than regular passwords
- Email configuration is saved locally (password is not stored in plain text)
- All email communication uses encrypted SMTP
- Email alerts include timestamp and evidence for verification

## 📱 Mobile Notifications

For instant mobile alerts:
1. Enable Gmail notifications on your phone
2. Set Gmail as high-priority in notification settings
3. Use distinctive notification sound for security emails

---

**Your Smart Surveillance System now provides instant email alerts for maximum security awareness!** 🛡️