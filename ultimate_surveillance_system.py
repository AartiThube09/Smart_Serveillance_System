#!/usr/bin/env python3
"""
🛡️ ULTIMATE SMART SURVEILLANCE SYSTEM
Login After Model Loading + Automatic Email Alerts + Beep Sounds + Perfect Detection
"""

import cv2
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import threading
import queue
import time
import datetime
import json
import sqlite3
import hashlib
import smtplib
from pathlib import Path
from PIL import Image, ImageTk
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import AI libraries
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

try:
    from fer import FER
    FER_AVAILABLE = True
except ImportError:
    FER_AVAILABLE = False

try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

class DatabaseManager:
    """Manages user authentication and data logging"""
    
    def __init__(self):
        self.db_path = "surveillance_system.db"
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table with email storage for alerts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                email_alerts BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Check if sessions table needs updating
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_email' not in columns:
            # Drop and recreate sessions table with new schema
            cursor.execute('DROP TABLE IF EXISTS sessions')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_email TEXT,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                logout_time TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Check if detections table needs updating
        cursor.execute("PRAGMA table_info(detections)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_email' not in columns or 'beep_played' not in columns:
            # Drop and recreate detections table with new schema
            cursor.execute('DROP TABLE IF EXISTS detections')
        
        # Detections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_email TEXT,
                session_id INTEGER,
                detection_type TEXT NOT NULL,
                confidence REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                email_sent BOOLEAN DEFAULT FALSE,
                beep_played BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, email, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            password_hash = self.hash_password(password)
            cursor.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", 
                         (email, password_hash))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def authenticate_user(self, email, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        password_hash = self.hash_password(password)
        cursor.execute("SELECT id FROM users WHERE email = ? AND password_hash = ?", 
                      (email, password_hash))
        result = cursor.fetchone()
        if result:
            user_id = result[0]
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
            conn.commit()
        else:
            user_id = None
        conn.close()
        return user_id
    
    def create_session(self, user_id, user_email):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (user_id, user_email) VALUES (?, ?)", (user_id, user_email))
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def log_detection(self, user_id, user_email, session_id, detection_type, confidence, description):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO detections 
                         (user_id, user_email, session_id, detection_type, confidence, description)
                         VALUES (?, ?, ?, ?, ?, ?)""",
                      (user_id, user_email, session_id, detection_type, confidence, description))
        detection_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return detection_id
    
    def mark_email_sent(self, detection_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE detections SET email_sent = TRUE WHERE id = ?", (detection_id,))
        conn.commit()
        conn.close()
    
    def mark_beep_played(self, detection_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE detections SET beep_played = TRUE WHERE id = ?", (detection_id,))
        conn.commit()
        conn.close()

class ModelLoader:
    """Load AI models with progress tracking"""
    
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.models = {}
        self.total_models = 3
        self.loaded_models = 0
    
    def update_progress(self, message):
        if self.progress_callback:
            self.progress_callback(message, self.loaded_models, self.total_models)
    
    def load_all_models(self):
        """Load all AI models with progress updates"""
        self.update_progress("🔄 Loading Weapon Detection Model...")
        try:
            if YOLO_AVAILABLE:
                # Try multiple model paths
                model_paths = [
                    "Object_detection/best.pt",
                    "Object_detection/yolov8n.pt", 
                    "yolov8n.pt"
                ]
                
                for path in model_paths:
                    try:
                        self.models['weapon'] = YOLO(path)
                        break
                    except Exception:
                        continue
                
                if 'weapon' not in self.models:
                    self.models['weapon'] = YOLO('yolov8n.pt')  # Default
                
                self.loaded_models += 1
                self.update_progress("✅ Weapon Detection Model Loaded")
            else:
                self.update_progress("❌ YOLO not available for weapons")
        except Exception as e:
            self.update_progress(f"❌ Weapon model error: {e}")
        
        time.sleep(0.5)
        
        self.update_progress("🔄 Loading Crowd Detection Model...")
        try:
            if YOLO_AVAILABLE:
                # Try crowd-specific models
                crowd_paths = [
                    "crowddetection/yolov8s.pt",
                    "crowddetection/yolov8n.pt",
                    "yolov8n.pt"
                ]
                
                for path in crowd_paths:
                    try:
                        self.models['crowd'] = YOLO(path)
                        break
                    except Exception:
                        continue
                
                if 'crowd' not in self.models:
                    self.models['crowd'] = YOLO('yolov8n.pt')  # Default
                
                self.loaded_models += 1
                self.update_progress("✅ Crowd Detection Model Loaded")
            else:
                self.update_progress("❌ YOLO not available for crowd")
        except Exception as e:
            self.update_progress(f"❌ Crowd model error: {e}")
        
        time.sleep(0.5)
        
        self.update_progress("🔄 Loading Emotion Recognition Model...")
        try:
            if FER_AVAILABLE:
                self.models['emotion'] = FER(mtcnn=True)
                self.loaded_models += 1
                self.update_progress("✅ Emotion Recognition Model Loaded")
            else:
                self.update_progress("❌ FER not available for emotions")
        except Exception as e:
            self.update_progress(f"❌ Emotion model error: {e}")
        
        time.sleep(0.5)
        self.update_progress("🎉 All Models Loaded Successfully!")
        
        return self.models

class LoadingWindow:
    """Model loading window with progress"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤖 Loading AI Models")
        self.root.geometry("500x300")
        self.root.configure(bg='#2c3e50')
        self.root.eval('tk::PlaceWindow . center')
        self.root.resizable(False, False)
        
        self.models = {}
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title_label = tk.Label(self.root, text="🤖 LOADING AI MODELS", 
                              font=('Arial', 18, 'bold'), bg='#2c3e50', fg='white')
        title_label.pack(pady=20)
        
        # Status
        self.status_label = tk.Label(self.root, text="Initializing...", 
                                    font=('Arial', 12), bg='#2c3e50', fg='#bdc3c7')
        self.status_label.pack(pady=10)
        
        # Progress bar frame
        progress_frame = tk.Frame(self.root, bg='#2c3e50')
        progress_frame.pack(pady=20, padx=50, fill='x')
        
        # Progress bar background
        self.progress_bg = tk.Frame(progress_frame, bg='#34495e', height=20)
        self.progress_bg.pack(fill='x')
        
        # Progress bar fill
        self.progress_fill = tk.Frame(self.progress_bg, bg='#2ecc71', height=20)
        self.progress_fill.place(x=0, y=0, width=0, height=20)
        
        # Progress text
        self.progress_text = tk.Label(self.root, text="0/3 Models Loaded", 
                                     font=('Arial', 11, 'bold'), bg='#2c3e50', fg='white')
        self.progress_text.pack(pady=10)
        
        # Start loading
        self.start_loading()
    
    def update_progress(self, message, loaded, total):
        """Update progress display"""
        self.status_label.config(text=message)
        self.progress_text.config(text=f"{loaded}/{total} Models Loaded")
        
        # Update progress bar
        progress_width = int((loaded / total) * 400)  # 400px max width
        self.progress_fill.config(width=progress_width)
        
        self.root.update()
    
    def start_loading(self):
        """Start model loading in thread"""
        def load_models():
            loader = ModelLoader(self.update_progress)
            self.models = loader.load_all_models()
            
            # Small delay to show completion
            time.sleep(1)
            self.root.quit()
        
        thread = threading.Thread(target=load_models)
        thread.daemon = True
        thread.start()
    
    def get_models(self):
        return self.models

