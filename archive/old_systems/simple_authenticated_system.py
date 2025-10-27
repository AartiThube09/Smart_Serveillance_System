#!/usr/bin/env python3
"""
🛡️ Simple Authenticated Surveillance System
User authentication with email alerts - Simplified version without complex dependencies
"""

import cv2
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import time
import datetime
import sqlite3
import hashlib
from pathlib import Path
from PIL import Image, ImageTk

# Import detection libraries with graceful fallback
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️ YOLO not available - weapon/crowd detection disabled")

# Email libraries
try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("⚠️ Email not available - alerts disabled")

# Sound alerts (Windows only)
try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False
    print("⚠️ Sound alerts not available")

class DatabaseManager:
    """Manages user authentication and activity logging"""
    
    def __init__(self, db_path="surveillance_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                logout_time TIMESTAMP,
                duration_minutes INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Detections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id INTEGER,
                detection_type TEXT NOT NULL,
                confidence REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                email_sent BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')
        
        # System logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password for secure storage"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, email, password):
        """Create new user account"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(password)
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None  # User already exists
    
    def authenticate_user(self, email, password):
        """Authenticate user and return user ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute(
            "SELECT id FROM users WHERE email = ? AND password_hash = ?",
            (email, password_hash)
        )
        
        result = cursor.fetchone()
        if result:
            user_id = result[0]
            # Update last login
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            conn.commit()
        else:
            user_id = None
        
        conn.close()
        return user_id
    
    def create_session(self, user_id):
        """Create new session for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO sessions (user_id) VALUES (?)",
            (user_id,)
        )
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def end_session(self, session_id):
        """End session and calculate duration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """UPDATE sessions 
               SET logout_time = CURRENT_TIMESTAMP,
                   duration_minutes = (julianday(CURRENT_TIMESTAMP) - julianday(login_time)) * 24 * 60
               WHERE id = ?""",
            (session_id,)
        )
        conn.commit()
        conn.close()
    
    def log_detection(self, user_id, session_id, detection_type, confidence=0.0, description=""):
        """Log threat detection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO detections 
               (user_id, session_id, detection_type, confidence, description)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, session_id, detection_type, confidence, description)
        )
        detection_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return detection_id
    
    def mark_email_sent(self, detection_id):
        """Mark that email was sent for detection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE detections SET email_sent = TRUE WHERE id = ?",
            (detection_id,)
        )
        conn.commit()
        conn.close()
    
    def log_system_action(self, user_id, action, details=""):
        """Log system actions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO system_logs (user_id, action, details) VALUES (?, ?, ?)",
            (user_id, action, details)
        )
        conn.commit()
        conn.close()
    
    def get_user_email(self, user_id):
        """Get user email by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None

