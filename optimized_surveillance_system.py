#!/usr/bin/env python3
"""
🛡️ OPTIMIZED SMART SURVEILLANCE SYSTEM
✅ Fast Processing + Stable Boxes + Fixed Email + Better Performance
OPTIMIZED VERSION - ALL ISSUES FIXED
"""

import cv2
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import threading
import time
import datetime
import json
import sqlite3
import hashlib
import smtplib
from PIL import Image, ImageTk
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os

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
        self.db_path = "data/surveillance_system.db"
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
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
                user_email TEXT,
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
    
    def create_user(self, email, password):
        """Create new user account"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash)
            )
            
            conn.commit()
            conn.close()
            return True, "Account created successfully"
        
        except sqlite3.IntegrityError:
            return False, "Email already exists"
        except Exception as e:
            return False, f"Error creating account: {str(e)}"
    
    def verify_user(self, email, password):
        """Verify user login credentials"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute(
                "SELECT id, email FROM users WHERE email = ? AND password_hash = ?",
                (email, password_hash)
            )
            
            user = cursor.fetchone()
            
            if user:
                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (user[0],)
                )
                conn.commit()
            
            conn.close()
            return user
        
        except Exception as e:
            print(f"Database error: {e}")
            return None
    
    def create_session(self, user_id, user_email):
        """Create new session for authenticated user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO sessions (user_id, user_email) VALUES (?, ?)",
                (user_id, user_email)
            )
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return session_id
        
        except Exception as e:
            print(f"Session creation error: {e}")
            return None
    
    def log_detection(self, user_id, user_email, session_id, detection_type, confidence, description):
        """Log detection event to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO detections 
                (user_id, user_email, session_id, detection_type, confidence, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, user_email, session_id, detection_type, confidence, description))
            
            detection_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return detection_id
        
        except Exception as e:
            print(f"Detection logging error: {e}")
            return None
    
    def mark_email_sent(self, detection_id):
        """Mark that email alert was sent for detection"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE detections SET email_sent = TRUE WHERE id = ?",
                (detection_id,)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Email marking error: {e}")
    
    def mark_beep_played(self, detection_id):
        """Mark that beep sound was played for detection"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE detections SET beep_played = TRUE WHERE id = ?",
                (detection_id,)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Beep marking error: {e}")