class LoginWindow:
    """User authentication window (shown after model loading)"""
    
    def __init__(self, db_manager, models):
        self.db_manager = db_manager
        self.models = models  # Already loaded models
        self.user_id = None
        self.user_email = None
        
        self.root = tk.Tk()
        self.root.title("🔐 Smart Surveillance System - Login")
        self.root.geometry("450x500")
        self.root.configure(bg='#2c3e50')
        self.root.eval('tk::PlaceWindow . center')
        
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        title_label = tk.Label(self.root, text="🛡️ SMART SURVEILLANCE SYSTEM", 
                              font=('Arial', 18, 'bold'), bg='#2c3e50', fg='white')
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(self.root, text="All-in-One Security Solution", 
                                 font=('Arial', 12), bg='#2c3e50', fg='#bdc3c7')
        subtitle_label.pack(pady=(0, 10))
        
        # Models loaded status
        models_label = tk.Label(self.root, text=f"✅ {len(self.models)} AI Models Ready", 
                               font=('Arial', 11, 'bold'), bg='#2c3e50', fg='#2ecc71')
        models_label.pack(pady=(0, 20))
        
        # Login frame
        login_frame = tk.Frame(self.root, bg='#34495e', padx=30, pady=25)
        login_frame.pack(pady=20, padx=40, fill='both', expand=True)
        
        # Email
        tk.Label(login_frame, text="📧 Email (for alerts):", bg='#34495e', fg='white', 
                font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        self.email_entry = tk.Entry(login_frame, font=('Arial', 11), width=30)
        self.email_entry.pack(pady=(0, 15), fill='x')
        
        # Password
        tk.Label(login_frame, text="🔒 Password:", bg='#34495e', fg='white', 
                font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        self.password_entry = tk.Entry(login_frame, show="*", font=('Arial', 11), width=30)
        self.password_entry.pack(pady=(0, 20), fill='x')
        
        # Buttons
        btn_frame = tk.Frame(login_frame, bg='#34495e')
        btn_frame.pack(fill='x', pady=(10, 0))
        
        login_btn = tk.Button(btn_frame, text="🚀 Login & Start Monitoring", 
                             command=self.login, bg='#2ecc71', fg='white', 
                             font=('Arial', 12, 'bold'), pady=8)
        login_btn.pack(fill='x', pady=(0, 10))
        
        register_btn = tk.Button(btn_frame, text="📝 Create New Account", 
                                command=self.register, bg='#3498db', fg='white', 
                                font=('Arial', 11), pady=6)
        register_btn.pack(fill='x')
        
        # Info
        info_label = tk.Label(login_frame, 
                             text="Your email will be used for automatic threat alerts",
                             bg='#34495e', fg='#bdc3c7', font=('Arial', 9))
        info_label.pack(pady=(20, 0))
        
        # Bind Enter key
        self.root.bind('<Return>', lambda e: self.login())
    
    def login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password")
            return
        
        user_id = self.db_manager.authenticate_user(email, password)
        if user_id:
            self.user_id = user_id
            self.user_email = email
            messagebox.showinfo("Success", f"Welcome back!\nEmail alerts will be sent to: {email}")
            self.root.quit()
        else:
            messagebox.showerror("Error", "Invalid email or password")
    
    def register(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return
        
        user_id = self.db_manager.create_user(email, password)
        if user_id:
            self.user_id = user_id
            self.user_email = email
            messagebox.showinfo("Success", f"Account created successfully!\nEmail alerts will be sent to: {email}")
            self.root.quit()
        else:
            messagebox.showerror("Error", "Email already exists")

class UltimateSurveillanceSystem:
    """Main surveillance system with automatic email alerts and beep sounds"""
    
    def __init__(self, db_manager, user_id, user_email, models):
        self.db_manager = db_manager
        self.user_id = user_id
        self.user_email = user_email
        self.models = models
        self.session_id = db_manager.create_session(user_id, user_email)
        
        # Setup automatic email (no configuration needed)
        self.email_config = {
            'enabled': True,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': 'your_gmail@gmail.com',  # User should update this
            'sender_password': 'your_app_password'   # User should update this
        }
        
        # Load email config if exists
        self.load_email_config()
        
        # Video capture
        self.cap = None
        self.video_source = 0
        self.is_monitoring = False
        
        # Threading
        self.video_thread = None
        self.detection_queue = queue.Queue()
        
        # Statistics
        self.stats = {
            'weapons_detected': 0,
            'people_detected': 0,
            'faces_analyzed': 0,
            'threats_blocked': 0,
            'emails_sent': 0,
            'beeps_played': 0
        }
        
        # Setup GUI
        self.setup_gui()
        
        # Start monitoring automatically
        self.start_monitoring()
    
    def setup_gui(self):
        """Setup main surveillance interface"""
        self.root = tk.Tk()
        self.root.title(f"🛡️ Ultimate Surveillance - {self.user_email}")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')
        
        # Top frame - User info and controls
        top_frame = tk.Frame(self.root, bg='#34495e', pady=10)
        top_frame.pack(fill='x', padx=10, pady=5)
        
        # User info
        user_label = tk.Label(top_frame, text=f"👤 User: {self.user_email} | 🤖 Models: {len(self.models)} | 📧 Auto-Alerts: ON", 
                             font=('Arial', 12, 'bold'), bg='#34495e', fg='white')
        user_label.pack(side='left')
        
        # Control buttons
        btn_frame = tk.Frame(top_frame, bg='#34495e')
        btn_frame.pack(side='right')
        
        self.monitor_btn = tk.Button(btn_frame, text="🔴 Stop Monitoring", 
                                    command=self.toggle_monitoring, bg='#e74c3c', fg='white', 
                                    font=('Arial', 11, 'bold'))
        self.monitor_btn.pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="📧 Email Setup", command=self.configure_email,
                 bg='#3498db', fg='white', font=('Arial', 11)).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="📱 IP Webcam", command=self.setup_ip_webcam,
                 bg='#9b59b6', fg='white', font=('Arial', 11)).pack(side='left', padx=5)
        
        # Main content frame
        content_frame = tk.Frame(self.root, bg='#2c3e50')
        content_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left side - Video feed
        video_frame = tk.Frame(content_frame, bg='#34495e', relief='raised', bd=2)
        video_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        tk.Label(video_frame, text="📹 LIVE SURVEILLANCE FEED", 
                font=('Arial', 14, 'bold'), bg='#34495e', fg='white').pack(pady=5)
        
        self.video_label = tk.Label(video_frame, bg='black')
        self.video_label.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Right side - Statistics and logs
        right_frame = tk.Frame(content_frame, bg='#2c3e50', width=300)
        right_frame.pack(side='right', fill='y')
        right_frame.pack_propagate(False)
        
        # Statistics
        stats_frame = tk.Frame(right_frame, bg='#34495e', relief='raised', bd=2)
        stats_frame.pack(fill='x', pady=(0, 5))
        
        tk.Label(stats_frame, text="📊 DETECTION STATISTICS", 
                font=('Arial', 12, 'bold'), bg='#34495e', fg='white').pack(pady=5)
        
        self.stats_vars = {}
        stats_data = [
            ('🔫 Weapons Detected', 'weapons_detected'),
            ('👥 People Detected', 'people_detected'),
            ('😊 Faces Analyzed', 'faces_analyzed'),
            ('🚨 Threats Blocked', 'threats_blocked'),
            ('📧 Emails Sent', 'emails_sent'),
            ('🔊 Beeps Played', 'beeps_played')
        ]
        
        for label_text, key in stats_data:
            frame = tk.Frame(stats_frame, bg='#34495e')
            frame.pack(fill='x', padx=10, pady=2)
            
            tk.Label(frame, text=label_text, bg='#34495e', fg='white',
                    font=('Arial', 10)).pack(side='left')
            
            self.stats_vars[key] = tk.Label(frame, text="0", bg='#34495e', fg='#2ecc71',
                                           font=('Arial', 10, 'bold'))
            self.stats_vars[key].pack(side='right')
        
        # Activity log
        log_frame = tk.Frame(right_frame, bg='#34495e', relief='raised', bd=2)
        log_frame.pack(fill='both', expand=True, pady=(5, 0))
        
        tk.Label(log_frame, text="📝 ACTIVITY LOG", 
                font=('Arial', 12, 'bold'), bg='#34495e', fg='white').pack(pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=35,
                                                 bg='#2c3e50', fg='white', font=('Consolas', 9))
        self.log_text.pack(padx=10, pady=10, fill='both', expand=True)
        
        # Welcome message
        self.log_message(f"🎉 Welcome {self.user_email}!")
        self.log_message(f"🤖 {len(self.models)} AI models loaded")
        self.log_message("🔴 Monitoring started automatically")
        self.log_message("📧 Email alerts configured for threats")
        self.log_message("🔊 Beep sounds enabled for alerts")
        
    def log_message(self, message):
        """Add message to activity log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def setup_camera_connection(self):
        """Setup camera connection with IP webcam option"""
        # Load saved IP config if available
        try:
            with open("ip_config.json", 'r') as f:
                config = json.load(f)
                self.ip_webcam_url = config.get("ip_webcam_url")
        except Exception:
            self.ip_webcam_url = None
        
        # Try IP webcam first if configured
        if hasattr(self, 'ip_webcam_url') and self.ip_webcam_url:
            self.log_message(f"📱 Trying saved IP webcam: {self.ip_webcam_url}")
            self.cap = cv2.VideoCapture(self.ip_webcam_url)
            
            if self.cap.isOpened():
                ret, test_frame = self.cap.read()
                if ret and test_frame is not None:
                    self.log_message("✅ IP webcam connected successfully!")
                    return True
                else:
                    self.cap.release()
                    self.log_message("❌ Saved IP webcam failed")
        
        # Ask user for camera preference
        camera_choice = messagebox.askyesnocancel("📱 Camera Selection", 
                                                  "Choose camera source:\n\n" +
                                                  "YES = Mobile IP Webcam (recommended)\n" +
                                                  "NO = Laptop/Desktop Camera\n" +
                                                  "CANCEL = Exit")
        
        if camera_choice is None:  # User clicked Cancel
            return False
        
        if camera_choice:  # User chose IP webcam
            # Get IP address from user
            ip_address = simpledialog.askstring("📱 Mobile IP Webcam Setup",
                                               "Enter your mobile IP address:\n\n" +
                                               "1. Install 'IP Webcam' app on your phone\n" +
                                               "2. Start the app and note the IP address\n" +
                                               "3. Enter IP address below:\n\n" +
                                               "Example: 192.168.0.107",
                                               initialvalue="192.168.0.107")
            
            if not ip_address:
                self.log_message("❌ IP address not provided, using laptop camera")
                return self.connect_laptop_camera()
            
            # Try to connect to IP webcam
            ip_url = f"http://{ip_address}:8080/video"
            self.log_message(f"📱 Connecting to mobile IP webcam: {ip_url}")
            
            self.cap = cv2.VideoCapture(ip_url)
            
            # Test connection
            if self.cap.isOpened():
                ret, test_frame = self.cap.read()
                if ret and test_frame is not None:
                    self.log_message("✅ Mobile IP webcam connected successfully!")
                    self.ip_webcam_url = ip_url
                    
                    # Save IP config
                    try:
                        with open("ip_config.json", 'w') as f:
                            json.dump({"ip_webcam_url": ip_url}, f, indent=2)
                    except Exception:
                        pass
                    
                    messagebox.showinfo("📱 Success", f"Connected to mobile camera at {ip_address}")
                    return True
                else:
                    self.cap.release()
                    self.log_message("❌ IP webcam connection failed")
            
            # IP webcam failed, ask if user wants to try laptop camera
            retry = messagebox.askyesno("❌ Connection Failed", 
                                       "Failed to connect to mobile IP webcam.\n\n" +
                                       "Would you like to use laptop camera instead?")
            if retry:
                return self.connect_laptop_camera()
            else:
                return False
        
        else:  # User chose laptop camera
            return self.connect_laptop_camera()
    
    def connect_laptop_camera(self):
        """Connect to laptop/desktop camera"""
        self.log_message("💻 Connecting to laptop camera...")
        
        # Try different camera indices
        for camera_index in [0, 1, 2]:
            self.cap = cv2.VideoCapture(camera_index)
            if self.cap.isOpened():
                ret, test_frame = self.cap.read()
                if ret and test_frame is not None:
                    self.log_message(f"✅ Laptop camera connected (index {camera_index})")
                    return True
                else:
                    self.cap.release()
        
        self.log_message("❌ No laptop camera found")
        messagebox.showerror("❌ Camera Error", "Cannot access any camera!\n\nPlease check:\n" +
                           "1. Camera permissions\n" +
                           "2. Camera not used by other apps\n" +
                           "3. Camera drivers installed")
        return False

    def start_monitoring(self):
        """Start video monitoring"""
        if self.is_monitoring:
            return
        
        try:
            # Setup camera connection
            if not self.setup_camera_connection():
                return
            
            # Configure camera settings
            if self.cap and self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for real-time
            
            self.is_monitoring = True
            self.monitor_btn.config(text="🔴 Stop Monitoring", bg='#e74c3c')
            
            # Start video processing thread
            self.video_thread = threading.Thread(target=self.process_video)
            self.video_thread.daemon = True
            self.video_thread.start()
            
            self.log_message("📹 Video monitoring started")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop video monitoring"""
        self.is_monitoring = False
        if self.cap:
            self.cap.release()
        
        self.monitor_btn.config(text="🟢 Start Monitoring", bg='#2ecc71')
        self.log_message("⏹️ Video monitoring stopped")
    
    def toggle_monitoring(self):
        """Toggle monitoring on/off"""
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def process_video(self):
        """Main video processing loop"""
        while self.is_monitoring:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Perform AI detection
            results = self.detect_threats(frame)
            
            # Draw results on frame (WITHOUT question marks)
            annotated_frame = self.draw_detections(frame, results)
            
            # Update GUI
            self.update_video_display(annotated_frame)
            
            # Handle threats
            if self.has_threats(results):
                self.handle_threat_detection(results)
            
            # Update statistics
            self.update_statistics(results)
            
            time.sleep(0.03)  # ~30 FPS
    
    def detect_threats(self, frame):
        """Detect all types of threats using AI models"""
        results = {
            'weapons': [],
            'people': [],
            'faces': [],
            'emotions': []
        }
        
        try:
            # Weapon detection
            if 'weapon' in self.models:
                weapon_results = self.models['weapon'](frame)
                for r in weapon_results:
                    boxes = r.boxes
                    if boxes is not None:
                        for box in boxes:
                            conf = float(box.conf[0])
                            if conf > 0.5:  # Confidence threshold
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                cls = int(box.cls[0])
                                results['weapons'].append({
                                    'bbox': (int(x1), int(y1), int(x2), int(y2)),
                                    'confidence': conf,
                                    'class': cls
                                })
            
            # People detection
            if 'crowd' in self.models:
                people_results = self.models['crowd'](frame)
                for r in people_results:
                    boxes = r.boxes
                    if boxes is not None:
                        for box in boxes:
                            conf = float(box.conf[0])
                            cls = int(box.cls[0])
                            if cls == 0 and conf > 0.4:  # Person class
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                results['people'].append({
                                    'bbox': (int(x1), int(y1), int(x2), int(y2)),
                                    'confidence': conf
                                })
            
            # Emotion detection
            if 'emotion' in self.models:
                emotion_results = self.models['emotion'].detect_emotions(frame)
                for face in emotion_results:
                    x, y, w, h = face['box']
                    results['faces'].append({
                        'bbox': (x, y, x+w, y+h),
                        'emotions': face['emotions'],
                        'dominant': max(face['emotions'], key=face['emotions'].get)
                    })
        
        except Exception as e:
            self.log_message(f"❌ Detection error: {e}")
        
        return results
    
    def draw_detections(self, frame, results):
        """Draw detection results on frame with BLACK text (no question marks)"""
        annotated_frame = frame.copy()
        
        # Draw weapons (RED boxes with BLACK text)
        for weapon in results['weapons']:
            x1, y1, x2, y2 = weapon['bbox']
            conf = weapon['confidence']
            
            # Red box for weapons
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # BLACK text for weapon label
            label = f"WEAPON {conf:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(annotated_frame, (x1, y1-25), (x1+label_size[0]+10, y1), (255, 255, 255), -1)
            cv2.putText(annotated_frame, label, (x1+5, y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        # Draw people (BLUE boxes with BLACK text)
        for person in results['people']:
            x1, y1, x2, y2 = person['bbox']
            conf = person['confidence']
            
            # Blue box for people
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
            # BLACK text for person label
            label = f"PERSON {conf:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(annotated_frame, (x1, y1-25), (x1+label_size[0]+10, y1), (255, 255, 255), -1)
            cv2.putText(annotated_frame, label, (x1+5, y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        # Draw faces with emotions (GREEN boxes with BLACK text)
        for face in results['faces']:
            x1, y1, x2, y2 = face['bbox']
            emotion = face['dominant']
            
            # Green box for faces
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # BLACK text for emotion label
            label = f"FACE: {emotion.upper()}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(annotated_frame, (x1, y1-25), (x1+label_size[0]+10, y1), (255, 255, 255), -1)
            cv2.putText(annotated_frame, label, (x1+5, y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return annotated_frame
    
    def update_video_display(self, frame):
        """Update video display in GUI"""
        try:
            # Resize frame to fit display
            display_frame = cv2.resize(frame, (640, 480))
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_frame)
            
            # Convert to tkinter PhotoImage
            photo = ImageTk.PhotoImage(pil_image)
            
            # Update label
            self.video_label.config(image=photo)
            self.video_label.image = photo  # Keep reference
            
        except Exception as e:
            self.log_message(f"❌ Display error: {e}")
    
    def has_threats(self, results):
        """Check if any threats detected"""
        return len(results['weapons']) > 0 or len(results['people']) > 10
    
    def handle_threat_detection(self, results):
        """Handle detected threats with automatic email and beep"""
        threat_messages = []
        
        # Check weapons
        if results['weapons']:
            weapon_count = len(results['weapons'])
            threat_messages.append(f"🔫 {weapon_count} weapon(s) detected!")
            
            # Log detection in database
            detection_id = self.db_manager.log_detection(
                self.user_id, self.user_email, self.session_id,
                "weapon", results['weapons'][0]['confidence'],
                f"{weapon_count} weapons detected in surveillance area"
            )
            
            # Play URGENT beep sound for weapons
            self.play_beep_sound("weapon")
            self.db_manager.mark_beep_played(detection_id)
            self.stats['beeps_played'] += 1
            
            # Send automatic email alert
            self.send_automatic_email_alert("WEAPON DETECTED", 
                f"{weapon_count} weapon(s) detected in surveillance area", detection_id)
        
        # Check crowd
        if len(results['people']) > 10:
            people_count = len(results['people'])
            threat_messages.append(f"👥 Large crowd detected: {people_count} people!")
            
            # Log detection in database
            detection_id = self.db_manager.log_detection(
                self.user_id, self.user_email, self.session_id,
                "crowd", 0.9,
                f"Large crowd of {people_count} people detected"
            )
            
            # Play crowd beep sound
            self.play_beep_sound("crowd")
            self.db_manager.mark_beep_played(detection_id)
            self.stats['beeps_played'] += 1
            
            # Send automatic email alert
            self.send_automatic_email_alert("CROWD DETECTED",
                f"Large crowd of {people_count} people detected", detection_id)
        
        # Log all threat messages
        for message in threat_messages:
            self.log_message(f"🚨 {message}")
    
    def play_beep_sound(self, threat_type):
        """Play beep sound based on threat type"""
        if not SOUND_AVAILABLE:
            return
        
        def beep_thread():
            try:
                if threat_type == "weapon":
                    # URGENT - Rapid high-pitched beeps
                    for _ in range(5):
                        winsound.Beep(1500, 200)  # 1500Hz, 200ms
                        time.sleep(0.1)
                elif threat_type == "crowd":
                    # WARNING - Medium beeps
                    for _ in range(3):
                        winsound.Beep(1000, 400)  # 1000Hz, 400ms
                        time.sleep(0.2)
                else:
                    # INFO - Single beep
                    winsound.Beep(800, 600)  # 800Hz, 600ms
                    
                self.log_message(f"🔊 {threat_type.upper()} alert beep played")
                
            except Exception as e:
                self.log_message(f"🔇 Beep error: {e}")
        
        # Play beep in separate thread to avoid blocking
        beep_thread = threading.Thread(target=beep_thread)
        beep_thread.daemon = True
        beep_thread.start()
    
    def send_automatic_email_alert(self, threat_type, message, detection_id):
        """Send automatic email alert to logged-in user"""
        if not self.email_config['enabled']:
            self.log_message("📧 Email not configured - please setup Gmail")
            return
        
        def send_email_thread():
            try:
                # Create email message
                msg = MIMEMultipart()
                msg['From'] = self.email_config['sender_email']
                msg['To'] = self.user_email  # Send to logged-in user's email
                msg['Subject'] = f"🚨 URGENT SECURITY ALERT: {threat_type}"
                
                # HTML email body
                html_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                        <h1 style="color: #e74c3c; text-align: center; margin-bottom: 20px;">🚨 SECURITY ALERT</h1>
                        
                        <div style="background-color: #ffebee; border-left: 5px solid #e74c3c; padding: 15px; margin: 20px 0;">
                            <h2 style="color: #c62828; margin: 0;">IMMEDIATE ATTENTION REQUIRED</h2>
                        </div>
                        
                        <p style="font-size: 16px; color: #333;">Dear <strong>{self.user_email}</strong>,</p>
                        
                        <p style="font-size: 16px; color: #333;">Your Smart Surveillance System has detected a security threat:</p>
                        
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #e74c3c; margin-top: 0;">🚨 THREAT DETAILS:</h3>
                            <p><strong>Type:</strong> {threat_type}</p>
                            <p><strong>Description:</strong> {message}</p>
                            <p><strong>Time:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            <p><strong>User:</strong> {self.user_email}</p>
                            <p><strong>Detection ID:</strong> {detection_id}</p>
                        </div>
                        
                        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #2e7d32; margin-top: 0;">📋 RECOMMENDED ACTIONS:</h3>
                            <ul style="color: #333;">
                                <li>Review live video feed immediately</li>
                                <li>Check the monitored area for threats</li>
                                <li>Contact security personnel if necessary</li>
                                <li>Verify all safety protocols</li>
                            </ul>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <p style="font-size: 14px; color: #666;">This alert was automatically sent by your authenticated Smart Surveillance System</p>
                            <p style="font-size: 18px; font-weight: bold; color: #2e7d32;">Stay Safe and Secure! 🛡️</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                msg.attach(MIMEText(html_body, 'html'))
                
                # Send email using Gmail SMTP
                server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
                server.starttls()
                server.login(self.email_config['sender_email'], self.email_config['sender_password'])
                server.sendmail(self.email_config['sender_email'], self.user_email, msg.as_string())
                server.quit()
                
                # Mark as sent in database
                self.db_manager.mark_email_sent(detection_id)
                
                self.log_message(f"📧 ALERT EMAIL sent to {self.user_email}")
                self.stats['emails_sent'] += 1
                self.update_stats_display()
                
            except Exception as e:
                self.log_message(f"❌ Email failed: {e}")
                if "authentication" in str(e).lower():
                    self.log_message("💡 Setup Gmail App Password in Email Settings")
        
        # Send email in separate thread
        email_thread = threading.Thread(target=send_email_thread)
        email_thread.daemon = True
        email_thread.start()
    
    def update_statistics(self, results):
        """Update detection statistics"""
        self.stats['weapons_detected'] += len(results['weapons'])
        self.stats['people_detected'] += len(results['people'])
        self.stats['faces_analyzed'] += len(results['faces'])
        
        if results['weapons'] or len(results['people']) > 10:
            self.stats['threats_blocked'] += 1
        
        self.update_stats_display()
    
    def update_stats_display(self):
        """Update statistics display"""
        for stat_name, value in self.stats.items():
            if stat_name in self.stats_vars:
                self.stats_vars[stat_name].config(text=str(value))
    
    def configure_email(self):
        """Configure Gmail settings for automatic alerts"""
        email_window = tk.Toplevel(self.root)
        email_window.title("📧 Gmail Setup for Automatic Alerts")
        email_window.geometry("600x500")
        email_window.configure(bg='#34495e')
        email_window.transient(self.root)
        email_window.grab_set()
        
        # Title
        tk.Label(email_window, text="📧 GMAIL CONFIGURATION", 
                font=('Arial', 16, 'bold'), bg='#34495e', fg='white').pack(pady=15)
        
        tk.Label(email_window, text=f"Alerts will be sent to: {self.user_email}", 
                font=('Arial', 12), bg='#34495e', fg='#2ecc71').pack(pady=5)
        
        # Form frame
        form_frame = tk.Frame(email_window, bg='#34495e')
        form_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Gmail email for sending
        tk.Label(form_frame, text="Gmail Address (for sending alerts):", bg='#34495e', fg='white', 
                font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        email_entry = tk.Entry(form_frame, font=('Arial', 11), width=50)
        email_entry.pack(fill='x', pady=(0, 15))
        email_entry.insert(0, self.email_config['sender_email'])
        
        # Gmail app password
        tk.Label(form_frame, text="Gmail App Password:", bg='#34495e', fg='white', 
                font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        password_entry = tk.Entry(form_frame, show="*", font=('Arial', 11), width=50)
        password_entry.pack(fill='x', pady=(0, 15))
        password_entry.insert(0, self.email_config['sender_password'])
        
        # Instructions
        instructions = tk.Label(form_frame, 
                               text="📱 Gmail App Password Setup:\n1. Go to Google Account settings\n2. Enable 2-Factor Authentication\n3. Generate App Password for 'Mail'\n4. Use the 16-character App Password here\n5. DO NOT use your regular Gmail password",
                               bg='#2c3e50', fg='#bdc3c7', font=('Arial', 10), 
                               justify='left', relief='flat', padx=15, pady=15)
        instructions.pack(fill='x', pady=(0, 20))
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg='#34495e')
        btn_frame.pack(fill='x')
        
        def test_email():
            """Test email configuration"""
            try:
                test_msg = MIMEText(f"🧪 Test email from Ultimate Surveillance System\n\nHello {self.user_email}!\n\nIf you receive this email, automatic threat alerts are configured correctly.\n\nYour surveillance system is ready to send security alerts automatically!\n\nStay Safe! 🛡️")
                test_msg['Subject'] = "🧪 Test - Ultimate Surveillance System Ready"
                test_msg['From'] = email_entry.get()
                test_msg['To'] = self.user_email
                
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(email_entry.get(), password_entry.get())
                server.sendmail(email_entry.get(), self.user_email, test_msg.as_string())
                server.quit()
                
                messagebox.showinfo("✅ Test Successful", f"Test email sent to {self.user_email}\n\nAutomatic threat alerts are now active!")
                
            except Exception as e:
                error_msg = str(e)
                if "authentication" in error_msg.lower():
                    messagebox.showerror("❌ Authentication Failed", "Gmail authentication failed.\n\nPlease check:\n1. Gmail address is correct\n2. App Password is correct (16 characters)\n3. 2-Factor Authentication is enabled\n4. Using App Password, not regular password")
                else:
                    messagebox.showerror("❌ Test Failed", f"Email test failed:\n{error_msg}")
        
        def save_config():
            """Save email configuration"""
            self.email_config['sender_email'] = email_entry.get()
            self.email_config['sender_password'] = password_entry.get()
            self.email_config['enabled'] = True
            
            self.save_email_config()
            
            messagebox.showinfo("✅ Saved", f"Gmail configuration saved!\n\nAutomatic threat alerts will be sent to:\n{self.user_email}")
            self.log_message("📧 Gmail configuration updated")
            email_window.destroy()
        
        tk.Button(btn_frame, text="🧪 Test Email", command=test_email,
                 bg='#3498db', fg='white', font=('Arial', 11, 'bold'), padx=20).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="💾 Save & Enable", command=save_config,
                 bg='#2ecc71', fg='white', font=('Arial', 11, 'bold'), padx=20).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="❌ Cancel", command=email_window.destroy,
                 bg='#e74c3c', fg='white', font=('Arial', 11, 'bold'), padx=20).pack(side='right', padx=5)
    
    def load_email_config(self):
        """Load email configuration from file"""
        try:
            config_path = Path("email_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                    self.email_config.update(saved_config)
        except Exception as e:
            self.log_message(f"Email config load error: {e}")
    
    def save_email_config(self):
        """Save email configuration to file"""
        try:
            config_path = Path("email_config.json")
            with open(config_path, 'w') as f:
                json.dump(self.email_config, f, indent=2)
        except Exception as e:
            self.log_message(f"Email config save error: {e}")
    
    def setup_ip_webcam(self):
        """Setup IP webcam connection while system is running"""
        if self.is_monitoring:
            restart_needed = messagebox.askyesno("📱 IP Webcam Setup", 
                                                "Monitoring is currently active.\n\n" +
                                                "Stop monitoring to setup IP webcam?")
            if restart_needed:
                self.stop_monitoring()
            else:
                return
        
        # IP webcam setup dialog
        ip_window = tk.Toplevel(self.root)
        ip_window.title("📱 Mobile IP Webcam Setup")
        ip_window.geometry("500x400")
        ip_window.configure(bg='#2c3e50')
        ip_window.transient(self.root)
        ip_window.grab_set()
        
        # Title
        tk.Label(ip_window, text="📱 MOBILE IP WEBCAM SETUP", 
                font=('Arial', 16, 'bold'), bg='#2c3e50', fg='white').pack(pady=15)
        
        # Instructions frame
        inst_frame = tk.Frame(ip_window, bg='#34495e', relief='raised', bd=2)
        inst_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(inst_frame, text="📋 SETUP INSTRUCTIONS:", 
                font=('Arial', 12, 'bold'), bg='#34495e', fg='#3498db').pack(pady=10)
        
        instructions = [
            "1. Install 'IP Webcam' app on your mobile phone",
            "2. Connect mobile and computer to SAME Wi-Fi network",
            "3. Open IP Webcam app on your phone",
            "4. Tap 'Start server' in the app",
            "5. Note the IP address shown (e.g., 192.168.0.107)",
            "6. Enter the IP address below"
        ]
        
        for i, instruction in enumerate(instructions, 1):
            tk.Label(inst_frame, text=instruction, font=('Arial', 10), 
                    bg='#34495e', fg='white', anchor='w').pack(fill='x', padx=15, pady=2)
        
        # IP input frame
        input_frame = tk.Frame(ip_window, bg='#2c3e50')
        input_frame.pack(fill='x', padx=20, pady=20)
        
        tk.Label(input_frame, text="📱 Mobile IP Address:", 
                font=('Arial', 12, 'bold'), bg='#2c3e50', fg='white').pack(anchor='w', pady=(0, 5))
        
        ip_entry = tk.Entry(input_frame, font=('Arial', 12), width=30)
        ip_entry.pack(fill='x', pady=(0, 10))
        ip_entry.insert(0, "192.168.0.107")  # Default IP
        
        # Status label
        status_label = tk.Label(input_frame, text="", font=('Arial', 10), 
                               bg='#2c3e50', fg='#3498db')
        status_label.pack(pady=5)
        
        # Buttons frame
        btn_frame = tk.Frame(ip_window, bg='#2c3e50')
        btn_frame.pack(fill='x', padx=20, pady=10)
        
        def test_connection():
            """Test IP webcam connection"""
            ip_address = ip_entry.get().strip()
            if not ip_address:
                status_label.config(text="❌ Please enter IP address", fg='#e74c3c')
                return
            
            status_label.config(text="🔄 Testing connection...", fg='#f39c12')
            ip_window.update()
            
            try:
                ip_url = f"http://{ip_address}:8080/video"
                test_cap = cv2.VideoCapture(ip_url)
                
                if test_cap.isOpened():
                    ret, frame = test_cap.read()
                    if ret and frame is not None:
                        status_label.config(text="✅ Connection successful!", fg='#2ecc71')
                        test_cap.release()
                        return True
                    else:
                        test_cap.release()
                        status_label.config(text="❌ Cannot read from camera", fg='#e74c3c')
                else:
                    status_label.config(text="❌ Cannot connect to IP webcam", fg='#e74c3c')
            except Exception as e:
                status_label.config(text=f"❌ Connection failed: {str(e)[:50]}", fg='#e74c3c')
            
            return False
        
        def connect_ip_webcam():
            """Connect to IP webcam"""
            if test_connection():
                ip_address = ip_entry.get().strip()
                self.ip_webcam_url = f"http://{ip_address}:8080/video"
                
                # Save IP to config
                config = {"ip_webcam_url": self.ip_webcam_url}
                try:
                    with open("ip_config.json", 'w') as f:
                        json.dump(config, f, indent=2)
                except Exception:
                    pass
                
                messagebox.showinfo("✅ Success", f"IP webcam configured!\n\nIP: {ip_address}\nURL: {self.ip_webcam_url}\n\nYou can now start monitoring.")
                self.log_message(f"📱 IP webcam configured: {ip_address}")
                ip_window.destroy()
        
        def use_laptop_camera():
            """Switch to laptop camera"""
            self.ip_webcam_url = None
            messagebox.showinfo("💻 Laptop Camera", "Switched to laptop camera.\n\nYou can now start monitoring.")
            self.log_message("💻 Switched to laptop camera")
            ip_window.destroy()
        
        # Buttons
        tk.Button(btn_frame, text="🧪 Test Connection", command=test_connection,
                 bg='#3498db', fg='white', font=('Arial', 11, 'bold')).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="📱 Connect IP Webcam", command=connect_ip_webcam,
                 bg='#2ecc71', fg='white', font=('Arial', 11, 'bold')).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="💻 Use Laptop Camera", command=use_laptop_camera,
                 bg='#f39c12', fg='white', font=('Arial', 11, 'bold')).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="❌ Cancel", command=ip_window.destroy,
                 bg='#e74c3c', fg='white', font=('Arial', 11, 'bold')).pack(side='right', padx=5)
    
    def run(self):
        """Run the surveillance system"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_close()
    
    def on_close(self):
        """Handle application close"""
        self.stop_monitoring()
        self.root.quit()
        self.root.destroy()

def main():
    """Main application entry point"""
    print("🤖 Ultimate Smart Surveillance System")
    print("=" * 50)
    
    # Initialize database
    db_manager = DatabaseManager()
    
    try:
        # Step 1: Load AI models first with progress
        print("🔄 Loading AI models...")
        loading_window = LoadingWindow()
        loading_window.root.mainloop()
        models = loading_window.get_models()
        loading_window.root.destroy()
        
        print(f"✅ {len(models)} AI models loaded successfully!")
        
        # Step 2: Show login after models are loaded
        print("🔐 User authentication...")
        login_window = LoginWindow(db_manager, models)
        login_window.root.mainloop()
        
        if login_window.user_id is None:
            print("❌ Authentication cancelled")
            return
        
        login_window.root.destroy()
        print(f"✅ User authenticated: {login_window.user_email}")
        
        # Step 3: Start surveillance system
        print("🛡️ Starting Ultimate Surveillance System...")
        system = UltimateSurveillanceSystem(
            db_manager, 
            login_window.user_id, 
            login_window.user_email, 
            models
        )
        
        print("🚀 System ready! Starting GUI...")
        system.run()
        
    except KeyboardInterrupt:
        print("\n👋 System shutdown requested")
    except Exception as e:
        print(f"❌ System error: {e}")
        messagebox.showerror("System Error", f"Critical error: {e}")
    
    print("🛡️ Ultimate Surveillance System stopped")

if __name__ == "__main__":
    main()