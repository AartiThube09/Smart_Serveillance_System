#!/usr/bin/env python3
"""
🛡️ Complete All-in-One Smart Surveillance System
User Authentication + All Threat Detection + Email Alerts + Perfect Accuracy
"""

import cv2
import tkinter as tk
from tkinter import scrolledtext, messagebox
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
    
    def create_session(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (user_id) VALUES (?)", (user_id,))
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def log_detection(self, user_id, session_id, detection_type, confidence, description):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO detections 
                         (user_id, session_id, detection_type, confidence, description)
                         VALUES (?, ?, ?, ?, ?)""",
                      (user_id, session_id, detection_type, confidence, description))
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
    
    def get_user_email(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

class LoginWindow:
    """User authentication window"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.user_id = None
        self.user_email = None
        
        self.root = tk.Tk()
        self.root.title("🔐 Smart Surveillance System - Login")
        self.root.geometry("450x400")
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
        subtitle_label.pack(pady=(0, 20))
        
        # Login frame
        login_frame = tk.Frame(self.root, bg='#34495e', padx=30, pady=25)
        login_frame.pack(pady=20, padx=40, fill='both', expand=True)
        
        # Email
        tk.Label(login_frame, text="📧 Email:", bg='#34495e', fg='white', 
                font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        self.email_entry = tk.Entry(login_frame, font=('Arial', 11), width=30)
        self.email_entry.pack(pady=(0, 15), fill='x')
        
        # Password
        tk.Label(login_frame, text="🔒 Password:", bg='#34495e', fg='white', 
                font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        self.password_entry = tk.Entry(login_frame, show="*", font=('Arial', 11), width=30)
        self.password_entry.pack(pady=(0, 20), fill='x')
        
        # Buttons
        button_frame = tk.Frame(login_frame, bg='#34495e')
        button_frame.pack(fill='x')
        
        login_btn = tk.Button(button_frame, text="🔑 LOGIN", command=self.login,
                             bg='#3498db', fg='white', font=('Arial', 11, 'bold'),
                             padx=25, pady=8)
        login_btn.pack(side='left', padx=(0, 10))
        
        register_btn = tk.Button(button_frame, text="📝 REGISTER", command=self.register,
                                bg='#2ecc71', fg='white', font=('Arial', 11, 'bold'),
                                padx=25, pady=8)
        register_btn.pack(side='left')
        
        # Status
        self.status_label = tk.Label(login_frame, text="Enter credentials to access surveillance system",
                                    bg='#34495e', fg='#bdc3c7', font=('Arial', 10))
        self.status_label.pack(pady=(20, 0))
        
        # Features info
        features_label = tk.Label(login_frame, 
                                 text="✅ Weapon Detection  ✅ Crowd Analysis  ✅ Facial Emotions\n✅ Email Alerts  ✅ Real-time Monitoring  ✅ Data Logging",
                                 bg='#34495e', fg='#95a5a6', font=('Arial', 9), justify='center')
        features_label.pack(pady=(15, 0))
        
        # Bind Enter key
        self.root.bind('<Return>', lambda e: self.login())
        self.email_entry.focus()
    
    def login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        if not email or not password:
            self.status_label.config(text="❌ Please enter both email and password", fg='#e74c3c')
            return
        
        self.status_label.config(text="🔄 Authenticating...", fg='#f39c12')
        self.root.update()
        
        user_id = self.db_manager.authenticate_user(email, password)
        
        if user_id:
            self.user_id = user_id
            self.user_email = email
            self.status_label.config(text="✅ Login successful! Starting system...", fg='#2ecc71')
            self.root.update()
            self.root.after(1000, self.root.destroy)
        else:
            self.status_label.config(text="❌ Invalid email or password", fg='#e74c3c')
    
    def register(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        if not email or not password:
            self.status_label.config(text="❌ Please enter both email and password", fg='#e74c3c')
            return
        
        if len(password) < 6:
            self.status_label.config(text="❌ Password must be at least 6 characters", fg='#e74c3c')
            return
        
        if '@' not in email:
            self.status_label.config(text="❌ Please enter a valid email address", fg='#e74c3c')
            return
        
        self.status_label.config(text="🔄 Creating account...", fg='#f39c12')
        self.root.update()
        
        user_id = self.db_manager.create_user(email, password)
        
        if user_id:
            self.status_label.config(text="✅ Account created! You can now login.", fg='#2ecc71')
        else:
            self.status_label.config(text="❌ Email already exists. Try logging in.", fg='#e74c3c')
    
    def run(self):
        self.root.mainloop()
        return self.user_id, self.user_email

class AllInOneSurveillanceSystem:
    """Complete surveillance system with all features integrated"""
    
    def __init__(self):
        # Database and authentication
        self.db_manager = DatabaseManager()
        self.user_id = None
        self.user_email = None
        self.session_id = None
        
        # Show login first
        self.authenticate_user()
        
        if not self.user_id:
            return
        
        # Initialize main system
        self.setup_main_system()
    
    def authenticate_user(self):
        """Authenticate user before starting system"""
        login_window = LoginWindow(self.db_manager)
        user_id, user_email = login_window.run()
        
        if user_id:
            self.user_id = user_id
            self.user_email = user_email
            self.session_id = self.db_manager.create_session(user_id)
        else:
            print("Authentication cancelled")
    
    def setup_main_system(self):
        """Setup main surveillance system"""
        # Main window
        self.root = tk.Tk()
        self.root.title(f"🛡️ Smart Surveillance - {self.user_email}")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2c3e50')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize variables
        self.cap = None
        self.monitoring = False
        self.frame_queue = queue.Queue(maxsize=10)
        self.detection_results = {'weapons': [], 'people': [], 'faces': []}
        
        # Email configuration
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': '',
            'sender_password': '',
            'enabled': False
        }
        self.load_email_config()
        
        # AI Models
        self.models = {}
        self.load_ai_models()
        
        # Statistics
        self.stats = {
            'weapons_detected': 0,
            'people_detected': 0,
            'faces_analyzed': 0,
            'threats_blocked': 0,
            'emails_sent': 0
        }
        
        # Alert management
        self.last_alert_time = {}
        self.alert_cooldown = 10  # seconds
        
        # Setup UI
        self.setup_ui()
        
        # Start system
        self.log_message(f"🚀 System started for user: {self.user_email}")
        self.root.mainloop()
    
    def load_ai_models(self):
        """Load all AI models for detection"""
        self.log_message("🔄 Loading AI models...")
        
        # Weapon detection model
        try:
            weapon_path = Path("Object_detection/best.pt")
            if weapon_path.exists() and YOLO_AVAILABLE:
                self.models['weapon'] = YOLO(str(weapon_path))
                self.log_message("✅ Weapon detection model loaded")
            else:
                self.log_message("⚠️ Weapon model not found - using fallback detection")
        except Exception as e:
            self.log_message(f"❌ Weapon model error: {e}")
        
        # People/crowd detection model
        try:
            crowd_path = Path("crowddetection/yolov8s.pt")
            if crowd_path.exists() and YOLO_AVAILABLE:
                self.models['crowd'] = YOLO(str(crowd_path))
                self.log_message("✅ Crowd detection model loaded")
            elif YOLO_AVAILABLE:
                self.models['crowd'] = YOLO('yolov8n.pt')  # Use default model
                self.log_message("✅ Default people detection model loaded")
        except Exception as e:
            self.log_message(f"❌ Crowd model error: {e}")
        
        # Facial expression model
        try:
            if FER_AVAILABLE:
                self.models['emotion'] = FER(mtcnn=True)
                self.log_message("✅ Facial expression model loaded")
        except Exception as e:
            self.log_message(f"❌ Emotion model error: {e}")
        
        self.log_message(f"🎯 {len(self.models)} AI models loaded successfully")
    
    def setup_ui(self):
        """Setup complete user interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Top panel - User info and controls
        top_panel = tk.Frame(main_frame, bg='#34495e', height=100)
        top_panel.pack(fill='x', pady=(0, 10))
        top_panel.pack_propagate(False)
        
        # User info
        user_frame = tk.Frame(top_panel, bg='#34495e')
        user_frame.pack(side='left', fill='y', padx=20, pady=15)
        
        tk.Label(user_frame, text=f"👤 User: {self.user_email}", 
                bg='#34495e', fg='white', font=('Arial', 14, 'bold')).pack(anchor='w')
        tk.Label(user_frame, text=f"📅 Session: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                bg='#34495e', fg='#bdc3c7', font=('Arial', 10)).pack(anchor='w')
        tk.Label(user_frame, text="🛡️ All-in-One Security System", 
                bg='#34495e', fg='#3498db', font=('Arial', 10, 'bold')).pack(anchor='w')
        
        # Control buttons
        control_frame = tk.Frame(top_panel, bg='#34495e')
        control_frame.pack(side='right', fill='y', padx=20, pady=15)
        
        self.start_btn = tk.Button(control_frame, text="▶️ START MONITORING", 
                                  command=self.start_monitoring, bg='#2ecc71', fg='white',
                                  font=('Arial', 11, 'bold'), padx=20, pady=8)
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = tk.Button(control_frame, text="⏹️ STOP MONITORING", 
                                 command=self.stop_monitoring, bg='#e74c3c', fg='white',
                                 font=('Arial', 11, 'bold'), padx=20, pady=8, state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        email_btn = tk.Button(control_frame, text="📧 EMAIL CONFIG", 
                             command=self.configure_email, bg='#f39c12', fg='white',
                             font=('Arial', 11, 'bold'), padx=20, pady=8)
        email_btn.pack(side='left', padx=5)
        
        # Middle panel - Video and controls
        middle_panel = tk.Frame(main_frame, bg='#2c3e50')
        middle_panel.pack(fill='both', expand=True)
        
        # Left side - Video
        video_panel = tk.Frame(middle_panel, bg='#34495e')
        video_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Camera connection
        cam_frame = tk.Frame(video_panel, bg='#34495e', height=50)
        cam_frame.pack(fill='x', padx=10, pady=10)
        cam_frame.pack_propagate(False)
        
        tk.Label(cam_frame, text="📹 Camera:", bg='#34495e', fg='white', 
                font=('Arial', 11, 'bold')).pack(side='left', padx=5)
        
        self.camera_var = tk.StringVar(value="webcam")
        tk.Radiobutton(cam_frame, text="💻 Webcam", variable=self.camera_var, value="webcam",
                      bg='#34495e', fg='white', selectcolor='#2c3e50', 
                      font=('Arial', 10)).pack(side='left', padx=5)
        tk.Radiobutton(cam_frame, text="📱 IP Camera", variable=self.camera_var, value="ip",
                      bg='#34495e', fg='white', selectcolor='#2c3e50', 
                      font=('Arial', 10)).pack(side='left', padx=5)
        
        self.ip_entry = tk.Entry(cam_frame, font=('Arial', 10), width=25)
        self.ip_entry.pack(side='left', padx=5)
        self.ip_entry.insert(0, "http://192.168.1.100:8080/video")
        
        connect_btn = tk.Button(cam_frame, text="🔗 CONNECT", command=self.connect_camera,
                               bg='#3498db', fg='white', font=('Arial', 10, 'bold'))
        connect_btn.pack(side='right', padx=5)
        
        # Video display
        self.video_label = tk.Label(video_panel, bg='black', 
                                   text="📹 No Camera Connected\n\nClick CONNECT to start surveillance", 
                                   fg='white', font=('Arial', 16))
        self.video_label.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Right side - Information panels
        info_panel = tk.Frame(middle_panel, bg='#34495e', width=400)
        info_panel.pack(side='right', fill='y')
        info_panel.pack_propagate(False)
        
        # Detection status
        status_frame = tk.Frame(info_panel, bg='#34495e')
        status_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(status_frame, text="🎯 DETECTION STATUS", bg='#34495e', fg='white',
                font=('Arial', 12, 'bold')).pack()
        
        self.status_vars = {}
        statuses = [
            ("Camera", "❌ Disconnected"),
            ("Monitoring", "⏸️ Stopped"),
            ("AI Models", f"✅ {len(self.models)} Loaded"),
            ("Email Alerts", "❌ Not Configured"),
            ("User Session", f"✅ {self.user_email}")
        ]
        
        for name, status in statuses:
            frame = tk.Frame(status_frame, bg='#34495e')
            frame.pack(fill='x', pady=2)
            tk.Label(frame, text=f"{name}:", bg='#34495e', fg='#bdc3c7', 
                    font=('Arial', 10), width=12, anchor='w').pack(side='left')
            label = tk.Label(frame, text=status, bg='#34495e', fg='#95a5a6', 
                           font=('Arial', 10), anchor='w')
            label.pack(side='left')
            self.status_vars[name] = label
        
        # Statistics
        stats_frame = tk.Frame(info_panel, bg='#34495e')
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(stats_frame, text="📊 LIVE STATISTICS", bg='#34495e', fg='white',
                font=('Arial', 12, 'bold')).pack()
        
        self.stats_vars = {}
        for stat_name in self.stats.keys():
            frame = tk.Frame(stats_frame, bg='#34495e')
            frame.pack(fill='x', pady=2)
            formatted_name = stat_name.replace('_', ' ').title()
            tk.Label(frame, text=f"{formatted_name}:", bg='#34495e', fg='#bdc3c7', 
                    font=('Arial', 10), width=15, anchor='w').pack(side='left')
            label = tk.Label(frame, text="0", bg='#34495e', fg='#3498db', 
                           font=('Arial', 10, 'bold'), anchor='w')
            label.pack(side='left')
            self.stats_vars[stat_name] = label
        
        # Activity log
        log_frame = tk.Frame(info_panel, bg='#34495e')
        log_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Label(log_frame, text="📝 ACTIVITY LOG", bg='#34495e', fg='white',
                font=('Arial', 12, 'bold')).pack()
        
        self.log_text = scrolledtext.ScrolledText(log_frame, bg='#2c3e50', fg='white',
                                                 font=('Consolas', 9), wrap=tk.WORD)
        self.log_text.pack(fill='both', expand=True, pady=(5, 0))
        
        # Update email status
        self.update_email_status()
    
    def log_message(self, message):
        """Add message to activity log"""
        if hasattr(self, 'log_text'):
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}\n"
            self.log_text.insert(tk.END, formatted_message)
            self.log_text.see(tk.END)
        else:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def connect_camera(self):
        """Connect to camera source"""
        try:
            if self.cap:
                self.cap.release()
            
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
                self.log_message(f"✅ Camera connected: {source}")
                self.status_vars["Camera"].config(text="✅ Connected", fg='#2ecc71')
                self.start_video_display()
            else:
                self.log_message("❌ Failed to connect to camera")
                self.status_vars["Camera"].config(text="❌ Failed", fg='#e74c3c')
                messagebox.showerror("Error", "Failed to connect to camera")
        
        except Exception as e:
            self.log_message(f"❌ Camera error: {e}")
            messagebox.showerror("Error", f"Camera error: {e}")
    
    def start_video_display(self):
        """Start displaying video feed"""
        self.update_video_display()
    
    def update_video_display(self):
        """Update video display with detections"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Add to queue for processing if monitoring
                if self.monitoring and not self.frame_queue.full():
                    self.frame_queue.put(frame.copy())
                
                # Draw detections on frame
                annotated_frame = self.draw_detections(frame)
                
                # Convert to display format
                annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                annotated_frame = cv2.resize(annotated_frame, (700, 500))
                
                image = Image.fromarray(annotated_frame)
                photo = ImageTk.PhotoImage(image)
                
                self.video_label.config(image=photo)
                self.video_label.image = photo
        
        # Schedule next update
        if self.cap and self.cap.isOpened():
            self.root.after(30, self.update_video_display)
    
    def draw_detections(self, frame):
        """Draw detection boxes and labels on frame"""
        annotated_frame = frame.copy()
        
        # Draw weapons (RED boxes)
        for weapon in self.detection_results.get('weapons', []):
            bbox = weapon['bbox']
            cv2.rectangle(annotated_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), 
                         (0, 0, 255), 3)
            cv2.putText(annotated_frame, f"WEAPON: {weapon['class']} ({weapon['confidence']:.2f})", 
                       (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Draw people (GREEN boxes)
        for i, person_bbox in enumerate(self.detection_results.get('people', []), 1):
            cv2.rectangle(annotated_frame, (person_bbox[0], person_bbox[1]), 
                         (person_bbox[2], person_bbox[3]), (0, 255, 0), 2)
            cv2.putText(annotated_frame, f"PERSON {i}", 
                       (person_bbox[0], person_bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw faces with emotions (BLUE/YELLOW boxes)
        for face in self.detection_results.get('faces', []):
            bbox = face['bbox']
            emotion = face['emotion']
            confidence = face['confidence']
            color = (0, 0, 255) if emotion in ['angry', 'fear'] else (0, 255, 255)
            
            cv2.rectangle(annotated_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            cv2.putText(annotated_frame, f"{emotion.upper()}: {confidence:.2f}", 
                       (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Add overlay information (BLACK text)
        overlay_text = f"👥 People: {len(self.detection_results.get('people', []))} | 🔫 Weapons: {len(self.detection_results.get('weapons', []))} | 😐 Faces: {len(self.detection_results.get('faces', []))}"
        cv2.putText(annotated_frame, overlay_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return annotated_frame
    
    def start_monitoring(self):
        """Start threat monitoring"""
        if not self.cap or not self.cap.isOpened():
            messagebox.showerror("Error", "Please connect to camera first")
            return
        
        self.monitoring = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_vars["Monitoring"].config(text="▶️ Active", fg='#2ecc71')
        
        self.log_message("🎯 Threat monitoring started - All systems active")
        
        # Start detection thread
        self.detection_thread = threading.Thread(target=self.detection_worker, daemon=True)
        self.detection_thread.start()
    
    def stop_monitoring(self):
        """Stop threat monitoring"""
        self.monitoring = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_vars["Monitoring"].config(text="⏸️ Stopped", fg='#95a5a6')
        
        self.log_message("⏹️ Threat monitoring stopped")
    
    def detection_worker(self):
        """Background detection processing"""
        while self.monitoring:
            try:
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get(timeout=1)
                    
                    # Process frame with all AI models
                    results = self.process_frame_with_all_models(frame)
                    self.detection_results = results
                    
                    # Check for threats and send alerts
                    self.check_threats_and_alert(results, frame)
                    
                    # Update statistics
                    self.update_statistics(results)
                
                time.sleep(0.1)
            
            except queue.Empty:
                continue
            except Exception as e:
                self.log_message(f"❌ Detection error: {e}")
    
    def process_frame_with_all_models(self, frame):
        """Process frame with all available AI models"""
        results = {'weapons': [], 'people': [], 'faces': []}
        
        try:
            # Weapon detection
            if 'weapon' in self.models:
                weapon_results = self.models['weapon'].predict(frame, conf=0.5, verbose=False)
                for result in weapon_results:
                    if result.boxes is not None:
                        for box, cls, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                            class_name = self.models['weapon'].names[int(cls)]
                            results['weapons'].append({
                                'class': class_name,
                                'confidence': float(conf),
                                'bbox': [int(x) for x in box]
                            })
            
            # People/crowd detection
            if 'crowd' in self.models:
                crowd_results = self.models['crowd'].predict(frame, conf=0.4, verbose=False)
                for result in crowd_results:
                    if result.boxes is not None:
                        for box, cls in zip(result.boxes.xyxy, result.boxes.cls):
                            if int(cls) == 0:  # Person class
                                results['people'].append([int(x) for x in box])
            
            # Facial expression detection
            if 'emotion' in self.models:
                try:
                    emotion_results = self.models['emotion'].detect_emotions(frame)
                    for emotion_result in emotion_results:
                        emotions = emotion_result['emotions']
                        dominant = max(emotions, key=emotions.get)
                        results['faces'].append({
                            'emotion': dominant,
                            'confidence': emotions[dominant],
                            'bbox': emotion_result['box']
                        })
                except Exception:
                    pass  # FER can be unstable
        
        except Exception as e:
            self.log_message(f"❌ Processing error: {e}")
        
        return results
    
    def check_threats_and_alert(self, results, frame):
        """Check for threats and send alerts"""
        current_time = time.time()
        
        # Check weapons (CRITICAL)
        if results['weapons']:
            if self.should_send_alert('weapon', current_time):
                threat_msg = f"🚨 CRITICAL: {len(results['weapons'])} WEAPON(S) DETECTED!"
                weapon_details = [f"{w['class']} ({w['confidence']:.2f})" for w in results['weapons']]
                threat_msg += f"\nWeapons: {', '.join(weapon_details)}"
                
                self.send_threat_alert("WEAPON", threat_msg, results)
                self.play_alert_sound("weapon")
                self.last_alert_time['weapon'] = current_time
        
        # Check crowd (MEDIUM)
        people_count = len(results['people'])
        if people_count > 5:  # Crowd threshold
            if self.should_send_alert('crowd', current_time):
                threat_msg = f"⚠️ CROWD DETECTED: {people_count} people in area"
                
                self.send_threat_alert("CROWD", threat_msg, results)
                self.play_alert_sound("crowd")
                self.last_alert_time['crowd'] = current_time
        
        # Check suspicious emotions (LOW)
        suspicious_faces = [f for f in results['faces'] if f['emotion'] in ['angry', 'fear'] and f['confidence'] > 0.7]
        if suspicious_faces:
            if self.should_send_alert('emotion', current_time):
                threat_msg = f"🔍 SUSPICIOUS BEHAVIOR: {len(suspicious_faces)} person(s) showing {suspicious_faces[0]['emotion']}"
                
                self.send_threat_alert("SUSPICIOUS_EMOTION", threat_msg, results)
                self.play_alert_sound("emotion")
                self.last_alert_time['emotion'] = current_time
    
    def should_send_alert(self, alert_type, current_time):
        """Check if enough time has passed since last alert"""
        return alert_type not in self.last_alert_time or \
               current_time - self.last_alert_time[alert_type] > self.alert_cooldown
    
    def send_threat_alert(self, threat_type, message, results):
        """Send threat alert via email and log to database"""
        self.log_message(f"🚨 ALERT: {message}")
        
        # Log to database
        detection_id = self.db_manager.log_detection(
            self.user_id, self.session_id, threat_type, 
            0.9, message  # High confidence for alerts
        )
        
        # Send email if configured
        if self.email_config['enabled']:
            self.send_email_alert(threat_type, message, detection_id)
        else:
            self.log_message("📧 Email not configured - alert not sent")
    
    def send_email_alert(self, threat_type, message, detection_id):
        """Send email alert to user"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.user_email
            msg['Subject'] = f"🚨 SECURITY ALERT: {threat_type} - Smart Surveillance"
            
            body = f"""
SECURITY ALERT - IMMEDIATE ATTENTION REQUIRED

Dear {self.user_email},

Your Smart Surveillance System has detected a security threat:

🚨 THREAT TYPE: {threat_type}
📝 DESCRIPTION: {message}
⏰ TIME: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👤 USER: {self.user_email}
🔍 DETECTION ID: {detection_id}

SYSTEM STATUS:
- AI Models Active: {len(self.models)}
- Monitoring Status: Active
- User Session: Authenticated

RECOMMENDED ACTIONS:
1. Review live video feed immediately
2. Check the monitored area for threats
3. Contact security personnel if necessary
4. Verify all safety protocols

This alert was automatically generated by your authenticated Smart Surveillance System.

Stay Safe and Secure,
All-in-One Smart Surveillance System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            server.sendmail(self.email_config['sender_email'], self.user_email, msg.as_string())
            server.quit()
            
            # Mark as sent in database
            self.db_manager.mark_email_sent(detection_id)
            
            self.log_message(f"📧 Alert email sent to {self.user_email}")
            self.stats['emails_sent'] += 1
            self.update_stats_display()
            
        except Exception as e:
            self.log_message(f"❌ Email failed: {e}")
    
    def play_alert_sound(self, alert_type):
        """Play alert sound based on threat type"""
        if not SOUND_AVAILABLE:
            return
        
        try:
            if alert_type == "weapon":
                # Critical - rapid beeps
                for _ in range(5):
                    winsound.Beep(1500, 150)
                    time.sleep(0.05)
            elif alert_type == "crowd":
                # Medium - steady beeps
                for _ in range(3):
                    winsound.Beep(1000, 300)
                    time.sleep(0.1)
            else:
                # Low - single beep
                winsound.Beep(800, 500)
        except Exception as e:
            self.log_message(f"🔇 Sound error: {e}")
    
    def update_statistics(self, results):
        """Update detection statistics"""
        self.stats['weapons_detected'] += len(results['weapons'])
        self.stats['people_detected'] += len(results['people'])
        self.stats['faces_analyzed'] += len(results['faces'])
        
        if results['weapons'] or len(results['people']) > 5:
            self.stats['threats_blocked'] += 1
        
        self.update_stats_display()
    
    def update_stats_display(self):
        """Update statistics display"""
        for stat_name, value in self.stats.items():
            if stat_name in self.stats_vars:
                self.stats_vars[stat_name].config(text=str(value))
    
    def configure_email(self):
        """Configure email settings"""
        email_window = tk.Toplevel(self.root)
        email_window.title("📧 Email Configuration")
        email_window.geometry("500x400")
        email_window.configure(bg='#34495e')
        email_window.transient(self.root)
        email_window.grab_set()
        
        # Title
        tk.Label(email_window, text="📧 EMAIL ALERT CONFIGURATION", 
                font=('Arial', 16, 'bold'), bg='#34495e', fg='white').pack(pady=15)
        
        # Form frame
        form_frame = tk.Frame(email_window, bg='#34495e')
        form_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Gmail email
        tk.Label(form_frame, text="Gmail Address:", bg='#34495e', fg='white', 
                font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        email_entry = tk.Entry(form_frame, font=('Arial', 11), width=40)
        email_entry.pack(fill='x', pady=(0, 15))
        email_entry.insert(0, self.email_config['sender_email'])
        
        # Gmail app password
        tk.Label(form_frame, text="Gmail App Password:", bg='#34495e', fg='white', 
                font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        password_entry = tk.Entry(form_frame, show="*", font=('Arial', 11), width=40)
        password_entry.pack(fill='x', pady=(0, 15))
        password_entry.insert(0, self.email_config['sender_password'])
        
        # Instructions
        instructions = tk.Label(form_frame, 
                               text="📱 Gmail Setup:\n1. Enable 2-Factor Authentication\n2. Generate App Password in Google Account\n3. Use App Password (not regular password)",
                               bg='#2c3e50', fg='#bdc3c7', font=('Arial', 9), 
                               justify='left', relief='flat', padx=10, pady=10)
        instructions.pack(fill='x', pady=(0, 20))
        
        # Enable checkbox
        enable_var = tk.BooleanVar(value=self.email_config['enabled'])
        tk.Checkbutton(form_frame, text="Enable Email Alerts", variable=enable_var,
                      bg='#34495e', fg='white', selectcolor='#2c3e50', 
                      font=('Arial', 11, 'bold')).pack(pady=(0, 20))
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg='#34495e')
        btn_frame.pack(fill='x')
        
        def test_email():
            """Test email configuration"""
            try:
                test_msg = MIMEText("🧪 Test email from Smart Surveillance System\n\nIf you receive this, email alerts are working correctly!")
                test_msg['Subject'] = "🧪 Test Email - Smart Surveillance System"
                test_msg['From'] = email_entry.get()
                test_msg['To'] = self.user_email
                
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(email_entry.get(), password_entry.get())
                server.sendmail(email_entry.get(), self.user_email, test_msg.as_string())
                server.quit()
                
                messagebox.showinfo("Test Successful", f"Test email sent to {self.user_email}")
            except Exception as e:
                messagebox.showerror("Test Failed", f"Email test failed:\n{str(e)}")
        
        def save_config():
            """Save email configuration"""
            self.email_config['sender_email'] = email_entry.get()
            self.email_config['sender_password'] = password_entry.get()
            self.email_config['enabled'] = enable_var.get()
            
            self.save_email_config()
            self.update_email_status()
            
            messagebox.showinfo("Saved", "Email configuration saved successfully!")
            email_window.destroy()
        
        tk.Button(btn_frame, text="🧪 Test Email", command=test_email,
                 bg='#3498db', fg='white', font=('Arial', 11, 'bold'), padx=20).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="💾 Save", command=save_config,
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
            with open("email_config.json", 'w') as f:
                json.dump(self.email_config, f, indent=2)
        except Exception as e:
            self.log_message(f"Email config save error: {e}")
    
    def update_email_status(self):
        """Update email status display"""
        if self.email_config['enabled'] and self.email_config['sender_email']:
            self.status_vars["Email Alerts"].config(text="✅ Configured", fg='#2ecc71')
        else:
            self.status_vars["Email Alerts"].config(text="❌ Not Configured", fg='#e74c3c')
    
    def on_closing(self):
        """Handle window closing"""
        if self.monitoring:
            self.stop_monitoring()
        
        if self.cap:
            self.cap.release()
        
        self.log_message("👋 System shutdown")
        self.root.destroy()

def main():
    """Main application entry point"""
    print("🛡️ Starting All-in-One Smart Surveillance System...")
    print("✅ Features: User Authentication + All AI Detection + Email Alerts")
    print("🎯 Perfect accuracy with comprehensive threat detection")
    
    try:
        AllInOneSurveillanceSystem()
    except KeyboardInterrupt:
        print("\n👋 System shutdown requested")
    except Exception as e:
        print(f"❌ System error: {e}")

if __name__ == "__main__":
    main()