#!/usr/bin/env python3
"""
🛡️ Authenticated Smart Surveillance System
Complete system with user login, automatic email alerts, and data logging
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

# Import detection libraries
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

# Email libraries
try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

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
                image_path TEXT,
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
    
    def log_detection(self, user_id, session_id, detection_type, confidence=0.0, description="", image_path=""):
        """Log threat detection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO detections 
               (user_id, session_id, detection_type, confidence, description, image_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, session_id, detection_type, confidence, description, image_path)
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
    
    def get_session_stats(self, user_id):
        """Get session statistics for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT COUNT(*) as total_sessions, 
                      AVG(duration_minutes) as avg_duration,
                      MAX(login_time) as last_session
               FROM sessions WHERE user_id = ? AND logout_time IS NOT NULL""",
            (user_id,)
        )
        
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_detection_stats(self, user_id):
        """Get detection statistics for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT detection_type, COUNT(*) as count
               FROM detections WHERE user_id = ?
               GROUP BY detection_type
               ORDER BY count DESC""",
            (user_id,)
        )
        
        results = cursor.fetchall()
        conn.close()
        return results

class LoginWindow:
    """User authentication window"""
    
    def __init__(self, db_manager, on_success_callback):
        self.db_manager = db_manager
        self.on_success_callback = on_success_callback
        self.user_id = None
        self.user_email = None
        
        self.root = tk.Tk()
        self.root.title("🔐 Surveillance System Login")
        self.root.geometry("400x300")
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

