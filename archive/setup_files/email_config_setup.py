#!/usr/bin/env python3
"""
📧 Email Configuration Manager
Secure email setup for surveillance system alerts
"""

import json
from pathlib import Path

class EmailConfig:
    """Manages email configuration for surveillance alerts"""
    
    def __init__(self, config_file="email_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """Load email configuration from file"""
        config_path = Path(self.config_file)
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.get_default_config()
        else:
            return self.get_default_config()
    
    def get_default_config(self):
        """Get default email configuration"""
        return {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "",
            "sender_password": "",
            "use_tls": True,
            "alert_templates": {
                "WEAPON": {
                    "subject": "🚨 CRITICAL ALERT: Weapon Detected",
                    "priority": "HIGH",
                    "sound_pattern": "rapid_beeps"
                },
                "CROWD": {
                    "subject": "⚠️ ALERT: Crowd Detected",
                    "priority": "MEDIUM",
                    "sound_pattern": "steady_beeps"
                },
                "SUSPICIOUS_EMOTION": {
                    "subject": "🔍 ALERT: Suspicious Behavior Detected",
                    "priority": "LOW",
                    "sound_pattern": "single_beep"
                }
            }
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def setup_gmail_config(self):
        """Interactive setup for Gmail configuration"""
        print("📧 Gmail Configuration Setup")
        print("=" * 40)
        print("\n⚠️  IMPORTANT: You need a Gmail App Password!")
        print("1. Go to https://myaccount.google.com/")
        print("2. Security → 2-Step Verification (turn ON)")
        print("3. Security → App passwords")
        print("4. Generate app password for 'Mail'")
        print("5. Use that password (not your regular Gmail password)")
        
        print("\n" + "=" * 40)
        
        # Get user input
        sender_email = input("Enter your Gmail address: ").strip()
        
        if not sender_email or '@gmail.com' not in sender_email:
            print("❌ Please enter a valid Gmail address")
            return False
        
        sender_password = input("Enter your Gmail App Password (16 characters): ").strip()
        
        if not sender_password or len(sender_password) < 16:
            print("❌ App password should be 16 characters")
            return False
        
        # Update configuration
        self.config["sender_email"] = sender_email
        self.config["sender_password"] = sender_password
        
        # Test configuration
        if self.test_email_config():
            print("✅ Email configuration successful!")
            self.save_config()
            return True
        else:
            print("❌ Email configuration failed!")
            return False
    
    def test_email_config(self):
        """Test email configuration"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            # Create test message
            msg = MIMEText("Test email from Smart Surveillance System")
            msg['Subject'] = "🧪 Test Email - Surveillance System"
            msg['From'] = self.config["sender_email"]
            msg['To'] = self.config["sender_email"]  # Send to self
            
            # Connect and send
            server = smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"])
            if self.config["use_tls"]:
                server.starttls()
            
            server.login(self.config["sender_email"], self.config["sender_password"])
            server.sendmail(self.config["sender_email"], [self.config["sender_email"]], msg.as_string())
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"❌ Email test failed: {e}")
            return False
    
    def get_config(self):
        """Get current configuration"""
        return self.config
    
    def is_configured(self):
        """Check if email is properly configured"""
        return (self.config.get("sender_email") and 
                self.config.get("sender_password") and 
                len(self.config.get("sender_password", "")) >= 16)

def main():
    """Main configuration setup"""
    print("🛡️ Smart Surveillance System - Email Setup")
    print("=" * 50)
    
    config_manager = EmailConfig()
    
    if config_manager.is_configured():
        print("✅ Email already configured!")
        print(f"📧 Sender: {config_manager.config['sender_email']}")
        
        reconfigure = input("\nReconfigure email? (y/N): ").strip().lower()
        if reconfigure == 'y':
            config_manager.setup_gmail_config()
    else:
        print("📧 Email not configured. Let's set it up!")
        config_manager.setup_gmail_config()
    
    print("\n" + "=" * 50)
    print("📋 Configuration Summary:")
    print(f"SMTP Server: {config_manager.config['smtp_server']}")
    print(f"SMTP Port: {config_manager.config['smtp_port']}")
    print(f"Sender Email: {config_manager.config['sender_email']}")
    print(f"Password Set: {'✅ Yes' if config_manager.config['sender_password'] else '❌ No'}")
    print(f"TLS Enabled: {'✅ Yes' if config_manager.config['use_tls'] else '❌ No'}")
    
    print("\n🎯 Alert Templates:")
    for alert_type, template in config_manager.config['alert_templates'].items():
        print(f"  {alert_type}: {template['subject']} ({template['priority']} priority)")

if __name__ == "__main__":
    main()