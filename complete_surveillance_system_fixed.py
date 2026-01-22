#!/usr/bin/env python3
"""
🛡️ COMPLETE SMART SURVEILLANCE SYSTEM
✅ Email Authentication + IP Webcam + Laptop Camera + Auto Email Alerts + Beep Sounds
ALL FEATURES IN ONE SYSTEM
"""

import cv2
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, ttk
import threading
import queue
import time
import datetime
import json
import sqlite3
import hashlib
try:
    from passlib.context import CryptContext
    PASSLIB_AVAILABLE = True
except Exception:
    PASSLIB_AVAILABLE = False
import smtplib
from pathlib import Path
from PIL import Image, ImageTk
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os
import concurrent.futures

# Optional torch import to prefer GPU when available
try:
    import torch
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False

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
        # Password hashing context (bcrypt)
        if PASSLIB_AVAILABLE:
            self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        else:
            self.pwd_context = None
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
    
    def hash_password(self, password):
        """Hash password using bcrypt (passlib). If passlib missing, fallback to SHA256 (not recommended)."""
        # Prefer the native `bcrypt` module when available for direct, predictable behavior
        try:
            import bcrypt as _bcrypt
            # bcrypt.hashpw returns bytes
            hashed = _bcrypt.hashpw(password.encode('utf-8'), _bcrypt.gensalt())
            return hashed.decode('utf-8')
        except Exception:
            pass

        # Next prefer passlib if available
        if self.pwd_context:
            return self.pwd_context.hash(password)

        # Final fallback (insecure): SHA256 hex
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
        # Fetch stored hash for the user
        cursor.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        user_id = None
        if row:
            user_id_db, stored_hash = row[0], row[1]
            try:
                # First, if stored hash looks like a bcrypt hash (starts with $2), try native bcrypt
                try:
                    if isinstance(stored_hash, str) and stored_hash.startswith('$2'):
                        import bcrypt as _bcrypt
                        if _bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                            user_id = user_id_db
                    # Next, try passlib if available and it recognizes the scheme
                    elif self.pwd_context and self.pwd_context.identify(stored_hash):
                        if self.pwd_context.verify(password, stored_hash):
                            user_id = user_id_db
                    else:
                        # Fallback: assume stored hash is SHA256 hex
                        sha_hash = hashlib.sha256(password.encode()).hexdigest()
                        if sha_hash == stored_hash:
                            user_id = user_id_db
                            # Re-hash with bcrypt (native) for better security if available
                            try:
                                import bcrypt as _bcrypt
                                new_hash = _bcrypt.hashpw(password.encode('utf-8'), _bcrypt.gensalt()).decode('utf-8')
                                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id_db))
                                conn.commit()
                                self.log_message(f"🔒 Upgraded password hash for user id {user_id_db} to bcrypt")
                            except Exception:
                                # If bcrypt native not available, try passlib re-hash
                                if self.pwd_context:
                                    try:
                                        new_hash = self.pwd_context.hash(password)
                                        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id_db))
                                        conn.commit()
                                        self.log_message(f"🔒 Upgraded password hash for user id {user_id_db} to passlib/bcrypt")
                                    except Exception:
                                        pass
                except Exception as e:
                    # Backend verification error
                    self.log_message(f"⚠️ Password backend verification error: {e}")
            except Exception as e:
                # Verification error
                self.log_message(f"⚠️ Password verification error: {e}")
        # Update last_login if authenticated
        if user_id:
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
            conn.commit()
        conn.close()
        return user_id
    
    def reset_password(self, email, new_password):
        """Reset password for an existing user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False
            
            user_id = row[0]
            # Hash the new password
            new_hash = self.hash_password(new_password)
            # Update password
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.log_message(f"❌ Password reset error: {e}")
            conn.close()
            return False
    
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

class AuthenticationWindow:
    """User authentication window with email login"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.user_id = None
        self.user_email = None
        
        self.root = tk.Tk()
        self.root.title("🔐 Smart Surveillance - Authentication")
        self.root.geometry("500x400")
        self.root.configure(bg='#2c3e50')
        self.root.eval('tk::PlaceWindow . center')
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main container
        main_container = tk.Frame(self.root, bg='#2c3e50')
        main_container.pack(fill='both', expand=True)
        
        # Title section
        title_label = tk.Label(main_container, text="🛡️ SMART SURVEILLANCE SYSTEM", 
                              font=('Arial', 18, 'bold'), bg='#2c3e50', fg='white')
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(main_container, text="Login with existing account OR Create new account", 
                                 font=('Arial', 12), bg='#2c3e50', fg='#bdc3c7')
        subtitle_label.pack(pady=(0, 10))
        
        # Instructions for new users
        new_user_label = tk.Label(main_container, text="👋 New User? Click 'Create New Account' below", 
                                 font=('Arial', 10, 'bold'), bg='#2c3e50', fg='#f39c12')
        new_user_label.pack(pady=(0, 20))
        
        # Center frame to hold the login form
        center_frame = tk.Frame(main_container, bg='#2c3e50')
        center_frame.pack(expand=True)
        
        # Login frame with fixed width (centered)
        login_frame = tk.Frame(center_frame, bg='#34495e', padx=30, pady=25)
        login_frame.pack()
        
        # Email
        tk.Label(login_frame, text="📧 Email Address (for alerts):", bg='#34495e', fg='white', 
                font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        self.email_entry = tk.Entry(login_frame, font=('Arial', 11), width=40)
        self.email_entry.pack(pady=(0, 15))
        
        # Password
        tk.Label(login_frame, text="🔒 Password:", bg='#34495e', fg='white', 
                font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        self.password_entry = tk.Entry(login_frame, show="*", font=('Arial', 11), width=40)
        self.password_entry.pack(pady=(0, 10))
        
        # Forgot password link
        forgot_btn = tk.Button(login_frame, text="🔑 Forgot Password?", 
                              command=self.reset_password, bg='#34495e', fg='#3498db', 
                              font=('Arial', 9, 'underline'), relief='flat', cursor='hand2',
                              activebackground='#34495e', activeforeground='#5dade2')
        forgot_btn.pack(anchor='e', pady=(0, 15))
        
        # Buttons with fixed width
        btn_frame = tk.Frame(login_frame, bg='#34495e')
        btn_frame.pack(pady=(10, 0))
        
        # Login button for existing users
        login_btn = tk.Button(btn_frame, text="🚀 Login (Existing User)", 
                            command=self.login, bg='#2ecc71', fg='white', 
                            font=('Arial', 11, 'bold'), pady=8, width=35)
        login_btn.pack(pady=(0, 8))
        
        # Separator
        separator_label = tk.Label(btn_frame, text="─── OR ───", 
                                bg='#34495e', fg='#7f8c8d', font=('Arial', 9))
        separator_label.pack(pady=5)
        
        # Register button for new users (more prominent)
        register_btn = tk.Button(btn_frame, text="📝 Create New Account (New User)", 
                                command=self.register, bg='#e74c3c', fg='white', 
                                font=('Arial', 11, 'bold'), pady=8, width=35)
        register_btn.pack(pady=(8, 0))
        
        # Info
        info_label = tk.Label(login_frame, 
                            text="Your email will receive automatic threat alerts\nAll detections logged securely",
                            bg='#34495e', fg='#bdc3c7', font=('Arial', 9))
        info_label.pack(pady=(20, 0))
        
        # Bind Enter key
        self.root.bind('<Return>', lambda e: self.login())
    
    def login(self):
        """Enhanced login for existing users"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not email or not password:
            messagebox.showerror("❌ Login Error", 
                            "Please enter both email and password\n\n🔐 Both fields are required to access your account")
            return
        
        user_id = self.db_manager.authenticate_user(email, password)
        if user_id:
            self.user_id = user_id
            self.user_email = email
            messagebox.showinfo("🎉 Welcome Back!", 
                            f"Successfully logged in!\n\n"
                            f"👤 User: {email}\n"
                            f"🛡️ Surveillance system ready\n"
                            f"📧 Alert notifications: ACTIVE\n\n"
                            f"Starting your monitoring session...")
            self.root.quit()
        else:
            # Enhanced error with helpful suggestions
            result = messagebox.askyesno("❌ Login Failed", 
                                    "Invalid email or password\n\n"
                                    "🔍 Possible issues:\n"
                                    "• Wrong password\n"
                                    "• Email not registered\n\n"
                                    "👋 New user? Click 'Yes' to create account\n"
                                    "📝 Try again? Click 'No'")
            if result:
                # Clear fields and show registration guidance
                self.password_entry.delete(0, tk.END)
                messagebox.showinfo("👋 New User Registration", 
                                "Welcome! Let's create your account:\n\n"
                                "1️⃣ Enter your email address\n"
                                "2️⃣ Choose a password (6+ characters)\n"
                                "3️⃣ Click 'Create New Account'\n\n"
                                "✅ You'll receive automatic threat alerts!")
    
    def register(self):
        """Enhanced registration for new users"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        
        # Comprehensive validation
        if not email or not password:
            messagebox.showerror("❌ Registration Error", 
                                "Please enter both email and password\n\n📝 Fill in both fields to create your account")
            return
        
        if len(password) < 6:
            messagebox.showerror("❌ Password Too Short", 
                                "Password must be at least 6 characters\n\n🔒 Choose a stronger password for security")
            return
        
        if "@" not in email or "." not in email:
            messagebox.showerror("❌ Invalid Email", 
                                "Please enter a valid email address\n\n📧 Example: user@gmail.com")
            return
        
        # Attempt to create user account
        user_id = self.db_manager.create_user(email, password)
        if user_id:
            self.user_id = user_id
            self.user_email = email
            messagebox.showinfo("🎉 Welcome New User!", 
                            f"Account created successfully!\n\n"
                            f"📧 Email: {email}\n"
                            f"✅ Automatic threat alerts: ENABLED\n"
                            f"🛡️ Your surveillance system is ready!\n\n"
                            f"Starting monitoring system now...")
            self.root.quit()
        else:
            # Email already exists - offer login option
            result = messagebox.askyesno("📧 Email Already Registered", 
                                        f"The email '{email}' already has an account.\n\n"
                                        f"👤 Do you want to login instead?\n"
                                        f"(Click 'Yes' to login, 'No' to try different email)")
            if result:
                # Automatically try login
                self.login()
    
    def reset_password(self):
        """Reset password for existing users"""
        # Create reset password dialog
        reset_window = tk.Toplevel(self.root)
        reset_window.title("🔑 Reset Password")
        reset_window.geometry("500x450")
        reset_window.configure(bg='#2c3e50')
        reset_window.transient(self.root)
        reset_window.grab_set()
        
        # Center the window relative to parent
        reset_window.update_idletasks()
        x = (reset_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (reset_window.winfo_screenheight() // 2) - (450 // 2)
        reset_window.geometry(f"500x450+{x}+{y}")
        
        # Main container
        main_container = tk.Frame(reset_window, bg='#2c3e50')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(main_container, text="🔑 Reset Your Password", 
                font=('Arial', 16, 'bold'), bg='#2c3e50', fg='white').pack(pady=(10, 10))
        
        tk.Label(main_container, text="Enter your registered email and new password", 
                font=('Arial', 10), bg='#2c3e50', fg='#bdc3c7').pack(pady=(0, 20))
        
        # Form frame
        form_frame = tk.Frame(main_container, bg='#34495e', padx=30, pady=25)
        form_frame.pack(pady=10)
        
        # Email
        tk.Label(form_frame, text="📧 Your Email Address:", bg='#34495e', fg='white', 
                font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        email_reset_entry = tk.Entry(form_frame, font=('Arial', 11), width=35)
        email_reset_entry.pack(pady=(0, 15))
        
        # New Password
        tk.Label(form_frame, text="🔒 New Password:", bg='#34495e', fg='white', 
                font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        new_pass_entry = tk.Entry(form_frame, show="*", font=('Arial', 11), width=35)
        new_pass_entry.pack(pady=(0, 15))
        
        # Confirm Password
        tk.Label(form_frame, text="🔒 Confirm New Password:", bg='#34495e', fg='white', 
                font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        confirm_pass_entry = tk.Entry(form_frame, show="*", font=('Arial', 11), width=35)
        confirm_pass_entry.pack(pady=(0, 20))
        
        def perform_reset():
            email = email_reset_entry.get().strip()
            new_password = new_pass_entry.get().strip()
            confirm_password = confirm_pass_entry.get().strip()
            
            # Validation
            if not email or not new_password or not confirm_password:
                messagebox.showerror("❌ Error", "Please fill in all fields")
                return
            
            if len(new_password) < 6:
                messagebox.showerror("❌ Password Too Short", 
                                    "Password must be at least 6 characters")
                return
            
            if new_password != confirm_password:
                messagebox.showerror("❌ Password Mismatch", 
                                    "New password and confirmation don't match")
                return
            
            # Check if user exists
            if self.db_manager.reset_password(email, new_password):
                messagebox.showinfo("✅ Success!", 
                                  f"Password reset successfully!\n\n"
                                  f"📧 Email: {email}\n"
                                  f"🔒 You can now login with your new password")
                reset_window.destroy()
                # Pre-fill email in login form
                self.email_entry.delete(0, tk.END)
                self.email_entry.insert(0, email)
                self.password_entry.focus()
            else:
                messagebox.showerror("❌ Reset Failed", 
                                   f"Email '{email}' not found\n\n"
                                   f"Please check the email address or create a new account")
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg='#34495e')
        btn_frame.pack(pady=(10, 0))
        
        tk.Button(btn_frame, text="✅ Reset Password", command=perform_reset,
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold'), 
                 pady=6, width=20).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="❌ Cancel", command=reset_window.destroy,
                 bg='#95a5a6', fg='white', font=('Arial', 10, 'bold'), 
                 pady=6, width=15).pack(side='left', padx=5)

class CompleteSurveillanceSystem:
    """Complete surveillance system with all features integrated"""

    def __init__(self, db_manager, user_id=None, user_email=None, preloaded_models=None):
        self.db_manager = db_manager
        self.user_id = user_id
        self.user_email = user_email
        # Create a session only if user is provided (auth step may happen later)
        if user_id and user_email:
            self.session_id = db_manager.create_session(user_id, user_email)
        else:
            self.session_id = None

        # Create configs directory
        os.makedirs("configs", exist_ok=True)

        # Enhanced Email configuration with App Password support
        self.email_config = {
            'enabled': False,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': '',
            'sender_password': '',
            'use_app_password': True 
        }

        # Camera settings
        self.cap = None
        self.camera_type = "none" 
        self.ip_webcam_url = ""
        self.is_monitoring = False

        # If models were preloaded before authentication, accept them to avoid reload delay
        self.models = preloaded_models or {}
        
        # Threading
        self.video_thread = None
        self.detection_queue = queue.Queue()
        # Executor for running inference off the capture/display thread
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.inference_future = None
        # How many display frames to skip between detection submissions
        self.detection_interval = 4
        # flag used to avoid queuing new inference while one is running
        self._inference_running = False
        
        # Alert settings
        self.alert_cooldown = 2  # Reduced to 2 seconds for better responsiveness
        self.last_alert_time = {}
        # Debounce confirmations to avoid false weapon logs
        self._weapon_confirm = {'count': 0, 'last_time': 0}
        os.makedirs("alerts", exist_ok=True)
        
        # Statistics
        self.stats = {
            'weapons_detected': 0,
            'people_detected': 0,
            'faces_analyzed': 0,
            'threats_blocked': 0,
            'emails_sent': 0,
            'beeps_played': 0
        }
        
        # Setup GUI first (needed for log_message)
        self.setup_gui()
        
        # Now load email config (after GUI is ready)
        self.load_email_config()

        # Try to auto-configure email if config file exists
        self.auto_configure_email()

        # Prefer environment variables for sensitive credentials (recommended)
        # Allows running without hard-coding secrets into config files
        env_sender = os.environ.get('SSS_EMAIL') or os.environ.get('SURVEILLANCE_SENDER')
        env_pass = os.environ.get('SSS_EMAIL_PASS') or os.environ.get('SURVEILLANCE_PASS')
        if env_sender:
            self.email_config['sender_email'] = env_sender
        if env_pass:
            self.email_config['sender_password'] = env_pass

        # Enable email alerts only when both sender email and password are available
        has_sender = bool(self.email_config.get('sender_email'))
        has_password = bool(self.email_config.get('sender_password'))
        if has_sender and has_password:
            self.email_config['enabled'] = True
        else:
            # keep disabled if missing credentials; user can configure via GUI or env vars
            self.email_config['enabled'] = False
        
        # Load AI models after GUI is ready
        self.load_ai_models()
    
    def load_ai_models(self):
        """Load AI models for detection"""
        try:
            # Weapon detection
            if YOLO_AVAILABLE:
                weapon_paths = [
                    "AI_models/Object_detection/best.pt",
                    "AI_models/Object_detection/yolov8n.pt",
                    "Object_detection/best.pt",
                    "yolov8n.pt"
                ]

                for path in weapon_paths:
                    try:
                        if os.path.exists(path):
                            self.models['weapon'] = YOLO(path)
                            self.log_message(f"✅ Weapon detection model loaded: {path}")
                            # Try to move underlying model to GPU if available
                            try:
                                if TORCH_AVAILABLE and torch.cuda.is_available():
                                    m = self.models['weapon']
                                    if hasattr(m, 'model') and hasattr(m.model, 'to'):
                                        m.model.to('cuda')
                                        self.log_message("🔧 Weapon model moved to CUDA")
                            except Exception as e:
                                self.log_message(f"⚠️ Weapon GPU move failed: {e}")
                            break
                    except Exception:
                        continue

                # Crowd detection
                crowd_paths = [
                    "AI_models/crowddetection/yolov8s.pt",
                    "AI_models/crowddetection/yolov8n.pt",
                    "crowddetection/yolov8s.pt",
                    "yolov8n.pt"
                ]

                for path in crowd_paths:
                    try:
                        if os.path.exists(path):
                            self.models['crowd'] = YOLO(path)
                            self.log_message(f"✅ Crowd detection model loaded: {path}")
                            try:
                                if TORCH_AVAILABLE and torch.cuda.is_available():
                                    m = self.models['crowd']
                                    if hasattr(m, 'model') and hasattr(m.model, 'to'):
                                        m.model.to('cuda')
                                        self.log_message("🔧 Crowd model moved to CUDA")
                            except Exception as e:
                                self.log_message(f"⚠️ Crowd GPU move failed: {e}")
                            break
                    except Exception:
                        continue

            # Emotion detection
            if FER_AVAILABLE:
                self.models['emotion'] = FER(mtcnn=True)
                self.log_message("✅ Emotion detection model loaded")

            # Try to load optional violence detection model (SlowFast / PyTorchVideo)
            try:
                import importlib
                violence_mod = importlib.import_module('AI_models.violence.violence')
                # The refactored module exposes load_model/predict helpers
                if hasattr(violence_mod, 'load_model'):
                    try:
                        # Attempt to load the model lazily; may raise ImportError if torch missing
                        violence_model = violence_mod.load_model()
                        # Store dict (module, model) so callers can use predict helpers
                        self.models['violence'] = {
                            'module': violence_mod,
                            'model': violence_model
                        }
                        self.log_message("✅ Violence detection model loaded (SlowFast)")
                    except Exception as inner_e:
                        self.log_message(f"ℹ️ Violence module found but failed to load model: {inner_e}")
                else:
                    self.log_message("ℹ️ Violence module found but API not compatible")
            except Exception as e:
                # Not critical; just log and continue with details
                self.log_message(f"ℹ️ Violence module not available or missing dependencies: {e}")

        except Exception as e:
            self.log_message(f"Model loading error: {e}")

        # Verification of loaded models
        self.log_message("🔍 MODEL STATUS:")
        self.log_message(f"  - Weapon model: {'✅ LOADED' if 'weapon' in self.models else '❌ NOT FOUND'}")
        self.log_message(f"  - Crowd model: {'✅ LOADED' if 'crowd' in self.models else '❌ NOT FOUND'}")
        self.log_message(f"  - Emotion model: {'✅ LOADED' if 'emotion' in self.models else '❌ NOT FOUND'}")

        # Test beep sound system
        if SOUND_AVAILABLE:
            self.log_message("🔊 Testing beep system...")
            # Play a quick test beep
            threading.Thread(target=lambda: winsound.Beep(1000, 100), daemon=True).start()
    
    def setup_gui(self):
        """Setup main surveillance interface"""
        self.root = tk.Tk()
        self.root.title(f"🛡️ Complete Surveillance - {self.user_email}")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2c3e50')
        
        # Top frame - User info and controls
        top_frame = tk.Frame(self.root, bg='#34495e', pady=10)
        top_frame.pack(fill='x', padx=10, pady=5)
        
        # User info
        user_info = f"👤 User: {self.user_email} | 🤖 AI Models: {len(self.models)} | 📧 Auto-Alerts: {'ON' if self.email_config['enabled'] else 'SETUP NEEDED'}"
        user_label = tk.Label(top_frame, text=user_info, 
                             font=('Arial', 12, 'bold'), bg='#34495e', fg='white')
        user_label.pack(side='left')
        
        # Control buttons
        btn_frame = tk.Frame(top_frame, bg='#34495e')
        btn_frame.pack(side='right')
        
        self.monitor_btn = tk.Button(btn_frame, text="🟢 Start Monitoring", 
                                    command=self.toggle_monitoring, bg='#2ecc71', fg='white', 
                                    font=('Arial', 11, 'bold'))
        self.monitor_btn.pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="📱 Camera Setup", command=self.show_camera_selection,
                 bg='#9b59b6', fg='white', font=('Arial', 11)).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="📧 Email Setup", command=self.configure_email,
                 bg='#3498db', fg='white', font=('Arial', 11)).pack(side='left', padx=5)

        # Logout to end session and close the app
        tk.Button(btn_frame, text="🚪 Logout", command=self.logout,
             bg='#e74c3c', fg='white', font=('Arial', 11)).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="💾 Save Frame", command=self.save_frame,
                 bg='#f39c12', fg='white', font=('Arial', 11)).pack(side='left', padx=5)
        
        # Main content frame
        content_frame = tk.Frame(self.root, bg='#2c3e50')
        content_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Left side - Video feed
        video_frame = tk.Frame(content_frame, bg='#34495e', relief='raised', bd=2)
        video_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        # Camera status label
        self.camera_status_label = tk.Label(video_frame, text="📹 CAMERA: Not Connected", 
                                           font=('Arial', 14, 'bold'), bg='#34495e', fg='#e74c3c')
        self.camera_status_label.pack(pady=5)
        
        self.video_label = tk.Label(video_frame, bg='black', text="Select camera source to start", 
                                   fg='white', font=('Arial', 16))
        self.video_label.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Right side - Statistics and controls
        right_frame = tk.Frame(content_frame, bg='#2c3e50', width=350)
        right_frame.pack(side='right', fill='y')
        right_frame.pack_propagate(False)
        
        # Statistics panel
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
        
        # Alert panel
        alert_frame = tk.Frame(right_frame, bg='#34495e', relief='raised', bd=2)
        alert_frame.pack(fill='both', expand=True, pady=(5, 0))
        
        tk.Label(alert_frame, text="🚨 ACTIVITY LOG", 
                font=('Arial', 12, 'bold'), bg='#34495e', fg='white').pack(pady=5)
        
        self.log_text = scrolledtext.ScrolledText(alert_frame, height=20, width=40,
                                                 bg='#2c3e50', fg='#00ff00', font=('Consolas', 9))
        self.log_text.pack(padx=10, pady=10, fill='both', expand=True)
        
        # Clear button
        tk.Button(alert_frame, text="Clear Log", command=self.clear_log,
                 bg='#95a5a6', fg='white', font=('Arial', 9)).pack(pady=5)
        
        # Welcome messages
        self.log_message(f"🎉 Welcome {self.user_email}!")
        self.log_message(f"🤖 {len(self.models)} AI models loaded")
        self.log_message("📧 Email alerts configured for your account")
        self.log_message("🔊 Beep sounds enabled for threats")
        self.log_message("📱 Click 'Camera Setup' to choose camera source")
        
        # Show camera selection after a short delay
        self.root.after(2000, self.show_camera_selection)

        # Add quick violence test button (if model available it will run)
        try:
            tk.Button(btn_frame, text="🔍 Test Violence", command=self.run_violence_test,
                      bg='#c0392b', fg='white', font=('Arial', 11)).pack(side='left', padx=5)
        except Exception:
            pass
    
    def show_camera_selection(self):
        """Show camera selection dialog"""
        camera_window = tk.Toplevel(self.root)
        camera_window.title("📱 Camera Selection")
        camera_window.geometry("550x480")
        camera_window.configure(bg='#2c3e50')
        camera_window.transient(self.root)     
        camera_window.grab_set()
        
        # Title
        tk.Label(camera_window, text="📱 SELECT CAMERA SOURCE", 
                font=('Arial', 16, 'bold'), bg='#2c3e50', fg='white').pack(pady=15)
        
        # Options frame
        options_frame = tk.Frame(camera_window, bg='#34495e', relief='raised', bd=2)
        options_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # IP Webcam option
        ip_frame = tk.Frame(options_frame, bg='#34495e')
        ip_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(ip_frame, text="📱 Mobile IP Webcam (Recommended)", 
                font=('Arial', 12, 'bold'), bg='#34495e', fg='#3498db').pack(anchor='w')
        
        tk.Label(ip_frame, text="• Install 'IP Webcam' app on your phone\n• Connect to same Wi-Fi network\n• Enter phone's IP address", 
                font=('Arial', 10), bg='#34495e', fg='white').pack(anchor='w', pady=5)
        
        ip_btn = tk.Button(ip_frame, text="📱 Setup IP Webcam", command=lambda: self.setup_ip_camera(camera_window),
                          bg='#3498db', fg='white', font=('Arial', 11, 'bold'))
        ip_btn.pack(anchor='w', pady=5)
        
        # Separator
        tk.Frame(options_frame, height=2, bg='#2c3e50').pack(fill='x', padx=15, pady=10)
        
        # Laptop camera option
        laptop_frame = tk.Frame(options_frame, bg='#34495e')
        laptop_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(laptop_frame, text="💻 Laptop/Desktop Camera", 
                font=('Arial', 12, 'bold'), bg='#34495e', fg='#f39c12').pack(anchor='w')
        
        tk.Label(laptop_frame, text="• Use built-in or USB camera\n• Plug and play, no setup needed", 
                font=('Arial', 10), bg='#34495e', fg='white').pack(anchor='w', pady=5)
        
        laptop_btn = tk.Button(laptop_frame, text="💻 Use Laptop Camera", command=lambda: self.setup_laptop_camera(camera_window),
                              bg='#f39c12', fg='white', font=('Arial', 11, 'bold'))
        laptop_btn.pack(anchor='w', pady=5)
        
        # Cancel button
        tk.Button(camera_window, text="❌ Cancel", command=camera_window.destroy,
                 bg='#e74c3c', fg='white', font=('Arial', 11)).pack(pady=15)
    
    def setup_ip_camera(self, parent_window):
        """Setup IP webcam"""
        ip_address = simpledialog.askstring("📱 IP Webcam Setup",
                                           "Enter your mobile IP address:\n\n" +
                                           "Example: 192.168.0.107\n" +
                                           "(Find this in your IP Webcam app)",
                                           initialvalue="192.168.0.107")
        
        if not ip_address:
            return
        
        self.ip_webcam_url = f"http://{ip_address}:8080/video"
        
        # Test connection
        self.log_message(f"📱 Testing IP webcam connection: {ip_address}")
        test_cap = cv2.VideoCapture(self.ip_webcam_url)
        
        if test_cap.isOpened():
            ret, frame = test_cap.read()
            if ret and frame is not None:
                test_cap.release()
                self.camera_type = "ip"
                self.camera_status_label.config(text=f"📱 CAMERA: IP Webcam ({ip_address})", fg='#2ecc71')
                self.log_message(f"✅ IP webcam connected: {ip_address}")
                messagebox.showinfo("✅ Success", f"IP webcam connected successfully!\n\nIP: {ip_address}")
                parent_window.destroy()
                return
            else:
                test_cap.release()
        
        messagebox.showerror("❌ Connection Failed", f"Cannot connect to IP webcam at {ip_address}\n\nPlease check:\n• IP Webcam app is running\n• IP address is correct\n• Same Wi-Fi network")
    
    def setup_laptop_camera(self, parent_window):
        """Setup laptop camera"""
        self.log_message("💻 Testing laptop camera...")
        
        # Try different camera indices
        for camera_index in [0, 1, 2]:
            test_cap = cv2.VideoCapture(camera_index)
            if test_cap.isOpened():
                ret, frame = test_cap.read()
                if ret and frame is not None:
                    test_cap.release()
                    self.camera_type = "laptop"
                    self.laptop_camera_index = camera_index
                    self.camera_status_label.config(text="💻 CAMERA: Laptop Camera", fg='#2ecc71')
                    self.log_message(f"✅ Laptop camera connected (index {camera_index})")
                    messagebox.showinfo("✅ Success", "Laptop camera connected successfully!")
                    parent_window.destroy()
                    return
                else:
                    test_cap.release()
        
        messagebox.showerror("❌ Camera Not Found", "Cannot access laptop camera\n\nPlease check:\n• Camera permissions\n• Camera not used by other apps\n• Camera drivers installed")
    
    def toggle_monitoring(self):
        """Toggle monitoring on/off"""
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start video monitoring"""
        if self.camera_type == "none":
            messagebox.showwarning("No Camera", "Please select a camera source first")
            self.show_camera_selection()
            return
        
        # Connect to camera
        if self.camera_type == "ip":
            self.cap = cv2.VideoCapture(self.ip_webcam_url)
        elif self.camera_type == "laptop":
            self.cap = cv2.VideoCapture(self.laptop_camera_index)
        
        if not self.cap.isOpened():
            messagebox.showerror("Camera Error", "Failed to connect to camera")
            return
        
        # Configure camera
        # Increase capture resolution for a larger display while keeping buffer small
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.is_monitoring = True
        self.monitor_btn.config(text="🔴 Stop Monitoring", bg='#e74c3c')
        
        # Start video thread
        self.video_thread = threading.Thread(target=self.video_loop)
        self.video_thread.daemon = True
        self.video_thread.start()
        
        self.log_message("🚀 Monitoring started!")
    
    def stop_monitoring(self):
        """Stop video monitoring"""
        self.is_monitoring = False
        if self.cap:
            self.cap.release()
        
        self.monitor_btn.config(text="🟢 Start Monitoring", bg='#2ecc71')
        self.log_message("⏹️ Monitoring stopped")

    def logout(self):
        """Logout user and close the application"""
        try:
            if messagebox.askyesno("Logout", "End session and close the app?"):
                # stop any monitoring and release camera
                if self.is_monitoring:
                    self.stop_monitoring()
                # shut down executor to avoid background tasks
                try:
                    self.executor.shutdown(wait=False)
                except Exception:
                    pass
                # close the UI
                self.root.destroy()
        except Exception as e:
            self.log_message(f"Logout error: {e}")
    
    def video_loop(self):
        """Enhanced video processing loop with smooth box persistence"""
        frame_count = 0
        
        # Enhanced detection caching system
        self.persistent_detections = {'weapons': [], 'people': [], 'faces': []}
        self.detection_timestamps = {'weapons': [], 'people': [], 'faces': []}
        self.box_lifetime = 4.0  # Keep boxes visible for 4 seconds
        
        while self.is_monitoring:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                current_time = time.time()
                
                # Submit detection work every detection_interval frames using executor
                # and collect results from previous inference when available.
                # This keeps the capture/display loop responsive while inference runs.
                if frame_count % self.detection_interval == 0:
                    # If a previous inference finished, collect and process its results
                    if self.inference_future is not None and self.inference_future.done():
                        try:
                            new_results = self.inference_future.result()
                            if new_results['weapons'] or new_results['people'] or new_results['faces']:
                                self.log_message(f"🔍 DETECTIONS: Weapons={len(new_results['weapons'])}, People={len(new_results['people'])}, Faces={len(new_results['faces'])}")
                                for detection_type in ['weapons', 'people', 'faces']:
                                    for detection in new_results[detection_type]:
                                        self.persistent_detections[detection_type].append(detection)
                                        self.detection_timestamps[detection_type].append(current_time)

                                if self.has_threats(new_results):
                                    self.log_message("🚨 THREAT DETECTED - Processing alerts...")
                                    # pass the latest frame for context
                                    self.handle_threat_detection(new_results, frame)

                                self.update_statistics(new_results)
                        except Exception as e:
                            self.log_message(f"❌ Inference result error: {e}")
                        finally:
                            self.inference_future = None

                    # If no inference is running, submit current frame for detection
                    if self.inference_future is None:
                        try:
                            frame_for_infer = frame.copy()
                            self.inference_future = self.executor.submit(self.detect_threats, frame_for_infer)
                        except Exception as e:
                            self.log_message(f"❌ Failed to submit inference: {e}")
                
                # Clean old detections from cache
                for detection_type in ['weapons', 'people', 'faces']:
                    # Remove detections older than box_lifetime
                    valid_indices = []
                    for i, timestamp in enumerate(self.detection_timestamps[detection_type]):
                        if current_time - timestamp < self.box_lifetime:
                            valid_indices.append(i)
                    
                    # Keep only valid (recent) detections
                    self.persistent_detections[detection_type] = [
                        self.persistent_detections[detection_type][i] for i in valid_indices
                    ]
                    self.detection_timestamps[detection_type] = [
                        self.detection_timestamps[detection_type][i] for i in valid_indices
                    ]
                
                # Always draw all persistent detections
                display_results = {
                    'weapons': self.persistent_detections['weapons'].copy(),
                    'people': self.persistent_detections['people'].copy(),
                    'faces': self.persistent_detections['faces'].copy()
                }
                
                # Draw detections with enhanced visibility
                frame = self.draw_detections(frame, display_results)
                
                # Update GUI display with optimized refresh
                self.update_video_display(frame)
                
                frame_count += 1
                time.sleep(0.01)  # Faster refresh for smoother display
                
            except Exception as e:
                self.log_message(f"❌ Video error: {e}")
                break
    
    def detect_threats(self, frame):
        """Detect threats using AI models"""
        results = {
            'weapons': [],
            'people': [],
            'faces': [],
            'emotions': []
        }
        
        try:
            # Enhanced weapon detection - only real weapons (knife, gun, sword, pistol, rifle)
            if 'weapon' in self.models:
                # Higher confidence thresholds to avoid false positives from metals
                for conf_threshold in [0.45, 0.55, 0.65]:
                    weapon_results = self.models['weapon'](frame, verbose=False, conf=conf_threshold)
                    for r in weapon_results:
                        boxes = r.boxes
                        if boxes is not None:
                            for box in boxes:
                                conf = float(box.conf[0])
                                cls = int(box.cls[0])
                                
                                # Filter for actual weapon classes only (0=knife, 1=gun, 2=sword, 3=pistol, 4=rifle)
                                valid_weapon_classes = [0, 1, 2, 3, 4]  # Only real weapons
                                
                                if conf > conf_threshold and cls in valid_weapon_classes:
                                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                    
                                    # Additional size filter - weapons should be reasonably sized
                                    bbox_width = x2 - x1
                                    bbox_height = y2 - y1
                                    bbox_area = bbox_width * bbox_height
                                    
                                    # Filter out too small or too large detections (likely false positives)
                                    if 500 < bbox_area < 100000:  # Reasonable weapon size
                                        results['weapons'].append({
                                            'bbox': (int(x1), int(y1), int(x2), int(y2)),
                                            'confidence': conf,
                                            'class': cls
                                        })
                                        weapon_names = {0: "KNIFE", 1: "GUN", 2: "SWORD", 3: "PISTOL", 4: "RIFLE"}
                                        weapon_type = weapon_names.get(cls, "WEAPON")
                                        self.log_message(f"🔍 REAL WEAPON FOUND: {weapon_type} (Class={cls}), Conf={conf:.3f}")
                    # If weapons found, break to avoid duplicates
                    if results['weapons']:
                        break
            
            # People detection
            if 'crowd' in self.models:
                people_results = self.models['crowd'](frame, verbose=False)
                for r in people_results:
                    boxes = r.boxes
                    if boxes is not None:
                        for box in boxes:
                            conf = float(box.conf[0])
                            cls = int(box.cls[0])
                            if cls == 0 and conf > 0.5:  # Person class
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                results['people'].append({
                                    'bbox': (int(x1), int(y1), int(x2), int(y2)),
                                    'confidence': conf
                                })
            
            # Emotion detection
            if 'emotion' in self.models:
                try:
                    emotion_results = self.models['emotion'].detect_emotions(frame)
                    for face in emotion_results:
                        x, y, w, h = face['box']
                        dominant = max(face['emotions'], key=face['emotions'].get)
                        results['faces'].append({
                            'bbox': (x, y, x+w, y+h),
                            'emotions': face['emotions'],
                            'dominant': dominant,
                            'confidence': face['emotions'][dominant]
                        })
                except Exception:
                    pass  # FER can be unstable
        
        except Exception as e:
            self.log_message(f"❌ Detection error: {e}")
        
        return results
    
    def has_threats(self, results):
        """Check if any threats are detected"""
        return (len(results['weapons']) > 0 or 
                len(results['people']) > 5 or
                any(face['dominant'] in ['angry', 'fear'] and face['confidence'] > 0.7 
                    for face in results['faces']))
    
    def handle_threat_detection(self, results, frame):
        """Handle detected threats with alerts and emails"""
        current_time = time.time()
        threats_handled = []
        
        # Handle weapon threats (CRITICAL) with debounce to avoid false positives
        if results['weapons']:
            # Confirm weapon across at least 2 consecutive inference cycles within 2 seconds
            if current_time - self._weapon_confirm['last_time'] > 2.0:
                self._weapon_confirm['count'] = 0
            self._weapon_confirm['count'] += 1
            self._weapon_confirm['last_time'] = current_time

            if self._weapon_confirm['count'] >= 2:  # require double confirmation
                self.log_message(f"🚨 PROCESSING {len(results['weapons'])} WEAPON ALERTS!")
                if 'weapon' not in self.last_alert_time or current_time - self.last_alert_time['weapon'] > self.alert_cooldown:
                    weapon_count = len(results['weapons'])
                    # Choose highest confidence detection for logging
                    top_weapon = max(results['weapons'], key=lambda w: w.get('confidence', 0))
                    threat_message = f"🚨 CRITICAL: {weapon_count} WEAPON(S) DETECTED!"
                    
                    # Log to database
                    detection_id = self.db_manager.log_detection(
                        self.user_id, self.user_email, self.session_id,
                        "weapon", top_weapon.get('confidence', 0.9),
                        f"{weapon_count} weapons detected in surveillance area"
                    )
                    
                    # Play urgent beep sound
                    self.play_beep_sound("weapon")
                    self.db_manager.mark_beep_played(detection_id)
                    self.stats['beeps_played'] += 1
                    
                    # Send email alert
                    self.send_email_alert("WEAPON DETECTED", threat_message, results, frame, detection_id)
                    
                    # Log message
                    self.log_message(threat_message)
                    threats_handled.append("weapon")
                    self.last_alert_time['weapon'] = current_time
                    self.stats['threats_blocked'] += 1
                    # reset confirmation after handling
                    self._weapon_confirm['count'] = 0
        
        # Handle crowd threats (HIGH)
        people_count = len(results['people'])
        if people_count > 5:
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
                self.send_email_alert("CROWD DETECTED", threat_message, results, frame, detection_id)
                
                # Log message
                self.log_message(threat_message)
                threats_handled.append("crowd")
                self.last_alert_time['crowd'] = current_time
                self.stats['threats_blocked'] += 1
        
        # Handle suspicious behavior (MEDIUM)
        suspicious_faces = [face for face in results['faces'] 
                          if face['dominant'] in ['angry', 'fear'] and face['confidence'] > 0.8]
        if suspicious_faces:
            if 'behavior' not in self.last_alert_time or current_time - self.last_alert_time['behavior'] > self.alert_cooldown:
                threat_message = f"😠 SUSPICIOUS BEHAVIOR: {len(suspicious_faces)} suspicious faces!"
                
                # Log to database
                detection_id = self.db_manager.log_detection(
                    self.user_id, self.user_email, self.session_id,
                    "behavior", suspicious_faces[0]['confidence'],
                    f"Suspicious behavior detected: {suspicious_faces[0]['dominant']}"
                )
                
                # Play behavior beep sound
                self.play_beep_sound("behavior")
                self.db_manager.mark_beep_played(detection_id)
                self.stats['beeps_played'] += 1
                
                # Send email alert
                self.send_email_alert("SUSPICIOUS BEHAVIOR", threat_message, results, frame, detection_id)
                
                # Log message
                self.log_message(threat_message)
                threats_handled.append("behavior")
                self.last_alert_time['behavior'] = current_time
                self.stats['threats_blocked'] += 1
        
        # Update statistics display
        self.update_stats_display()

    def run_violence_test(self):
        """Run a small test using the optional violence detection module (if available)."""
        try:
            if 'violence' in self.models and isinstance(self.models['violence'], dict):
                mod = self.models['violence'].get('module')
                model_obj = self.models['violence'].get('model')
                if mod is None or model_obj is None:
                    messagebox.showwarning("No Violence Model", "Violence module found but model not loaded.")
                    return

                # Try a few common function names exposed by a violence module
                if hasattr(mod, 'predict'):
                    try:
                        res = mod.predict(model_obj)
                        messagebox.showinfo("Violence Test Result", f"Violence prediction: {res}")
                        return
                    except Exception:
                        pass

                if hasattr(mod, 'run_inference'):
                    try:
                        res = mod.run_inference(model_obj)
                        messagebox.showinfo("Violence Test Result", f"Violence inference: {res}")
                        return
                    except Exception:
                        pass

                # No known test entrypoint
                messagebox.showinfo("Violence Model", "Violence module is available but no compatible test function was found.")
                return

            # No violence module loaded
            messagebox.showinfo("No Model", "Violence detection model not loaded or unavailable.")

        except Exception as e:
            self.log_message(f"❌ Violence test error: {e}")
            try:
                messagebox.showerror("Test Failed", f"Violence test failed: {e}")
            except Exception:
                print(f"Violence test failed: {e}")
    
    def play_beep_sound(self, threat_type):
        """Play beep sound based on threat type"""
        # If winsound is available (Windows), use it; otherwise fallback to tkinter bell
        def play_beeps_with_winsound():
            try:
                if threat_type == "weapon":
                    for _ in range(5):
                        winsound.Beep(1500, 200)
                        time.sleep(0.1)
                elif threat_type == "crowd":
                    for _ in range(3):
                        winsound.Beep(1000, 300)
                        time.sleep(0.2)
                elif threat_type == "behavior":
                    for _ in range(2):
                        winsound.Beep(800, 400)
                        time.sleep(0.3)

                self.log_message(f"🔊 {threat_type.upper()} beep alert played")
            except Exception as e:
                self.log_message(f"🔇 Beep error (winsound): {e}")

        def play_beeps_with_tkbell():
            try:
                # Use root.bell() as a cross-platform fallback; emulate different patterns
                if threat_type == "weapon":
                    for _ in range(5):
                        try:
                            self.root.bell()
                        except Exception:
                            print('\a', end='')
                        time.sleep(0.15)
                elif threat_type == "crowd":
                    for _ in range(3):
                        try:
                            self.root.bell()
                        except Exception:
                            print('\a', end='')
                        time.sleep(0.25)
                elif threat_type == "behavior":
                    for _ in range(2):
                        try:
                            self.root.bell()
                        except Exception:
                            print('\a', end='')
                        time.sleep(0.35)

                self.log_message(f"🔊 {threat_type.upper()} bell alert played (fallback)")
            except Exception as e:
                self.log_message(f"🔇 Beep error (fallback): {e}")

        # Choose implementation
        if SOUND_AVAILABLE:
            thread_target = play_beeps_with_winsound
        else:
            thread_target = play_beeps_with_tkbell

        beep_thread = threading.Thread(target=thread_target)
        beep_thread.daemon = True
        beep_thread.start()
    
    def send_email_alert(self, alert_type, message, results, frame, detection_id):
        """Send automatic email alert to user"""
        if not self.email_config['enabled']:
            self.log_message("📧 Email not configured - please setup Gmail")
            return
        
        def send_email():
            try:
                # Create email message
                msg = MIMEMultipart()
                msg['From'] = self.email_config['sender_email']
                msg['To'] = self.user_email
                msg['Subject'] = f"🚨 SECURITY ALERT: {alert_type}"
                
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Create detailed email body
                body = f"""
🛡️ SMART SURVEILLANCE SYSTEM - SECURITY ALERT

⚠️ ALERT TYPE: {alert_type}
⏰ TIME: {timestamp}
👤 USER: {self.user_email}
🔍 DETECTION ID: {detection_id}

📋 ALERT DETAILS:
{message}

📊 DETECTION SUMMARY:
"""
                
                # Add detection details
                if results['weapons']:
                    body += f"🔫 WEAPONS: {len(results['weapons'])} detected\n"
                if results['people']:
                    body += f"👥 PEOPLE: {len(results['people'])} detected\n"
                if results['faces']:
                    body += f"😊 FACES: {len(results['faces'])} analyzed\n"
                
                body += f"""
🚨 RECOMMENDED ACTIONS:
✓ Check surveillance feed immediately
✓ Verify threat level in monitored area
✓ Contact security if necessary
✓ Review recorded evidence

📧 This alert was automatically sent to: {self.user_email}
🤖 Generated by: Complete Smart Surveillance System
"""
                
                msg.attach(MIMEText(body, 'plain'))
                
                # Attach screenshot evidence
                try:
                    screenshot_path = f"alerts/alert_{detection_id}_{timestamp.replace(':', '-')}.jpg"
                    cv2.imwrite(screenshot_path, frame)
                    
                    with open(screenshot_path, 'rb') as f:
                        img_data = f.read()
                        image = MIMEImage(img_data)
                        image.add_header('Content-Disposition', 'attachment', 
                                       filename=f'{alert_type}_evidence.jpg')
                        msg.attach(image)
                except Exception as e:
                    self.log_message(f"📎 Screenshot attach failed: {e}")
                
                # Send email with enhanced authentication
                server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
                server.starttls()
                
                # Prefer environment variables for credentials if provided
                env_sender = os.environ.get('SSS_EMAIL') or os.environ.get('SURVEILLANCE_SENDER')
                env_pass = os.environ.get('SSS_EMAIL_PASS') or os.environ.get('SURVEILLANCE_PASS')

                if env_sender:
                    sender_email = env_sender
                    self.log_message("📧 Using sender from environment variable SSS_EMAIL")
                else:
                    sender_email = self.email_config.get('sender_email', self.user_email)

                if env_pass:
                    sender_password = env_pass
                    self.log_message("🔐 Using app password from environment variable SSS_EMAIL_PASS")
                else:
                    sender_password = self.email_config.get('sender_password', '')

                if not sender_email:
                    self.log_message("📧 Email attempt: No sender configured - cannot send email")
                    self.db_manager.mark_email_sent(detection_id)
                    return

                if not sender_password:
                    self.log_message("⚠️ Email alert attempted but App Password not configured")
                    self.log_message(f"📧 ALERT LOGGED: {alert_type} detected at {timestamp}")
                    # Still log the alert even if email fails
                    self.db_manager.mark_email_sent(detection_id)
                    return

                # Attempt to login - catch authentication errors separately for clearer guidance
                try:
                    server.login(sender_email, sender_password)
                except smtplib.SMTPAuthenticationError as auth_err:
                    self.log_message(f"❌ SMTP Authentication failed: {auth_err}")
                    self.log_message("💡 Make sure 2-Step Verification is enabled and you're using a 16-character Gmail App Password")
                    self.db_manager.mark_email_sent(detection_id)
                    return
                except Exception as ex:
                    self.log_message(f"❌ SMTP login error: {ex}")
                    self.db_manager.mark_email_sent(detection_id)
                    return
                server.sendmail(sender_email, self.user_email, msg.as_string())
                server.quit()
                
                # Mark as sent
                self.db_manager.mark_email_sent(detection_id)
                self.stats['emails_sent'] += 1
                
                self.log_message(f"✅ {alert_type} email sent successfully to {self.user_email}")
                
            except Exception as e:
                self.log_message(f"❌ Email sending failed: {e}")
                self.log_message(f"📧 ALERT LOGGED: {alert_type} detected at {timestamp}")
                
                # Provide specific guidance based on error type
                error_str = str(e).lower()
                if "authentication" in error_str or "password" in error_str:
                    self.log_message("💡 Setup Gmail App Password: Gmail Settings > Security > 2FA > App Passwords")
                elif "connection" in error_str or "network" in error_str:
                    self.log_message("🌐 Check internet connection")
                else:
                    self.log_message("⚙️ Check Email Settings in system menu")
        
        # Send email in background thread
        email_thread = threading.Thread(target=send_email)
        email_thread.daemon = True
        email_thread.start()
    
    def draw_detections(self, frame, results):
        """Ultra-enhanced detection drawing with maximum visibility"""
        # Draw weapons (leaner styling)
        for i, weapon in enumerate(results['weapons']):
            x1, y1, x2, y2 = weapon['bbox']
            conf = weapon['confidence']

            # Slim weapon box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 1)

            # Get specific weapon type name based on class
            weapon_names = {
                0: "KNIFE",
                1: "GUN", 
                2: "SWORD",
                3: "PISTOL",
                4: "RIFLE"
            }
            weapon_type = weapon_names.get(weapon.get('class', 0), "WEAPON")
            
            # Clean weapon label (compact)
            label = f"{weapon_type} {conf:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]

            # Compact label background
            cv2.rectangle(frame, (x1, y1-16), (x1+label_size[0]+8, y1), (20, 20, 20), -1)
            cv2.rectangle(frame, (x1, y1-16), (x1+label_size[0]+8, y1), (0, 0, 255), 1)
            cv2.putText(frame, label, (x1+4, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw people (leaner styling)
        for i, person in enumerate(results['people'], 1):
            x1, y1, x2, y2 = person['bbox']
            conf = person['confidence']
            
            # Slim box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 180, 0), 1)
            
            # Compact label
            label = f"PERSON {i} {conf:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.rectangle(frame, (x1, y1-16), (x1+label_size[0]+8, y1), (15, 15, 15), -1)
            cv2.rectangle(frame, (x1, y1-16), (x1+label_size[0]+8, y1), (0, 180, 0), 1)
            cv2.putText(frame, label, (x1+4, y1-4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw faces with emotions (leaner styling)
        for face in results['faces']:
            x1, y1, x2, y2 = face['bbox']
            emotion = face['dominant']
            conf = face['confidence']
            
            # Color based on emotion intensity
            if emotion in ['angry', 'fear', 'disgust']:
                color = (0, 0, 255)  # Red for negative emotions
            elif emotion in ['happy', 'surprise']:
                color = (0, 255, 0)  # Green for positive emotions  
            else:
                color = (255, 0, 0)  # Blue for neutral emotions
            
            # Slim box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)
            
            # Compact label
            label = f"{emotion.upper()} {conf:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.rectangle(frame, (x1, y1-16), (x1+label_size[0]+8, y1), (15, 15, 15), -1)
            cv2.rectangle(frame, (x1, y1-16), (x1+label_size[0]+8, y1), color, 1)
            cv2.putText(frame, label, (x1+3, y1-4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Enhanced detection summary with status indicators
        total_detections = len(results['weapons']) + len(results['people']) + len(results['faces'])
        if total_detections > 0:
            # Dynamic summary with threat level - clean text
            if results['weapons']:
                status = "CRITICAL WEAPON THREAT"
                bg_color = (0, 0, 255)
            elif len(results['people']) >= 5:
                status = "CROWD DETECTED" 
                bg_color = (0, 165, 255)
            else:
                status = "MONITORING ACTIVE"
                bg_color = (0, 128, 0)
            
            summary = f"{status} | W:{len(results['weapons'])} P:{len(results['people'])} F:{len(results['faces'])}"
            
            # Slim summary display sized to text
            text_size = cv2.getTextSize(summary, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)[0]
            pad_x, pad_y = 8, 8
            x1, y1 = 8, 8
            x2 = x1 + text_size[0] + pad_x
            y2 = y1 + text_size[1] + pad_y
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), -1)
            cv2.rectangle(frame, (x1+2, y1+2), (x2-2, y2-2), bg_color, -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)
            cv2.putText(frame, summary, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        
        return frame
    
    def update_video_display(self, frame):
        """Optimized video display with reduced lag"""
        try:
            # Resize for display (optimized size)
            frame = cv2.resize(frame, (800, 600))  # Larger display for better visibility
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image with optimization
            pil_image = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Direct update without threading delay
            if hasattr(self, 'video_label'):
                self.video_label.config(image=photo)
                self.video_label.image = photo  # Keep reference to prevent garbage collection
            
        except Exception:
            pass  # Reduce error logging to prevent console spam
    
    def update_statistics(self, results):
        """Update detection statistics"""
        self.stats['weapons_detected'] += len(results['weapons'])
        self.stats['people_detected'] += len(results['people'])
        self.stats['faces_analyzed'] += len(results['faces'])
    
    def update_stats_display(self):
        """Update statistics display in GUI"""
        def update_gui():
            for stat_name, value in self.stats.items():
                if stat_name in self.stats_vars:
                    self.stats_vars[stat_name].config(text=str(value))
        
        self.root.after(0, update_gui)
    
    def configure_email(self):
        """Configure Gmail settings"""
        email_window = tk.Toplevel(self.root)
        email_window.title("📧 Gmail Setup for Automatic Alerts")
        email_window.geometry("550x450")
        email_window.configure(bg='#2c3e50')
        email_window.transient(self.root)
        email_window.grab_set()
        
        # Title
        tk.Label(email_window, text="📧 GMAIL ALERT CONFIGURATION", 
                font=('Arial', 16, 'bold'), bg='#2c3e50', fg='white').pack(pady=15)
        
        tk.Label(email_window, text=f"Alerts will be sent to: {self.user_email}", 
                font=('Arial', 12), bg='#2c3e50', fg='#2ecc71').pack(pady=5)
        
        # Form frame
        form_frame = tk.Frame(email_window, bg='#34495e', relief='raised', bd=2)
        form_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Instructions
        tk.Label(form_frame, text="📱 Gmail App Password Setup:", 
                font=('Arial', 12, 'bold'), bg='#34495e', fg='#3498db').pack(pady=10)
        
        instructions = [
            "1. Go to Google Account settings",
            "2. Enable 2-Factor Authentication", 
            "3. Generate App Password for 'Mail'",
            "4. Use the 16-character App Password below"
        ]
        
        for instruction in instructions:
            tk.Label(form_frame, text=instruction, font=('Arial', 10), 
                    bg='#34495e', fg='white').pack(anchor='w', padx=15)
        
        # Gmail email
        tk.Label(form_frame, text="Gmail Address (for sending):", 
                bg='#34495e', fg='white', font=('Arial', 11, 'bold')).pack(anchor='w', padx=15, pady=(15, 5))
        sender_entry = tk.Entry(form_frame, font=('Arial', 11), width=45)
        sender_entry.pack(padx=15, pady=(0, 10))
        sender_entry.insert(0, self.email_config['sender_email'])
        
        # App password
        tk.Label(form_frame, text="Gmail App Password:", 
                bg='#34495e', fg='white', font=('Arial', 11, 'bold')).pack(anchor='w', padx=15, pady=(0, 5))
        password_entry = tk.Entry(form_frame, show="*", font=('Arial', 11), width=45)
        password_entry.pack(padx=15, pady=(0, 15))
        password_entry.insert(0, self.email_config['sender_password'])
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg='#34495e')
        btn_frame.pack(fill='x', padx=15, pady=15)
        
        def test_email():
            try:
                msg = MIMEText("🧪 Test email from Complete Surveillance System\n\nYour automatic threat alerts are working correctly!")
                msg['Subject'] = "🧪 Test - Surveillance System Ready"
                msg['From'] = sender_entry.get()
                msg['To'] = self.user_email
                
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender_entry.get(), password_entry.get())
                server.sendmail(sender_entry.get(), self.user_email, msg.as_string())
                server.quit()
                
                messagebox.showinfo("✅ Success", f"Test email sent to {self.user_email}!\n\nAutomatic alerts are now active.")
                
            except Exception as e:
                messagebox.showerror("❌ Failed", f"Email test failed:\n{str(e)}")
        
        def save_config():
            self.email_config['sender_email'] = sender_entry.get()
            self.email_config['sender_password'] = password_entry.get()
            # Only enable if both fields are provided
            if not self.email_config['sender_email'] or not self.email_config['sender_password']:
                messagebox.showwarning("⚠️ Incomplete", "Please provide both Gmail address and App Password to enable email alerts.\n\nYou can also set environment variables SSS_EMAIL and SSS_EMAIL_PASS for secure storage.")
                return

            self.email_config['enabled'] = True

            self.save_email_config()
            messagebox.showinfo("✅ Saved", "Gmail configuration saved!\n\nAutomatic threat alerts enabled.")
            self.log_message("📧 Gmail alerts configured and enabled")
            email_window.destroy()
        
        tk.Button(btn_frame, text="🧪 Test Email", command=test_email,
                 bg='#3498db', fg='white', font=('Arial', 11, 'bold')).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="💾 Save & Enable", command=save_config,
                 bg='#2ecc71', fg='white', font=('Arial', 11, 'bold')).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="❌ Cancel", command=email_window.destroy,
                 bg='#e74c3c', fg='white', font=('Arial', 11, 'bold')).pack(side='right', padx=5)
    
    def load_email_config(self):
        """Load email configuration"""
        try:
            config_path = Path("configs/email_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                    self.email_config.update(saved_config)
        except Exception as e:
            self.log_message(f"Email config load error: {e}")
    def save_email_config(self):
        """Save email configuration"""
        try:
            config_path = Path("configs/email_config.json")
            with open(config_path, 'w') as f:
                json.dump(self.email_config, f, indent=2)
        except Exception as e:
            self.log_message(f"Email config save error: {e}")

    def auto_configure_email(self):
        """Auto-configure email if config file exists"""
        config_path = Path("configs/email_config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)

                # Support both new and legacy key names
                sender = file_config.get('sender_email') or file_config.get('email') or ''
                passwd = file_config.get('sender_password') or file_config.get('password') or ''

                if sender and passwd:
                    self.email_config.update({
                        'enabled': True,
                        'sender_email': sender,
                        'sender_password': passwd,
                        'use_app_password': True
                    })
                    self.log_message("✅ Email auto-configured from config file")

            except Exception as e:
                self.log_message(f"❌ Auto-config failed: {e}")
        else:
            # Create a safe example template file (no secrets)
            template_config = {
                "sender_email": "your_email@gmail.com",
                "sender_password": "your_app_password_here",
                "instructions": "Enable 2FA in Google and create an App Password for Mail"
            }
            try:
                example_path = Path("configs/email_config.json.example")
                with open(example_path, 'w') as f:
                    json.dump(template_config, f, indent=2)
                self.log_message("📝 Created email config example: configs/email_config.json.example")
            except Exception as e:
                self.log_message(f"❌ Template creation failed: {e}")

    def save_frame(self):
        """Save current frame"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"alerts/manual_save_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                self.log_message(f"💾 Frame saved: {filename}")
                messagebox.showinfo("💾 Saved", f"Frame saved to {filename}")

    def clear_log(self):
        """Clear activity log"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("📝 Activity log cleared")

    def log_message(self, message):
        """Add message to activity log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        def update_log():
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)

        # Safely update the UI from other threads
        try:
            self.root.after(0, update_log)
        except Exception:
            # If UI not available, fallback to printing
            print(log_entry)

    def run(self):
        """Run the surveillance system"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def on_close(self):
        """Handle application close"""
        if self.is_monitoring:
            self.stop_monitoring()
        # Shutdown inference executor if running
        try:
            if hasattr(self, 'executor') and self.executor:
                self.executor.shutdown(wait=False)
        except Exception:
            pass
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass


def preload_models():
    """Preload AI models before user authentication to avoid startup wait after login.
    Returns a dict of loaded models (keys: 'weapon', 'crowd', 'emotion').
    """
    models = {}
    try:
        print("🔄 Preloading AI models (this may take a moment)...")
        if YOLO_AVAILABLE:
            weapon_paths = [
                "AI_models/Object_detection/best.pt",
                "AI_models/Object_detection/yolov8n.pt",
                "Object_detection/best.pt",
                "yolov8n.pt"
            ]
            for path in weapon_paths:
                try:
                    if os.path.exists(path):
                        models['weapon'] = YOLO(path)
                        print(f"✅ Weapon model loaded: {path}")
                        # try move to CUDA if available
                        try:
                            if TORCH_AVAILABLE and torch.cuda.is_available():
                                m = models['weapon']
                                if hasattr(m, 'model') and hasattr(m.model, 'to'):
                                    m.model.to('cuda')
                                    print("🔧 Weapon model moved to CUDA")
                        except Exception:
                            pass
                        break
                except Exception:
                    continue

            crowd_paths = [
                "AI_models/crowddetection/yolov8s.pt",
                "AI_models/crowddetection/yolov8n.pt",
                "crowddetection/yolov8s.pt",
                "yolov8n.pt"
            ]
            for path in crowd_paths:
                try:
                    if os.path.exists(path):
                        models['crowd'] = YOLO(path)
                        print(f"✅ Crowd model loaded: {path}")
                        try:
                            if TORCH_AVAILABLE and torch.cuda.is_available():
                                m = models['crowd']
                                if hasattr(m, 'model') and hasattr(m.model, 'to'):
                                    m.model.to('cuda')
                                    print("🔧 Crowd model moved to CUDA")
                        except Exception:
                            pass
                        break
                except Exception:
                    continue

        if FER_AVAILABLE:
            models['emotion'] = FER(mtcnn=True)
            print("✅ Emotion model loaded")

    except Exception as e:
        print(f"❌ Preload models error: {e}")

    print("🔍 Preload complete. Models available:", 
        f"weapon={'yes' if 'weapon' in models else 'no'}, ",
        f"crowd={'yes' if 'crowd' in models else 'no'}, ",
        f"emotion={'yes' if 'emotion' in models else 'no'}")
    return models


def main():
    """Main application entry point"""
    print("🛡️ Complete Smart Surveillance System")
    print("=" * 50)
    
    # Initialize database
    db_manager = DatabaseManager()
    
    try:
        # Preload AI models before asking user to login (faster UX after login)
        print("🔄 Preloading AI models before authentication...")
        preloaded = preload_models()

        # Step 1: User Authentication (runs after models begin loading)
        print("🔐 User authentication required...")
        auth_window = AuthenticationWindow(db_manager)
        auth_window.root.mainloop()

        if auth_window.user_id is None:
            print("❌ Authentication cancelled")
            return

        auth_window.root.destroy()
        print(f"✅ User authenticated: {auth_window.user_email}")

        # Step 2: Start Complete Surveillance System with preloaded models
        print("🛡️ Starting Complete Surveillance System...")
        system = CompleteSurveillanceSystem(
            db_manager,
            auth_window.user_id,
            auth_window.user_email,
            preloaded_models=preloaded
        )
        
        print("🚀 System ready! Starting GUI...")
        system.run()
        
    except KeyboardInterrupt:
        print("\n👋 System shutdown requested")
    except Exception as e:
        print(f"❌ System error: {e}")
        messagebox.showerror("System Error", f"Critical error: {e}")
    
    print("🛡️ Complete Surveillance System stopped")

if __name__ == "__main__":
    main()