class AuthenticatedSurveillanceSystem:
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
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize variables
        self.cap = None
        self.monitoring = False
        self.frame_queue = queue.Queue(maxsize=10)
        self.detection_queue = queue.Queue()
        
        # Load AI models (lazy loading)
        self.models = {}
        self.load_models()
        
        # Setup UI
        self.setup_ui()
        
        # Start detection thread
        self.detection_thread = threading.Thread(target=self.detection_worker, daemon=True)
        self.detection_thread.start()
        
        # Log system start
        self.db_manager.log_system_action(
            self.user_id, 
            "SYSTEM_START", 
            f"Surveillance system started for session {self.session_id}"
        )
        
        # Run main loop
        self.root.mainloop()
    
    def load_models(self):
        """Load AI models with error handling"""
        self.log_message("🔄 Loading AI models...")
        
        # Load weapon detection model
        try:
            if YOLO_AVAILABLE:
                weapon_model_path = Path("Object_detection/best.pt")
                if weapon_model_path.exists():
                    self.models['weapon'] = YOLO(str(weapon_model_path))
                    self.log_message("✅ Weapon detection model loaded")
                else:
                    self.log_message("⚠️ Weapon detection model not found")
        except Exception as e:
            self.log_message(f"❌ Failed to load weapon model: {e}")
        
        # Load crowd detection model
        try:
            if YOLO_AVAILABLE:
                crowd_model_path = Path("crowddetection/yolov8n.pt")
                if crowd_model_path.exists():
                    self.models['crowd'] = YOLO(str(crowd_model_path))
                    self.log_message("✅ Crowd detection model loaded")
                else:
                    self.log_message("⚠️ Crowd detection model not found")
        except Exception as e:
            self.log_message(f"❌ Failed to load crowd model: {e}")
        
        # Load facial expression model
        try:
            if FER_AVAILABLE:
                self.models['emotion'] = FER(mtcnn=True)
                self.log_message("✅ Facial expression model loaded")
        except Exception as e:
            self.log_message(f"❌ Failed to load emotion model: {e}")
        
        self.log_message(f"🎯 Loaded {len(self.models)} AI models successfully")
    
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
        
        # Middle frame - video and controls
        middle_frame = tk.Frame(main_frame, bg='#2c3e50')
        middle_frame.pack(fill='both', expand=True)
        
        # Left panel - video
        video_frame = tk.Frame(middle_frame, bg='#34495e')
        video_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # IP Camera connection
        ip_frame = tk.Frame(video_frame, bg='#34495e', height=60)
        ip_frame.pack(fill='x', padx=10, pady=10)
        ip_frame.pack_propagate(False)
        
        tk.Label(ip_frame, text="📱 IP Camera URL:", bg='#34495e', fg='white', font=('Arial', 10)).pack(side='left', padx=5)
        
        self.ip_entry = tk.Entry(ip_frame, font=('Arial', 10), width=30)
        self.ip_entry.pack(side='left', padx=5)
        self.ip_entry.insert(0, "http://192.168.1.100:8080/video")
        
        connect_btn = tk.Button(
            ip_frame,
            text="🔗 Connect",
            command=self.connect_camera,
            bg='#3498db',
            fg='white',
            font=('Arial', 9, 'bold')
        )
        connect_btn.pack(side='left', padx=5)
        
        # Video display
        self.video_label = tk.Label(video_frame, bg='black', text="No video feed", fg='white')
        self.video_label.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Right panel - logs and statistics
        right_panel = tk.Frame(middle_frame, bg='#34495e', width=400)
        right_panel.pack(side='right', fill='y')
        right_panel.pack_propagate(False)
        
        # Notebook for tabs
        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Logs tab
        logs_frame = tk.Frame(notebook, bg='#34495e')
        notebook.add(logs_frame, text="📝 Activity Logs")
        
        self.log_text = scrolledtext.ScrolledText(
            logs_frame,
            bg='#2c3e50',
            fg='white',
            font=('Consolas', 9),
            wrap=tk.WORD
        )
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Statistics tab
        stats_frame = tk.Frame(notebook, bg='#34495e')
        notebook.add(stats_frame, text="📊 Statistics")
        
        self.stats_text = scrolledtext.ScrolledText(
            stats_frame,
            bg='#2c3e50',
            fg='white',
            font=('Consolas', 9),
            wrap=tk.WORD,
            state='disabled'
        )
        self.stats_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Update stats periodically
        self.update_stats()
        
        # Initial log message
        self.log_message(f"🚀 System initialized for user: {self.user_email}")
        self.log_message("📋 Connect to your IP camera to start monitoring")
    
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
    
    def update_stats(self):
        """Update statistics display"""
        try:
            if self.user_id:
                # Get session stats
                session_stats = self.db_manager.get_session_stats(self.user_id)
                detection_stats = self.db_manager.get_detection_stats(self.user_id)
                
                # Update display
                self.stats_text.config(state='normal')
                self.stats_text.delete(1.0, tk.END)
                
                self.stats_text.insert(tk.END, "📊 USER STATISTICS\n")
                self.stats_text.insert(tk.END, "=" * 30 + "\n\n")
                
                if session_stats and session_stats[0]:
                    total_sessions, avg_duration, last_session = session_stats
                    self.stats_text.insert(tk.END, f"Total Sessions: {total_sessions}\n")
                    self.stats_text.insert(tk.END, f"Avg Duration: {avg_duration:.1f} min\n" if avg_duration else "Avg Duration: N/A\n")
                    self.stats_text.insert(tk.END, f"Last Session: {last_session}\n\n" if last_session else "")
                
                self.stats_text.insert(tk.END, "🚨 THREAT DETECTIONS\n")
                self.stats_text.insert(tk.END, "=" * 30 + "\n")
                
                if detection_stats:
                    for detection_type, count in detection_stats:
                        self.stats_text.insert(tk.END, f"{detection_type}: {count}\n")
                else:
                    self.stats_text.insert(tk.END, "No threats detected yet\n")
                
                self.stats_text.config(state='disabled')
        
        except Exception as e:
            print(f"Error updating stats: {e}")
        
        # Schedule next update
        self.root.after(30000, self.update_stats)  # Update every 30 seconds
    
    def connect_camera(self):
        """Connect to IP camera"""
        ip_url = self.ip_entry.get().strip()
        
        if not ip_url:
            messagebox.showerror("Error", "Please enter IP camera URL")
            return
        
        try:
            self.log_message(f"🔗 Connecting to camera: {ip_url}")
            
            # Release existing connection
            if self.cap:
                self.cap.release()
            
            # Connect to IP camera
            self.cap = cv2.VideoCapture(ip_url)
            
            if self.cap.isOpened():
                self.log_message("✅ Camera connected successfully!")
                self.db_manager.log_system_action(self.user_id, "CAMERA_CONNECT", f"Connected to {ip_url}")
                
                # Start video display
                self.update_video_display()
            else:
                self.log_message("❌ Failed to connect to camera")
                messagebox.showerror("Connection Error", "Failed to connect to IP camera")
        
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
        
        self.log_message("⏹️ Threat monitoring stopped")
        self.db_manager.log_system_action(self.user_id, "MONITORING_STOP", "Threat detection monitoring stopped")
    
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
                frame = cv2.resize(frame, (640, 480))
                
                image = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(image)
                
                self.video_label.config(image=photo)
                self.video_label.image = photo
        
        # Schedule next update
        if self.cap and self.cap.isOpened():
            self.root.after(30, self.update_video_display)
    
    def monitor_threats(self):
        """Monitor for threats in video frames"""
        while self.monitoring:
            try:
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get(timeout=1)
                    
                    # Check each detection model
                    self.check_weapon_detection(frame)
                    self.check_crowd_detection(frame)
                    self.check_emotion_detection(frame)
                
                time.sleep(0.1)  # Small delay
            
            except queue.Empty:
                continue
            except Exception as e:
                self.log_message(f"❌ Monitoring error: {e}")
    
    def check_weapon_detection(self, frame):
        """Check for weapons in frame"""
        if 'weapon' not in self.models:
            return
        
        try:
            results = self.models['weapon'](frame)
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        confidence = float(box.conf[0])
                        if confidence > 0.5:  # Confidence threshold
                            # Log detection
                            detection_id = self.db_manager.log_detection(
                                self.user_id,
                                self.session_id,
                                "WEAPON",
                                confidence,
                                f"Weapon detected with {confidence:.2f} confidence"
                            )
                            
                            # Send alert
                            self.send_threat_alert("WEAPON", f"Weapon detected with {confidence:.2f} confidence", detection_id)
        
        except Exception as e:
            self.log_message(f"Weapon detection error: {e}")
    
    def check_crowd_detection(self, frame):
        """Check for crowds in frame"""
        if 'crowd' not in self.models:
            return
        
        try:
            results = self.models['crowd'](frame)
            
            person_count = 0
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        
                        if confidence > 0.5 and class_id == 0:  # Person class
                            person_count += 1
            
            if person_count > 5:  # Crowd threshold
                detection_id = self.db_manager.log_detection(
                    self.user_id,
                    self.session_id,
                    "CROWD",
                    person_count / 10.0,  # Normalize confidence
                    f"Crowd detected: {person_count} people"
                )
                
                self.send_threat_alert("CROWD", f"Crowd detected: {person_count} people", detection_id)
        
        except Exception as e:
            self.log_message(f"Crowd detection error: {e}")
    
    def check_emotion_detection(self, frame):
        """Check for suspicious emotions"""
        if 'emotion' not in self.models:
            return
        
        try:
            emotions = self.models['emotion'].detect_emotions(frame)
            
            for emotion_data in emotions:
                emotions_dict = emotion_data['emotions']
                
                # Check for high anger or fear
                anger_score = emotions_dict.get('angry', 0)
                fear_score = emotions_dict.get('fear', 0)
                
                if anger_score > 0.7 or fear_score > 0.7:
                    emotion_type = "anger" if anger_score > fear_score else "fear"
                    confidence = max(anger_score, fear_score)
                    
                    detection_id = self.db_manager.log_detection(
                        self.user_id,
                        self.session_id,
                        "SUSPICIOUS_EMOTION",
                        confidence,
                        f"High {emotion_type} detected: {confidence:.2f}"
                    )
                    
                    self.send_threat_alert("SUSPICIOUS_EMOTION", f"High {emotion_type} detected", detection_id)
        
        except Exception as e:
            self.log_message(f"Emotion detection error: {e}")
    
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
            return
        
        try:
            if threat_type == "WEAPON":
                # High priority - rapid beeps
                for _ in range(5):
                    winsound.Beep(1000, 200)
                    time.sleep(0.1)
            elif threat_type == "CROWD":
                # Medium priority - steady beeps
                for _ in range(3):
                    winsound.Beep(800, 300)
                    time.sleep(0.2)
            else:
                # Low priority - single beep
                winsound.Beep(600, 500)
        
        except Exception as e:
            self.log_message(f"Sound alert error: {e}")
    
    def send_email_alert(self, threat_type, description, detection_id):
        """Send email alert to logged-in user"""
        if not EMAIL_AVAILABLE:
            self.log_message("❌ Email not available")
            return
        
        try:
            # Load email configuration
            from email_config_setup import EmailConfig
            email_config = EmailConfig()
            
            if not email_config.is_configured():
                self.log_message("❌ Email not configured. Run email_config_setup.py first")
                return
            
            config = email_config.get_config()
            smtp_server = config["smtp_server"]
            smtp_port = config["smtp_port"]
            sender_email = config["sender_email"]
            sender_password = config["sender_password"]
            
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
    
    def detection_worker(self):
        """Process detection alerts"""
        while True:
            try:
                if not self.detection_queue.empty():
                    self.detection_queue.get()
                    # Process alert if needed
                    pass
                time.sleep(0.1)
            except Exception:
                break
    
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
    print("🛡️ Starting Authenticated Smart Surveillance System...")
    
    try:
        AuthenticatedSurveillanceSystem()
    except KeyboardInterrupt:
        print("\n👋 System shutdown requested")
    except Exception as e:
        print(f"❌ System error: {e}")

if __name__ == "__main__":
    main()