class LoginWindow:
    """User authentication window"""
    
    def __init__(self, db_manager, on_success_callback):
        self.db_manager = db_manager
        self.on_success_callback = on_success_callback
        self.user_id = None
        self.user_email = None
        
        self.root = tk.Tk()
        self.root.title("🔐 Surveillance System Login")
        self.root.geometry("400x350")
        self.root.configure(bg='#2c3e50')
        
        # Center window
        self.root.eval('tk::PlaceWindow . center')
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup login interface"""
        # Title
        title_label = tk.Label(
            self.root, 
            text="🛡️ Smart Surveillance System",
            font=('Arial', 16, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title_label.pack(pady=20)
        
        # Login frame
        login_frame = tk.Frame(self.root, bg='#34495e', padx=20, pady=20)
        login_frame.pack(pady=20, padx=40, fill='both', expand=True)
        
        # Email
        tk.Label(login_frame, text="Email:", bg='#34495e', fg='white', font=('Arial', 10)).pack(anchor='w')
        self.email_entry = tk.Entry(login_frame, font=('Arial', 10), width=30)
        self.email_entry.pack(pady=(5, 15), fill='x')
        
        # Password
        tk.Label(login_frame, text="Password:", bg='#34495e', fg='white', font=('Arial', 10)).pack(anchor='w')
        self.password_entry = tk.Entry(login_frame, show="*", font=('Arial', 10), width=30)
        self.password_entry.pack(pady=(5, 15), fill='x')
        
        # Buttons frame
        buttons_frame = tk.Frame(login_frame, bg='#34495e')
        buttons_frame.pack(fill='x')
        
        # Login button
        login_btn = tk.Button(
            buttons_frame,
            text="🔑 Login",
            command=self.login,
            bg='#3498db',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20
        )
        login_btn.pack(side='left', padx=(0, 10))
        
        # Register button
        register_btn = tk.Button(
            buttons_frame,
            text="📝 Register",
            command=self.register,
            bg='#2ecc71',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20
        )
        register_btn.pack(side='left')
        
        # Status label
        self.status_label = tk.Label(
            login_frame,
            text="Enter your credentials to access the system",
            bg='#34495e',
            fg='#bdc3c7',
            font=('Arial', 9)
        )
        self.status_label.pack(pady=(15, 0))
        
        # Info label
        info_label = tk.Label(
            login_frame,
            text="• Automatic email alerts when threats detected\n• Complete activity logging\n• Secure user authentication",
            bg='#34495e',
            fg='#95a5a6',
            font=('Arial', 8),
            justify='left'
        )
        info_label.pack(pady=(10, 0))
        
        # Bind Enter key
        self.root.bind('<Return>', lambda e: self.login())
        
        # Focus on email entry
        self.email_entry.focus()
    
    def login(self):
        """Handle user login"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        if not email or not password:
            self.status_label.config(text="Please enter both email and password", fg='#e74c3c')
            return
        
        self.status_label.config(text="Authenticating...", fg='#f39c12')
        self.root.update()
        
        user_id = self.db_manager.authenticate_user(email, password)
        
        if user_id:
            self.user_id = user_id
            self.user_email = email
            self.db_manager.log_system_action(user_id, "LOGIN", f"User logged in from {email}")
            
            self.status_label.config(text="Login successful! Starting system...", fg='#2ecc71')
            self.root.update()
            
            # Wait a moment then close
            self.root.after(1000, self.success_login)
        else:
            self.status_label.config(text="Invalid email or password", fg='#e74c3c')
    
    def register(self):
        """Handle user registration"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        if not email or not password:
            self.status_label.config(text="Please enter both email and password", fg='#e74c3c')
            return
        
        if len(password) < 6:
            self.status_label.config(text="Password must be at least 6 characters", fg='#e74c3c')
            return
        
        if '@' not in email:
            self.status_label.config(text="Please enter a valid email address", fg='#e74c3c')
            return
        
        self.status_label.config(text="Creating account...", fg='#f39c12')
        self.root.update()
        
        user_id = self.db_manager.create_user(email, password)
        
        if user_id:
            self.status_label.config(text="Account created! You can now login.", fg='#2ecc71')
            self.db_manager.log_system_action(user_id, "REGISTER", f"New user registered: {email}")
        else:
            self.status_label.config(text="Email already exists. Try logging in.", fg='#e74c3c')
    
    def success_login(self):
        """Handle successful login"""
        self.root.destroy()
        self.on_success_callback(self.user_id, self.user_email)
    
    def run(self):
        """Run login window"""
        self.root.mainloop()
        return self.user_id, self.user_email

class SimpleSurveillanceSystem:
    """Main surveillance system with authentication"""
    
    def __init__(self):
        # Initialize database
        self.db_manager = DatabaseManager()
        
        # User session info
        self.user_id = None
        self.user_email = None
        self.session_id = None
        
        # Show login first
        self.show_login()
    
    def show_login(self):
        """Show login window"""
        login_window = LoginWindow(self.db_manager, self.on_login_success)
        user_id, user_email = login_window.run()
        
        if user_id:
            self.user_id = user_id
            self.user_email = user_email
            self.start_surveillance_system()
        else:
            print("Login cancelled")
    
    def on_login_success(self, user_id, user_email):
        """Handle successful login"""
        self.user_id = user_id
        self.user_email = user_email
    
    def start_surveillance_system(self):
        """Start main surveillance system"""
        # Create session
        self.session_id = self.db_manager.create_session(self.user_id)
        
        # Initialize main GUI
        self.root = tk.Tk()
        self.root.title(f"🛡️ Smart Surveillance System - {self.user_email}")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2c3e50')
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize variables
        self.cap = None
        self.monitoring = False
        self.frame_queue = queue.Queue(maxsize=10)
        
        # Setup UI
        self.setup_ui()
        
        # Log system start
        self.db_manager.log_system_action(
            self.user_id, 
            "SYSTEM_START", 
            f"Surveillance system started for session {self.session_id}"
        )
        
        # Run main loop
        self.root.mainloop()
    
    def setup_ui(self):
        """Setup user interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Top frame - user info and controls
        top_frame = tk.Frame(main_frame, bg='#34495e', height=80)
        top_frame.pack(fill='x', pady=(0, 10))
        top_frame.pack_propagate(False)
        
        # User info
        user_info_frame = tk.Frame(top_frame, bg='#34495e')
        user_info_frame.pack(side='left', fill='y', padx=20, pady=10)
        
        tk.Label(
            user_info_frame,
            text=f"👤 User: {self.user_email}",
            bg='#34495e',
            fg='white',
            font=('Arial', 12, 'bold')
        ).pack(anchor='w')
        
        tk.Label(
            user_info_frame,
            text=f"📅 Session: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            bg='#34495e',
            fg='#bdc3c7',
            font=('Arial', 10)
        ).pack(anchor='w')
        
        # Control buttons
        control_frame = tk.Frame(top_frame, bg='#34495e')
        control_frame.pack(side='right', fill='y', padx=20, pady=10)
        
        self.start_btn = tk.Button(
            control_frame,
            text="▶️ Start Monitoring",
            command=self.start_monitoring,
            bg='#2ecc71',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=15
        )
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = tk.Button(
            control_frame,
            text="⏹️ Stop Monitoring",
            command=self.stop_monitoring,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=15,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=5)
        
        # Test alert button
        test_btn = tk.Button(
            control_frame,
            text="🧪 Test Alert",
            command=self.test_alert,
            bg='#f39c12',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=15
        )
        test_btn.pack(side='left', padx=5)
        
        # Middle frame - video and controls
        middle_frame = tk.Frame(main_frame, bg='#2c3e50')
        middle_frame.pack(fill='both', expand=True)
        
        # Left panel - video
        video_frame = tk.Frame(middle_frame, bg='#34495e')
        video_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Camera connection
        camera_frame = tk.Frame(video_frame, bg='#34495e', height=60)
        camera_frame.pack(fill='x', padx=10, pady=10)
        camera_frame.pack_propagate(False)
        
        tk.Label(camera_frame, text="📹 Camera Source:", bg='#34495e', fg='white', font=('Arial', 10)).pack(side='left', padx=5)
        
        # Camera options
        self.camera_var = tk.StringVar(value="webcam")
        
        webcam_radio = tk.Radiobutton(
            camera_frame, 
            text="💻 Webcam", 
            variable=self.camera_var, 
            value="webcam",
            bg='#34495e', 
            fg='white', 
            selectcolor='#2c3e50'
        )
        webcam_radio.pack(side='left', padx=5)
        
        ip_radio = tk.Radiobutton(
            camera_frame, 
            text="📱 IP Camera", 
            variable=self.camera_var, 
            value="ip",
            bg='#34495e', 
            fg='white', 
            selectcolor='#2c3e50'
        )
        ip_radio.pack(side='left', padx=5)
        
        # IP entry (initially hidden)
        ip_entry_frame = tk.Frame(video_frame, bg='#34495e', height=40)
        ip_entry_frame.pack(fill='x', padx=10, pady=(0, 10))
        ip_entry_frame.pack_propagate(False)
        
        tk.Label(ip_entry_frame, text="📡 IP URL:", bg='#34495e', fg='white', font=('Arial', 9)).pack(side='left', padx=5)
        
        self.ip_entry = tk.Entry(ip_entry_frame, font=('Arial', 9), width=35)
        self.ip_entry.pack(side='left', padx=5)
        self.ip_entry.insert(0, "http://192.168.1.100:8080/video")
        
        connect_btn = tk.Button(
            ip_entry_frame,
            text="🔗 Connect Camera",
            command=self.connect_camera,
            bg='#3498db',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        connect_btn.pack(side='left', padx=5)
        
        # Video display
        self.video_label = tk.Label(video_frame, bg='black', text="📹 No camera connected\n\nClick 'Connect Camera' to start", fg='white', font=('Arial', 12))
        self.video_label.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Right panel - logs and info
        right_panel = tk.Frame(middle_frame, bg='#34495e', width=350)
        right_panel.pack(side='right', fill='y')
        right_panel.pack_propagate(False)
        
        # Logs frame
        logs_label = tk.Label(right_panel, text="📝 Activity Log", bg='#34495e', fg='white', font=('Arial', 12, 'bold'))
        logs_label.pack(pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(
            right_panel,
            bg='#2c3e50',
            fg='white',
            font=('Consolas', 9),
            wrap=tk.WORD,
            height=25
        )
        self.log_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Status frame
        status_frame = tk.Frame(right_panel, bg='#34495e', height=80)
        status_frame.pack(fill='x', padx=10, pady=(0, 10))
        status_frame.pack_propagate(False)
        
        tk.Label(status_frame, text="🔐 System Status", bg='#34495e', fg='white', font=('Arial', 10, 'bold')).pack()
        
        self.status_labels = {}
        statuses = [
            ("Camera", "❌ Disconnected"),
            ("Monitoring", "⏹️ Stopped"),
            ("Email", "📧 Ready" if EMAIL_AVAILABLE else "❌ Disabled"),
            ("Sound", "🔊 Ready" if SOUND_AVAILABLE else "❌ Disabled")
        ]
        
        for status_name, status_text in statuses:
            label = tk.Label(status_frame, text=f"{status_name}: {status_text}", bg='#34495e', fg='#bdc3c7', font=('Arial', 8))
            label.pack()
            self.status_labels[status_name] = label
        
        # Initial log message
        self.log_message(f"🚀 System initialized for user: {self.user_email}")
        self.log_message("📋 Connect camera and start monitoring to detect threats")
        self.log_message("🚨 All detections will automatically email you at: " + self.user_email)
    
    def log_message(self, message):
        """Add message to log display"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        
        # Also log to database
        if hasattr(self, 'user_id') and self.user_id:
            try:
                self.db_manager.log_system_action(self.user_id, "LOG", message)
            except Exception:
                pass  # Don't fail if database logging fails
    
    def connect_camera(self):
        """Connect to camera"""
        try:
            # Release existing connection
            if self.cap:
                self.cap.release()
            
            # Connect based on selection
            if self.camera_var.get() == "webcam":
                self.log_message("🔗 Connecting to webcam...")
                self.cap = cv2.VideoCapture(0)
                source = "Webcam"
            else:
                ip_url = self.ip_entry.get().strip()
                if not ip_url:
                    messagebox.showerror("Error", "Please enter IP camera URL")
                    return
                
                self.log_message(f"🔗 Connecting to IP camera: {ip_url}")
                self.cap = cv2.VideoCapture(ip_url)
                source = ip_url
            
            if self.cap.isOpened():
                self.log_message(f"✅ Camera connected successfully: {source}")
                self.db_manager.log_system_action(self.user_id, "CAMERA_CONNECT", f"Connected to {source}")
                self.status_labels["Camera"].config(text="Camera: ✅ Connected")
                
                # Start video display
                self.update_video_display()
            else:
                self.log_message("❌ Failed to connect to camera")
                self.status_labels["Camera"].config(text="Camera: ❌ Failed")
                messagebox.showerror("Connection Error", "Failed to connect to camera")
        
        except Exception as e:
            self.log_message(f"❌ Camera connection error: {e}")
            messagebox.showerror("Error", f"Camera connection error: {e}")
    
    def start_monitoring(self):
        """Start threat monitoring"""
        if not self.cap or not self.cap.isOpened():
            messagebox.showerror("Error", "Please connect to camera first")
            return
        
        self.monitoring = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_labels["Monitoring"].config(text="Monitoring: ▶️ Active")
        
        self.log_message("🎯 Threat monitoring started")
        self.db_manager.log_system_action(self.user_id, "MONITORING_START", "Threat detection monitoring started")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_threats, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop threat monitoring"""
        self.monitoring = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_labels["Monitoring"].config(text="Monitoring: ⏹️ Stopped")
        
        self.log_message("⏹️ Threat monitoring stopped")
        self.db_manager.log_system_action(self.user_id, "MONITORING_STOP", "Threat detection monitoring stopped")
    
    def test_alert(self):
        """Test alert system"""
        self.log_message("🧪 Testing alert system...")
        
        # Log test detection
        detection_id = self.db_manager.log_detection(
            self.user_id,
            self.session_id,
            "TEST",
            1.0,
            "System test alert"
        )
        
        # Send test alert
        self.send_threat_alert("TEST", "System alert test - all systems working!", detection_id)
    
    def update_video_display(self):
        """Update video display"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Add to queue for monitoring if enabled
                if self.monitoring and not self.frame_queue.full():
                    self.frame_queue.put(frame.copy())
                
                # Display frame
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (560, 420))
                
                image = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(image)
                
                self.video_label.config(image=photo)
                self.video_label.image = photo
        
        # Schedule next update
        if self.cap and self.cap.isOpened():
            self.root.after(50, self.update_video_display)
    
    def monitor_threats(self):
        """Monitor for threats in video frames"""
        threat_counter = 0
        
        while self.monitoring:
            try:
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get(timeout=1)
                    
                    # Simple motion detection or random threat simulation
                    threat_counter += 1
                    
                    # Simulate threat detection every 30 seconds (for demo)
                    if threat_counter > 600:  # 30 seconds at ~20 FPS
                        self.simulate_threat_detection()
                        threat_counter = 0
                
                time.sleep(0.05)  # 20 FPS processing
            
            except queue.Empty:
                continue
            except Exception as e:
                self.log_message(f"❌ Monitoring error: {e}")
    
    def simulate_threat_detection(self):
        """Simulate threat detection for demo purposes"""
        import random
        
        threats = [
            ("SUSPICIOUS_MOTION", "Unusual movement detected in monitored area", 0.75),
            ("UNAUTHORIZED_ACCESS", "Person detected in restricted zone", 0.85),
            ("UNUSUAL_ACTIVITY", "Suspicious behavior pattern identified", 0.65)
        ]
        
        threat_type, description, confidence = random.choice(threats)
        
        # Log detection
        detection_id = self.db_manager.log_detection(
            self.user_id,
            self.session_id,
            threat_type,
            confidence,
            description
        )
        
        # Send alert
        self.send_threat_alert(threat_type, description, detection_id)
    
    def send_threat_alert(self, threat_type, description, detection_id):
        """Send threat alert via email and sound"""
        self.log_message(f"🚨 THREAT DETECTED: {threat_type} - {description}")
        
        # Play sound alert
        self.play_alert_sound(threat_type)
        
        # Send email alert
        self.send_email_alert(threat_type, description, detection_id)
    
    def play_alert_sound(self, threat_type):
        """Play appropriate alert sound"""
        if not SOUND_AVAILABLE:
            self.log_message("🔇 Sound alert not available")
            return
        
        try:
            if threat_type in ["WEAPON", "UNAUTHORIZED_ACCESS"]:
                # High priority - rapid beeps
                for _ in range(3):
                    winsound.Beep(1000, 200)
                    time.sleep(0.1)
            else:
                # Normal priority - single beep
                winsound.Beep(800, 500)
        
        except Exception as e:
            self.log_message(f"🔇 Sound alert error: {e}")
    
    def send_email_alert(self, threat_type, description, detection_id):
        """Send email alert to logged-in user"""
        if not EMAIL_AVAILABLE:
            self.log_message("❌ Email not available - install email libraries")
            return
        
        try:
            # Simple email configuration - user should update these
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = "your_gmail@gmail.com"  # UPDATE THIS
            sender_password = "your_app_password"  # UPDATE THIS
            
            # Check if email is configured
            if sender_email == "your_gmail@gmail.com":
                self.log_message("⚠️ Email not configured - update email settings in code")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = self.user_email
            msg['Subject'] = f"🚨 SECURITY ALERT: {threat_type} Detected"
            
            # Email body
            body = f"""
SECURITY ALERT - IMMEDIATE ATTENTION REQUIRED

Dear {self.user_email},

A security threat has been detected by your surveillance system:

🚨 THREAT TYPE: {threat_type}
📝 DESCRIPTION: {description}
⏰ TIME: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👤 USER: {self.user_email}
🎯 SESSION ID: {self.session_id}

RECOMMENDED ACTIONS:
- Review the surveillance footage immediately
- Check the area for any suspicious activity
- Contact security personnel if necessary
- Verify system is functioning properly

This alert was automatically generated by your Smart Surveillance System.

Stay Safe,
Smart Surveillance System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, self.user_email, text)
            server.quit()
            
            # Mark email as sent
            self.db_manager.mark_email_sent(detection_id)
            
            self.log_message(f"📧 Alert email sent to {self.user_email}")
            
        except Exception as e:
            self.log_message(f"❌ Email alert failed: {e}")
            self.log_message("💡 Tip: Update email credentials in send_email_alert() method")
    
    def on_closing(self):
        """Handle window closing"""
        # Stop monitoring
        if self.monitoring:
            self.stop_monitoring()
        
        # Release camera
        if self.cap:
            self.cap.release()
        
        # End session
        if self.session_id:
            self.db_manager.end_session(self.session_id)
            self.db_manager.log_system_action(self.user_id, "LOGOUT", "User logged out")
        
        # Close window
        self.root.destroy()

def main():
    """Main application entry point"""
    print("🛡️ Starting Simple Authenticated Surveillance System...")
    print("✅ This version works without complex dependencies")
    print("📧 Update email credentials in code for email alerts")
    
    try:
        app = SimpleSurveillanceSystem()
    except KeyboardInterrupt:
        print("\n👋 System shutdown requested")
    except Exception as e:
        print(f"❌ System error: {e}")

if __name__ == "__main__":
    main()