class AuthenticationWindow:
    """User authentication interface"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🛡️ Smart Surveillance System - Login")
        self.root.geometry("500x400")
        self.root.configure(bg='#2c3e50')
        
        # Center window
        self.center_window()
        
        self.db_manager = DatabaseManager()
        self.authenticated_user = None
        
        self.create_ui()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"500x400+{x}+{y}")
    
    def create_ui(self):
        """Create authentication interface"""
        # Title
        title_label = tk.Label(
            self.root, text="🛡️ Smart Surveillance System", 
            font=("Arial", 18, "bold"), fg='white', bg='#2c3e50'
        )
        title_label.pack(pady=20)
        
        # Subtitle
        subtitle_label = tk.Label(
            self.root, text="Secure Authentication Required", 
            font=("Arial", 12), fg='#bdc3c7', bg='#2c3e50'
        )
        subtitle_label.pack(pady=5)
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#34495e', padx=30, pady=30)
        main_frame.pack(pady=30, padx=50, fill='both', expand=True)
        
        # Email field
        tk.Label(main_frame, text="📧 Email:", font=("Arial", 11, "bold"), 
                fg='white', bg='#34495e').pack(anchor='w', pady=(0, 5))
        
        self.email_entry = tk.Entry(main_frame, font=("Arial", 11), width=35, 
                                   relief='flat', bd=5)
        self.email_entry.pack(pady=(0, 15), ipady=8)
        
        # Password field
        tk.Label(main_frame, text="🔒 Password:", font=("Arial", 11, "bold"), 
                fg='white', bg='#34495e').pack(anchor='w', pady=(0, 5))
        
        self.password_entry = tk.Entry(main_frame, font=("Arial", 11), width=35, 
                                      show="*", relief='flat', bd=5)
        self.password_entry.pack(pady=(0, 20), ipady=8)
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg='#34495e')
        button_frame.pack(pady=10)
        
        # Login button
        login_btn = tk.Button(
            button_frame, text="🔐 Login", font=("Arial", 11, "bold"),
            bg='#27ae60', fg='white', padx=20, pady=8,
            relief='flat', cursor='hand2', command=self.login
        )
        login_btn.pack(side='left', padx=(0, 10))
        
        # Register button
        register_btn = tk.Button(
            button_frame, text="📝 Register", font=("Arial", 11, "bold"),
            bg='#3498db', fg='white', padx=20, pady=8,
            relief='flat', cursor='hand2', command=self.register
        )
        register_btn.pack(side='left')
        
        # Bind Enter key to login
        self.root.bind('<Return>', lambda e: self.login())
        
    def login(self):
        """Handle user login"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password")
            return
        
        user = self.db_manager.verify_user(email, password)
        if user:
            self.authenticated_user = {
                'id': user[0],
                'email': user[1],
                'session_id': self.db_manager.create_session(user[0], user[1])
            }
            messagebox.showinfo("Success", f"Welcome back, {email}!")
            self.root.quit()
            self.root.destroy()
        else:
            messagebox.showerror("Error", "Invalid email or password")
            self.password_entry.delete(0, tk.END)
    
    def register(self):
        """Handle user registration"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password")
            return
        
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return
        
        if '@' not in email or '.' not in email:
            messagebox.showerror("Error", "Please enter a valid email address")
            return
        
        success, message = self.db_manager.create_user(email, password)
        
        if success:
            messagebox.showinfo("Success", message + "\nYou can now login")
            self.password_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", message)
    
    def run(self):
        """Run authentication window"""
        self.root.mainloop()
        return self.authenticated_user

class OptimizedSurveillanceSystem:
    """Optimized surveillance system with improved performance"""
    
    def __init__(self, user_info):
        # User information
        self.user_id = user_info['id']
        self.user_email = user_info['email'] 
        self.session_id = user_info['session_id']
        
        # Initialize database
        self.db_manager = DatabaseManager()
        
        # System state
        self.monitoring = False
        self.camera = None
        self.camera_type = "laptop"  # "laptop" or "ip"
        self.ip_url = ""
        
        # AI Models - Load on demand for better performance
        self.models = {}
        self.models_loaded = {'weapon': False, 'crowd': False, 'expression': False}
        
        # Performance optimization
        self.frame_skip = 2  # Process every 2nd frame for better speed
        self.frame_count = 0
        self.detection_cache = {}  # Cache recent detections
        self.box_display_time = 3.0  # Keep boxes visible for 3 seconds
        self.active_detections = {}  # Track active detections with timestamps
        
        # Alert system
        self.last_alert_time = {}
        self.alert_cooldown = 3  # Reduced from 5 to 3 seconds
        
        # Statistics
        self.stats = {
            'detections_total': 0,
            'weapons_detected': 0, 
            'people_count': 0,
            'faces_analyzed': 0,
            'threats_blocked': 0,
            'emails_sent': 0,
            'beeps_played': 0
        }
        
        # UI setup
        self.setup_ui()
        self.load_ai_models()
        
    def setup_ui(self):
        """Create optimized user interface"""
        self.root = tk.Tk()
        self.root.title("🛡️ Optimized Smart Surveillance System")
        self.root.geometry("1400x800")
        self.root.configure(bg='#2c3e50')
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Top control panel
        self.create_control_panel(main_frame)
        
        # Content area
        content_frame = tk.Frame(main_frame, bg='#2c3e50')
        content_frame.pack(fill='both', expand=True, pady=5)
        
        # Video display
        self.create_video_display(content_frame)
        
        # Side panel
        self.create_side_panel(content_frame)
        
    def create_control_panel(self, parent):
        """Create control panel"""
        control_frame = tk.Frame(parent, bg='#34495e', height=80)
        control_frame.pack(fill='x', pady=(0, 5))
        control_frame.pack_propagate(False)
        
        # User info
        user_info = tk.Label(
            control_frame, text=f"👤 User: {self.user_email} | 🤖 AI Models: Loading... | 🚨 Alerts: ON",
            font=("Arial", 10, "bold"), fg='white', bg='#34495e'
        )
        user_info.pack(side='left', padx=15, pady=20)
        
        # Control buttons
        button_frame = tk.Frame(control_frame, bg='#34495e')
        button_frame.pack(side='right', padx=15, pady=15)
        
        # Start/Stop monitoring
        self.monitor_btn = tk.Button(
            button_frame, text="🟢 Start Monitoring", font=("Arial", 10, "bold"),
            bg='#27ae60', fg='white', padx=15, pady=8, relief='flat',
            cursor='hand2', command=self.toggle_monitoring
        )
        self.monitor_btn.pack(side='left', padx=5)
        
        # Camera selection
        camera_btn = tk.Button(
            button_frame, text="📱 Select Camera", font=("Arial", 10, "bold"),
            bg='#3498db', fg='white', padx=15, pady=8, relief='flat',
            cursor='hand2', command=self.select_camera
        )
        camera_btn.pack(side='left', padx=5)
        
        # Email test
        email_btn = tk.Button(
            button_frame, text="📧 Test Email", font=("Arial", 10, "bold"),
            bg='#e67e22', fg='white', padx=15, pady=8, relief='flat',
            cursor='hand2', command=self.test_email_connection
        )
        email_btn.pack(side='left', padx=5)
        
        # Save screenshot
        save_btn = tk.Button(
            button_frame, text="💾 Save Screenshot", font=("Arial", 10, "bold"),
            bg='#9b59b6', fg='white', padx=15, pady=8, relief='flat',
            cursor='hand2', command=self.save_screenshot
        )
        save_btn.pack(side='left', padx=5)
        
    def create_video_display(self, parent):
        """Create video display area"""
        video_frame = tk.Frame(parent, bg='#34495e', relief='solid', bd=2)
        video_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Video label
        self.video_label = tk.Label(video_frame, bg='black', text="📹 Video Feed\n\nClick 'Start Monitoring' to begin",
                                   font=("Arial", 14), fg='white')
        self.video_label.pack(fill='both', expand=True, padx=5, pady=5)
        
    def create_side_panel(self, parent):
        """Create side information panel"""
        side_frame = tk.Frame(parent, bg='#34495e', width=350, relief='solid', bd=2)
        side_frame.pack(side='right', fill='y')
        side_frame.pack_propagate(False)
        
        # Statistics panel
        stats_frame = tk.LabelFrame(side_frame, text="📊 REAL-TIME STATISTICS", 
                                   font=("Arial", 11, "bold"), fg='white', bg='#34495e')
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_labels = {}
        stats_items = [
            ("🔫 Weapons Detected", "0"),
            ("👥 People Count", "0"), 
            ("😊 Faces Analyzed", "0"),
            ("🚨 Total Threats", "0"),
            ("📧 Emails Sent", "0"),
            ("🔊 Alert Beeps", "0")
        ]
        
        for label, value in stats_items:
            row_frame = tk.Frame(stats_frame, bg='#34495e')
            row_frame.pack(fill='x', padx=10, pady=3)
            
            tk.Label(row_frame, text=label, font=("Arial", 9), 
                    fg='white', bg='#34495e').pack(side='left')
            
            value_label = tk.Label(row_frame, text=value, font=("Arial", 9, "bold"), 
                                  fg='#e74c3c', bg='#34495e')
            value_label.pack(side='right')
            self.stats_labels[label] = value_label
        
        # Activity log
        log_frame = tk.LabelFrame(side_frame, text="🚨 ACTIVITY LOG", 
                                 font=("Arial", 11, "bold"), fg='white', bg='#34495e')
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.activity_log = scrolledtext.ScrolledText(
            log_frame, height=20, width=40, font=("Consolas", 9),
            bg='#2c3e50', fg='white', insertbackground='white'
        )
        self.activity_log.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Initial log message
        self.log_message("🛡️ System initialized")
        self.log_message(f"✅ User authenticated: {self.user_email}")
        
    def load_ai_models(self):
        """Load AI models with better error handling"""
        self.log_message("🤖 Loading AI models...")
        
        # Try to load models in separate thread to avoid UI blocking
        threading.Thread(target=self._load_models_thread, daemon=True).start()
    
    def _load_models_thread(self):
        """Load models in background thread"""
        try:
            # Weapon detection model
            if YOLO_AVAILABLE:
                weapon_paths = [
                    "AI_models/Object_detection/best.pt",
                    "Object_detection/best.pt",
                    "best.pt"
                ]
                
                for path in weapon_paths:
                    if os.path.exists(path):
                        try:
                            self.models['weapon'] = YOLO(path)
                            self.models_loaded['weapon'] = True
                            self.log_message(f"✅ Weapon detection model loaded: {path}")
                            break
                        except Exception:
                            continue
                
                # Crowd detection  
                crowd_paths = [
                    "AI_models/crowddetection/yolov8s.pt",
                    "AI_models/crowddetection/yolov8n.pt",
                    "crowddetection/yolov8s.pt",
                    "crowddetection/yolov8n.pt"
                ]
                
                for path in crowd_paths:
                    if os.path.exists(path):
                        try:
                            self.models['crowd'] = YOLO(path)
                            self.models_loaded['crowd'] = True
                            self.log_message(f"✅ Crowd detection model loaded: {path}")
                            break
                        except Exception:
                            continue
            
            # Facial expression model
            if FER_AVAILABLE:
                try:
                    self.models['expression'] = FER(mtcnn=True)
                    self.models_loaded['expression'] = True
                    self.log_message("✅ Facial expression model loaded")
                except Exception as e:
                    self.log_message(f"⚠️ FER model failed: {e}")
            
            # Update UI
            models_count = sum(1 for loaded in self.models_loaded.values() if loaded)
            self.root.after(0, lambda: self.log_message(f"🚀 {models_count}/3 AI models ready"))
            
        except Exception as model_error:
            error_msg = f"❌ Model loading error: {model_error}"
            self.root.after(0, lambda: self.log_message(error_msg))
    
    def select_camera(self):
        """Enhanced camera selection with better IP webcam support"""
        choice = messagebox.askyesnocancel(
            "Camera Selection",
            "Choose camera type:\n\n• Yes: Mobile IP Webcam (wireless)\n• No: Laptop Camera\n• Cancel: Keep current"
        )
        
        if choice is True:  # IP Webcam
            self.camera_type = "ip"
            ip = simpledialog.askstring(
                "IP Webcam Setup", 
                "Enter phone IP address:\n(Find in IP Webcam app)\n\nFormat: 192.168.x.x",
                initialvalue="192.168.0.106"
            )
            
            if ip:
                # Try different common ports
                ports = ["8080", "8081", "4747"]
                for port in ports:
                    test_url = f"http://{ip}:{port}/video"
                    self.log_message(f"🔍 Testing: {test_url}")
                    
                    # Quick connection test
                    import urllib.request
                    try:
                        urllib.request.urlopen(test_url, timeout=3)
                        self.ip_url = test_url
                        self.log_message(f"✅ IP webcam configured: {self.ip_url}")
                        return
                    except:
                        continue
                
                self.log_message("❌ Could not connect to IP webcam")
                messagebox.showerror("Connection Failed", 
                    f"Could not connect to {ip}\n\nPlease check:\n• Phone and computer on same Wi-Fi\n• IP Webcam app is running\n• Correct IP address")
        
        elif choice is False:  # Laptop camera
            self.camera_type = "laptop"
            self.log_message("✅ Laptop camera selected")
        
    def test_email_connection(self):
        """Test email configuration with better error handling"""
        self.log_message("📧 Testing email connection...")
        
        # Load email config
        config_path = "configs/email_config.json"
        if not os.path.exists(config_path):
            messagebox.showerror("Email Error", 
                f"Email configuration not found!\n\nPlease create: {config_path}\n\nWith your Gmail credentials:\n{{\n  \"email\": \"your@gmail.com\",\n  \"password\": \"your_app_password\"\n}}")
            return
        
        try:
            with open(config_path, 'r') as f:
                email_config = json.load(f)
            
            # Test connection
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email_config['email'], email_config['password'])
            server.quit()
            
            self.log_message("✅ Email connection successful")
            messagebox.showinfo("Email Test", "Email connection successful!\nAlerts will be sent to your registered email.")
            
        except FileNotFoundError:
            messagebox.showerror("Configuration Error", "Email configuration file not found")
        except json.JSONDecodeError:
            messagebox.showerror("Configuration Error", "Invalid email configuration format")
        except smtplib.SMTPAuthenticationError:
            messagebox.showerror("Authentication Error", 
                "Gmail authentication failed!\n\nPlease:\n1. Enable 2FA on Gmail\n2. Generate App Password\n3. Use App Password in config file")
        except Exception as e:
            messagebox.showerror("Email Error", f"Email test failed: {str(e)}")
            self.log_message(f"❌ Email test failed: {e}")
    
    def toggle_monitoring(self):
        """Start/stop monitoring with better performance"""
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """Start surveillance monitoring"""
        self.log_message("🚀 Starting surveillance...")
        
        # Initialize camera
        if not self.init_camera():
            return
        
        self.monitoring = True
        self.monitor_btn.config(text="⏹️ Stop Monitoring", bg='#e74c3c')
        
        # Start processing in separate thread
        self.processing_thread = threading.Thread(target=self.process_video, daemon=True)
        self.processing_thread.start()
        
        self.log_message("🟢 Monitoring started!")
    
    def init_camera(self):
        """Initialize camera with better error handling"""
        try:
            if self.camera_type == "ip":
                if not self.ip_url:
                    self.select_camera()
                    if not self.ip_url:
                        return False
                
                self.camera = cv2.VideoCapture(self.ip_url)
                self.log_message(f"📱 IP webcam connected: {self.ip_url}")
                
            else:  # Laptop camera
                # Try different camera indices
                for i in [0, 1, 2]:
                    self.camera = cv2.VideoCapture(i)
                    if self.camera.isOpened():
                        self.log_message(f"💻 Laptop camera connected (index {i})")
                        break
                else:
                    messagebox.showerror("Camera Error", "No camera found")
                    return False
            
            # Set camera properties for better performance
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            return self.camera.isOpened()
            
        except Exception as e:
            self.log_message(f"❌ Camera initialization failed: {e}")
            messagebox.showerror("Camera Error", f"Failed to initialize camera: {e}")
            return False
    
    def process_video(self):
        """Optimized video processing loop"""
        while self.monitoring:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    self.log_message("❌ Camera connection lost")
                    break
                
                # Frame skipping for better performance
                self.frame_count += 1
                if self.frame_count % self.frame_skip != 0:
                    continue
                
                # Process AI detection on every nth frame only
                if self.frame_count % (self.frame_skip * 3) == 0:
                    detection_results = self.detect_threats(frame)
                    self.handle_detections(detection_results, frame)
                
                # Draw persistent detection boxes
                frame = self.draw_detection_boxes(frame)
                
                # Update UI
                self.update_video_display(frame)
                self.update_statistics()
                
                # Small delay to prevent overloading
                time.sleep(0.03)  # ~33 FPS max
                
            except Exception as e:
                self.log_message(f"❌ Processing error: {e}")
                break
        
        # Cleanup
        if self.camera:
            self.camera.release()
        self.monitoring = False
        self.monitor_btn.config(text="🟢 Start Monitoring", bg='#27ae60')
    
    def detect_threats(self, frame):
        """Optimized threat detection"""
        results = {
            'weapons': [],
            'people': [],
            'faces': []
        }
        
        try:
            # Weapon detection
            if 'weapon' in self.models:
                weapon_results = self.models['weapon'](frame, verbose=False, conf=0.6)
                for result in weapon_results:
                    if result.boxes is not None:
                        for box, cls, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                            results['weapons'].append({
                                'class': int(cls),
                                'confidence': float(conf),
                                'bbox': [int(x) for x in box]
                            })
            
            # People/crowd detection
            if 'crowd' in self.models:
                people_results = self.models['crowd'](frame, verbose=False, conf=0.5)
                for result in people_results:
                    if result.boxes is not None:
                        for box, cls in zip(result.boxes.xyxy, result.boxes.cls):
                            if int(cls) == 0:  # Person class
                                results['people'].append([int(x) for x in box])
            
            # Facial expression detection (less frequent)
            if 'expression' in self.models and self.frame_count % 10 == 0:
                try:
                    emotion_results = self.models['expression'].detect_emotions(frame)
                    if emotion_results:
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
            self.log_message(f"❌ Detection error: {e}")
        
        return results
    
    def handle_detections(self, results, frame):
        """Handle threat detections with optimized alerting"""
        current_time = time.time()
        
        # Handle weapon threats (CRITICAL)
        if results['weapons']:
            weapon_count = len(results['weapons'])
            if 'weapon' not in self.last_alert_time or current_time - self.last_alert_time['weapon'] > self.alert_cooldown:
                threat_message = f"🔫 CRITICAL: {weapon_count} weapons detected!"
                
                # Log to database
                detection_id = self.db_manager.log_detection(
                    self.user_id, self.user_email, self.session_id,
                    "weapon", 0.95,
                    f"Critical weapon threat: {weapon_count} weapons detected"
                )
                
                # Play weapon beep sound
                self.play_beep_sound("weapon")
                self.db_manager.mark_beep_played(detection_id)
                self.stats['beeps_played'] += 1
                
                # Send email alert
                self.send_email_alert(detection_id, "weapon", threat_message, frame)
                
                self.log_message(threat_message)
                self.last_alert_time['weapon'] = current_time
                self.stats['threats_blocked'] += 1
        
        # Handle crowd threats (HIGH)
        people_count = len(results['people'])
        if people_count > 5:  # Updated threshold
            if 'crowd' not in self.last_alert_time or current_time - self.last_alert_time['crowd'] > self.alert_cooldown:
                threat_message = f"👥 CROWD ALERT: {people_count} people detected!"
                
                # Log to database
                detection_id = self.db_manager.log_detection(
                    self.user_id, self.user_email, self.session_id,
                    "crowd", 0.9,
                    f"Large crowd of {people_count} people detected"
                )
                
                # Play crowd beep sound
                self.play_beep_sound("crowd")
                self.db_manager.mark_beep_played(detection_id)
                self.stats['beeps_played'] += 1
                
                # Send email alert
                self.send_email_alert(detection_id, "crowd", threat_message, frame)
                
                self.log_message(threat_message)
                self.last_alert_time['crowd'] = current_time
        
        # Handle suspicious behavior (MEDIUM)
        suspicious_faces = [face for face in results['faces'] 
                          if face['emotion'] in ['angry', 'fear'] and face['confidence'] > 0.7]
        
        if suspicious_faces:
            if 'behavior' not in self.last_alert_time or current_time - self.last_alert_time['behavior'] > self.alert_cooldown:
                threat_message = "😠 BEHAVIOR: Suspicious emotions detected!"
                
                # Log to database
                detection_id = self.db_manager.log_detection(
                    self.user_id, self.user_email, self.session_id,
                    "behavior", 0.8,
                    f"Suspicious behavior: {len(suspicious_faces)} concerning expressions"
                )
                
                # Play behavior beep sound
                self.play_beep_sound("behavior")
                self.db_manager.mark_beep_played(detection_id)
                self.stats['beeps_played'] += 1
                
                # Send email alert
                self.send_email_alert(detection_id, "behavior", threat_message, frame)
                
                self.log_message(threat_message)
                self.last_alert_time['behavior'] = current_time
        
        # Update active detections for persistent display
        if results['weapons'] or results['people'] or results['faces']:
            self.active_detections = {
                'timestamp': current_time,
                'weapons': results['weapons'],
                'people': results['people'],
                'faces': results['faces']
            }
    
    def draw_detection_boxes(self, frame):
        """Draw persistent detection boxes"""
        current_time = time.time()
        
        # Check if we have recent detections to display
        if (hasattr(self, 'active_detections') and self.active_detections and
            current_time - self.active_detections['timestamp'] < self.box_display_time):
            
            detections = self.active_detections
            
            # Draw weapon boxes (RED)
            for weapon in detections['weapons']:
                bbox = weapon['bbox']
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 3)
                cv2.putText(frame, f"WEAPON {weapon['confidence']:.2f}", 
                           (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            
            # Draw people boxes (GREEN)
            for person_bbox in detections['people']:
                cv2.rectangle(frame, (person_bbox[0], person_bbox[1]), 
                             (person_bbox[2], person_bbox[3]), (0, 255, 0), 2)
                cv2.putText(frame, "PERSON", 
                           (person_bbox[0], person_bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            # Draw face emotion boxes (BLUE)
            for face in detections['faces']:
                bbox = face['bbox']
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
                cv2.putText(frame, f"{face['emotion'].upper()}", 
                           (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return frame
    
    def update_video_display(self, frame):
        """Update video display efficiently"""
        # Resize for display
        height, width = frame.shape[:2]
        if width > 800:
            scale = 800 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        # Convert to PhotoImage
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        photo = ImageTk.PhotoImage(image)
        
        # Update display
        self.video_label.config(image=photo, text="")
        self.video_label.image = photo
    
    def update_statistics(self):
        """Update statistics display"""
        stats_mapping = {
            "🔫 Weapons Detected": str(self.stats['weapons_detected']),
            "👥 People Count": str(self.stats['people_count']),
            "😊 Faces Analyzed": str(self.stats['faces_analyzed']),
            "🚨 Total Threats": str(self.stats['threats_blocked']),
            "📧 Emails Sent": str(self.stats['emails_sent']),
            "🔊 Alert Beeps": str(self.stats['beeps_played'])
        }
        
        for label, value in stats_mapping.items():
            if label in self.stats_labels:
                self.stats_labels[label].config(text=value)
    
    def play_beep_sound(self, threat_type):
        """Play differentiated beep sounds"""
        if not SOUND_AVAILABLE:
            return
        
        def play_sound():
            try:
                if threat_type == "weapon":
                    # 5 rapid high-pitched beeps for weapons
                    for _ in range(5):
                        winsound.Beep(1500, 200)
                        time.sleep(0.1)
                elif threat_type == "crowd":
                    # 3 medium-pitched beeps for crowds
                    for _ in range(3):
                        winsound.Beep(1000, 300)
                        time.sleep(0.2)
                elif threat_type == "behavior":
                    # 2 low-pitched beeps for behavior
                    for _ in range(2):
                        winsound.Beep(800, 400)
                        time.sleep(0.3)
                
                self.log_message(f"🔊 {threat_type.upper()} beep alert played")
                
            except Exception as e:
                self.log_message(f"❌ Sound error: {e}")
        
        # Play sound in separate thread to avoid blocking
        sound_thread = threading.Thread(target=play_sound, daemon=True)
        sound_thread.start()
    
    def send_email_alert(self, detection_id, threat_type, message, frame):
        """Send optimized email alerts"""
        def send_email():
            try:
                # Load email configuration
                config_path = "configs/email_config.json"
                if not os.path.exists(config_path):
                    self.log_message("❌ Email config not found")
                    return
                
                with open(config_path, 'r') as f:
                    email_config = json.load(f)
                
                # Create email
                msg = MIMEMultipart()
                msg['From'] = email_config['email']
                msg['To'] = self.user_email
                msg['Subject'] = f"🚨 SECURITY ALERT: {threat_type.upper()}"
                
                # Email body
                priority = {"weapon": "CRITICAL", "crowd": "HIGH", "behavior": "MEDIUM"}
                body = f"""
                <html>
                <body>
                <h2>🛡️ Security Alert</h2>
                <p><strong>Threat Level:</strong> <span style="color: red;">{priority.get(threat_type, 'MEDIUM')}</span></p>
                <p><strong>Detection:</strong> {message}</p>
                <p><strong>Time:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>User:</strong> {self.user_email}</p>
                <p><strong>System:</strong> Smart Surveillance System</p>
                <hr>
                <p><em>Evidence screenshot attached.</em></p>
                </body>
                </html>
                """
                
                msg.attach(MIMEText(body, 'html'))
                
                # Attach screenshot
                os.makedirs("alerts/screenshots", exist_ok=True)
                screenshot_path = f"alerts/screenshots/alert_{int(time.time())}.jpg"
                cv2.imwrite(screenshot_path, frame)
                
                with open(screenshot_path, "rb") as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-Disposition', 'attachment', filename="evidence.jpg")
                    msg.attach(img)
                
                # Send email
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(email_config['email'], email_config['password'])
                server.send_message(msg)
                server.quit()
                
                # Mark as sent
                self.db_manager.mark_email_sent(detection_id)
                self.stats['emails_sent'] += 1
                self.log_message(f"✅ Email alert sent: {threat_type}")
                
            except Exception as e:
                self.log_message(f"❌ Email failed: {e}")
        
        # Send email in separate thread
        email_thread = threading.Thread(target=send_email, daemon=True)
        email_thread.start()
    
    def save_screenshot(self):
        """Save current video frame"""
        if hasattr(self, 'camera') and self.camera:
            ret, frame = self.camera.read()
            if ret:
                os.makedirs("alerts/screenshots", exist_ok=True)
                filename = f"alerts/screenshots/manual_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                self.log_message(f"💾 Screenshot saved: {filename}")
                messagebox.showinfo("Screenshot", f"Screenshot saved:\n{filename}")
    
    def stop_monitoring(self):
        """Stop surveillance monitoring"""
        self.monitoring = False
        self.log_message("⏹️ Monitoring stopped")
    
    def log_message(self, message):
        """Add message to activity log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Update UI in main thread
        if hasattr(self, 'activity_log'):
            self.activity_log.insert(tk.END, log_entry)
            self.activity_log.see(tk.END)
    
    def run(self):
        """Run the surveillance system"""
        self.root.mainloop()

def main():
    """Main function - Updated with optimization"""
    print("🛡️ Starting Optimized Smart Surveillance System...")
    
    # User authentication
    auth = AuthenticationWindow()
    user_info = auth.run()
    
    if not user_info:
        print("❌ Authentication failed or cancelled")
        return
    
    print(f"✅ User authenticated: {user_info['email']}")
    
    # Start surveillance system
    app = OptimizedSurveillanceSystem(user_info)
    app.run()

if __name__ == "__main__":
    main()