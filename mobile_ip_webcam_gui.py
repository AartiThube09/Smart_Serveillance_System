#!/usr/bin/env python3
"""
🛡️ Mobile IP Webcam GUI - Simple Interface
Integrates IP webcam with all detection models and alert generation
"""

import cv2
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading
import queue
import time
import datetime
import json
import os
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
    from email.mime.image import MIMEImage
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

class MobileIPWebcamGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🛡️ Smart Surveillance System")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')
        
        # Configuration
        self.ip_webcam_url = "http://192.168.0.107:8080/video"
        self.backup_camera = 0
        self.alert_cooldown = 10
        
        # Email Configuration
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': '',
            'sender_password': '',
            'recipient_emails': [],
            'enabled': False
        }
        
        # Models (lazy loading)
        self.models = {}
        self.model_paths = {
            'weapon': "Object_detection/best.pt",
            'crowd': "crowddetection/yolov8s.pt",
            'expression': None  # FER model auto-downloads
        }
        self.models_loaded = {
            'weapon': False,
            'crowd': False,
            'expression': False
        }
        
        # Model selection (user can choose which models to use)
        self.active_models = {
            'weapon': True,   # Default: Enable weapon detection
            'crowd': True,    # Default: Enable crowd detection  
            'expression': False  # Default: Disable expression (slower)
        }
        
        # Video capture
        self.cap = None
        self.frame_queue = queue.Queue(maxsize=5)
        self.detection_results = {}
        
        # Threading
        self.running = False
        self.detection_thread = None
        
        # Alerts
        self.alerts_folder = Path("alerts")
        self.alerts_folder.mkdir(exist_ok=True)
        self.last_alert_time = {}
        
        # Statistics
        self.stats = {
            "frames_processed": 0,
            "alerts_generated": 0,
            "people_detected": 0,
            "weapons_detected": 0
        }
        
        self.setup_gui()
        self.load_email_config()
        self.update_email_status()
        
    def load_model_on_demand(self, model_name):
        """Load specific model only when needed (lazy loading)"""
        if self.models_loaded[model_name] or not self.active_models[model_name]:
            return True
        
        print(f"📦 Loading {model_name} model...")
        
        try:
            if model_name == 'weapon' and YOLO_AVAILABLE:
                if os.path.exists(self.model_paths['weapon']):
                    self.models['weapon'] = YOLO(self.model_paths['weapon'])
                    print("✅ Weapon detection model loaded")
                    self.models_loaded['weapon'] = True
                    return True
                else:
                    print(f"❌ Weapon model not found: {self.model_paths['weapon']}")
                    
            elif model_name == 'crowd' and YOLO_AVAILABLE:
                if os.path.exists(self.model_paths['crowd']):
                    self.models['crowd'] = YOLO(self.model_paths['crowd'])
                    print("✅ Crowd detection model loaded")
                    self.models_loaded['crowd'] = True
                    return True
                else:
                    print(f"❌ Crowd model not found: {self.model_paths['crowd']}")
                    
            elif model_name == 'expression' and FER_AVAILABLE:
                self.models['expression'] = FER(mtcnn=True)
                print("✅ Expression detection model loaded")
                self.models_loaded['expression'] = True
                return True
                
        except Exception as e:
            print(f"❌ Error loading {model_name} model: {e}")
            
        return False
    
    def get_available_models(self):
        """Check which models are available without loading them"""
        available = {}
        
        # Check weapon model
        available['weapon'] = YOLO_AVAILABLE and os.path.exists(self.model_paths['weapon'])
        
        # Check crowd model  
        available['crowd'] = YOLO_AVAILABLE and os.path.exists(self.model_paths['crowd'])
        
        # Check expression model (always available if FER installed)
        available['expression'] = FER_AVAILABLE
        
        return available
    
    def setup_gui(self):
        """Setup the GUI interface"""
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top control panel
        control_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = tk.Label(control_frame, text="🛡️ Smart Surveillance System", 
                              font=('Arial', 16, 'bold'), bg='#34495e', fg='white')
        title_label.pack(pady=10)
        
        # Connection frame
        conn_frame = tk.Frame(control_frame, bg='#34495e')
        conn_frame.pack(pady=5)
        
        tk.Label(conn_frame, text="IP Webcam URL:", bg='#34495e', fg='white').pack(side=tk.LEFT, padx=5)
        
        self.ip_entry = tk.Entry(conn_frame, width=30, font=('Arial', 10))
        self.ip_entry.insert(0, self.ip_webcam_url)
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        
        self.connect_btn = tk.Button(conn_frame, text="Connect", command=self.connect_camera,
                                   bg='#3498db', fg='white', font=('Arial', 10, 'bold'))
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        # Control buttons
        btn_frame = tk.Frame(control_frame, bg='#34495e')
        btn_frame.pack(pady=5)
        
        self.start_btn = tk.Button(btn_frame, text="▶ Start Monitoring", command=self.start_monitoring,
                                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'), width=15)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹ Stop Monitoring", command=self.stop_monitoring,
                                bg='#e74c3c', fg='white', font=('Arial', 10, 'bold'), width=15, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = tk.Button(btn_frame, text="💾 Save Frame", command=self.save_frame,
                                bg='#f39c12', fg='white', font=('Arial', 10, 'bold'), width=15)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.email_btn = tk.Button(btn_frame, text="📧 Configure Email", command=self.configure_email,
                                 bg='#9b59b6', fg='white', font=('Arial', 10, 'bold'), width=15)
        self.email_btn.pack(side=tk.LEFT, padx=5)
        
        # Main content area
        content_frame = tk.Frame(main_frame, bg='#2c3e50')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Video feed
        video_frame = tk.Frame(content_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(video_frame, text="📹 Live Video Feed", bg='#34495e', fg='white', 
                font=('Arial', 12, 'bold')).pack(pady=5)
        
        self.video_label = tk.Label(video_frame, bg='black', text="No video feed", 
                                   fg='white', font=('Arial', 14))
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right side - Detection results and controls
        right_frame = tk.Frame(content_frame, bg='#2c3e50')
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Status panel
        status_frame = tk.Frame(right_frame, bg='#34495e', relief=tk.RAISED, bd=2, width=300)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        status_frame.pack_propagate(False)
        
        tk.Label(status_frame, text="📊 Detection Status", bg='#34495e', fg='white', 
                font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Detection counters
        self.status_labels = {}
        status_items = [("Camera Status", "Disconnected"), ("Email Alerts", "Disabled"), 
                       ("Weapons Detected", "0"), ("People Count", "0"), ("Threat Level", "Low")]
        
        for item, default in status_items:
            frame = tk.Frame(status_frame, bg='#34495e')
            frame.pack(fill=tk.X, padx=10, pady=2)
            
            tk.Label(frame, text=f"{item}:", bg='#34495e', fg='white', 
                    font=('Arial', 9)).pack(side=tk.LEFT)
            
            label = tk.Label(frame, text=default, bg='#34495e', fg='#3498db', 
                           font=('Arial', 9, 'bold'))
            label.pack(side=tk.RIGHT)
            self.status_labels[item] = label
        
        # Alert panel
        alert_frame = tk.Frame(right_frame, bg='#34495e', relief=tk.RAISED, bd=2, width=300)
        alert_frame.pack(fill=tk.BOTH, expand=True)
        alert_frame.pack_propagate(False)
        
        tk.Label(alert_frame, text="🚨 Alert Messages", bg='#34495e', fg='white', 
                font=('Arial', 12, 'bold')).pack(pady=5)
        
        self.alert_text = scrolledtext.ScrolledText(alert_frame, bg='black', fg='#00ff00', 
                                                   font=('Courier', 9), height=15)
        self.alert_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Clear alerts button
        clear_btn = tk.Button(alert_frame, text="Clear Alerts", command=self.clear_alerts,
                            bg='#95a5a6', fg='white', font=('Arial', 9))
        clear_btn.pack(pady=5)
        
        # Status bar
        status_bar = tk.Frame(main_frame, bg='#34495e', relief=tk.SUNKEN, bd=1)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Connect to your mobile IP webcam")
        status_label = tk.Label(status_bar, textvariable=self.status_var, bg='#34495e', 
                               fg='white', font=('Arial', 9))
        status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
    def connect_camera(self):
        """Connect to IP webcam or laptop camera"""
        url = self.ip_entry.get().strip()
        if not url.startswith("http"):
            url = f"http://{url}:8080/video"
        
        self.log_message(f"Attempting to connect to: {url}")
        
        # Try IP webcam first with timeout
        self.cap = cv2.VideoCapture(url)
        
        # Give it a moment to initialize and test if it can read a frame
        if self.cap.isOpened():
            ret, test_frame = self.cap.read()
            if ret and test_frame is not None:
                self.log_message("✅ Connected to IP webcam")
                self.status_labels["Camera Status"].config(text="IP Webcam", fg='#27ae60')
                connection_successful = True
            else:
                self.cap.release()
                connection_successful = False
        else:
            connection_successful = False
        
        # If IP webcam failed, try laptop camera
        if not connection_successful:
            self.log_message("❌ IP webcam failed, trying laptop camera...")
            self.cap = cv2.VideoCapture(self.backup_camera)
            
            if not self.cap.isOpened():
                self.log_message("❌ No camera available!")
                messagebox.showerror("Camera Error", "Cannot connect to any camera!")
                return False
            else:
                self.log_message("✅ Connected to laptop camera")
                self.status_labels["Camera Status"].config(text="Laptop Camera", fg='#f39c12')
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for real-time
        
        self.status_var.set("Camera connected - Ready to start monitoring")
        return True
    
    def start_monitoring(self):
        """Start the monitoring process"""
        if not self.cap or not self.cap.isOpened():
            if not self.connect_camera():
                return
        
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Start detection thread
        self.detection_thread = threading.Thread(target=self.detection_worker, daemon=True)
        self.detection_thread.start()
        
        # Start video update
        self.update_video()
        
        self.log_message("🚀 Monitoring started!")
        self.status_var.set("Monitoring active - Analyzing video feed")
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.status_labels["Camera Status"].config(text="Disconnected", fg='#e74c3c')
        self.status_var.set("Monitoring stopped")
        self.log_message("⏹ Monitoring stopped!")
    
    def detection_worker(self):
        """Background detection processing"""
        frame_count = 0
        
        while self.running:
            try:
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get(timeout=1)
                    frame_count += 1
                    
                    # Process frame every few frames for performance
                    if frame_count % 3 == 0:
                        results = self.process_frame(frame)
                        self.detection_results = results
                        
                        # Check for threats and generate alerts
                        self.check_threats(results, frame)
                        
                        # Update statistics
                        self.update_stats(results)
                        
                        self.stats["frames_processed"] += 1
                
            except queue.Empty:
                continue
            except Exception as e:
                self.log_message(f"Detection error: {e}")
                time.sleep(0.1)
    
    def process_frame(self, frame):
        """Process frame with all detection models"""
        results = {
            'weapons': [],
            'people': [],
            'faces': [],
            'threat_level': 'Low'
        }
        
        try:
            # Weapon detection
            if 'weapon' in self.models:
                weapon_results = self.models['weapon'].predict(frame, conf=0.6, verbose=False)
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
                crowd_results = self.models['crowd'].predict(frame, conf=0.5, verbose=False)
                for result in crowd_results:
                    if result.boxes is not None:
                        for box, cls in zip(result.boxes.xyxy, result.boxes.cls):
                            if int(cls) == 0:  # Person class
                                results['people'].append([int(x) for x in box])
            
            # Facial expression detection
            if 'expression' in self.models:
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
                    pass  # FER can be unstable, continue without crashing
            
            # Determine threat level
            if results['weapons']:
                results['threat_level'] = 'High'
            elif len(results['people']) > 5:
                results['threat_level'] = 'Medium'
            elif any(face['emotion'] in ['angry', 'fear'] and face['confidence'] > 0.8 
                    for face in results['faces']):
                results['threat_level'] = 'Medium'
            else:
                results['threat_level'] = 'Low'
        
        except Exception as e:
            self.log_message(f"Processing error: {e}")
        
        return results
    
    def check_threats(self, results, frame):
        """Check for threats and generate alerts with specific sounds and emails"""
        threat_detected = False
        alert_message = ""
        threat_type = ""
        sound_pattern = []
        
        current_time = time.time()
        
        # Check weapons (HIGHEST PRIORITY)
        if results['weapons']:
            if 'weapon' not in self.last_alert_time or \
               current_time - self.last_alert_time['weapon'] > self.alert_cooldown:
                threat_detected = True
                threat_type = "WEAPON"
                
                # Build detailed weapon message
                weapon_details = []
                for weapon in results['weapons']:
                    weapon_details.append(f"{weapon['class']} (confidence: {weapon['confidence']:.2f})")
                
                alert_message = "🚨 CRITICAL THREAT: WEAPON DETECTED!\n"
                alert_message += f"Weapons found: {', '.join(weapon_details)}\n"
                alert_message += f"Total weapons: {len(results['weapons'])}\n"
                alert_message += "⚠️ IMMEDIATE ACTION REQUIRED!"
                
                # Urgent sound pattern for weapons
                sound_pattern = [(1500, 200), (1000, 200), (1500, 200), (1000, 200), (1500, 500)]
                
                self.last_alert_time['weapon'] = current_time
                self.stats['weapons_detected'] += len(results['weapons'])
        
        # Check crowd (MEDIUM PRIORITY)
        people_count = len(results['people'])
        if people_count > 10:  # Lowered threshold for better detection
            if 'crowd' not in self.last_alert_time or \
               current_time - self.last_alert_time['crowd'] > self.alert_cooldown:
                
                if people_count > 15:
                    threat_detected = True
                    threat_type = "OVERCROWDING"
                    alert_message = "👥 OVERCROWDING ALERT!\n"
                    alert_message += f"People detected: {people_count}\n"
                    alert_message += "Threshold exceeded: Critical level\n"
                    alert_message += "⚠️ Crowd control may be needed!"
                    
                    # Crowd alert sound pattern
                    sound_pattern = [(800, 300), (600, 300), (800, 300)]
                    
                elif people_count > 10:
                    threat_detected = True
                    threat_type = "CROWD_MEDIUM"
                    alert_message = "👥 CROWD ALERT!\n"
                    alert_message += f"People detected: {people_count}\n"
                    alert_message += "Alert level: Medium\n"
                    alert_message += "ℹ️ Monitor crowd density"
                    
                    # Medium crowd sound
                    sound_pattern = [(700, 400), (500, 400)]
                
                self.last_alert_time['crowd'] = current_time
        
        # Check suspicious emotions/behavior (MEDIUM PRIORITY)
        suspicious_faces = [face for face in results['faces'] 
                          if face['emotion'] in ['angry', 'fear', 'disgust'] and face['confidence'] > 0.7]
        if suspicious_faces:
            if 'emotion' not in self.last_alert_time or \
               current_time - self.last_alert_time['emotion'] > self.alert_cooldown:
                threat_detected = True
                threat_type = "SUSPICIOUS_BEHAVIOR"
                
                # Build emotion details
                emotion_details = []
                for face in suspicious_faces:
                    emotion_details.append(f"{face['emotion']} ({face['confidence']:.2f})")
                
                alert_message = "😠 SUSPICIOUS BEHAVIOR DETECTED!\n"
                alert_message += f"Suspicious emotions: {', '.join(emotion_details)}\n"
                alert_message += f"Faces showing suspicious behavior: {len(suspicious_faces)}\n"
                alert_message += "⚠️ Monitor for potential threats!"
                
                # Suspicious behavior sound pattern
                sound_pattern = [(900, 250), (700, 250), (900, 250)]
                
                self.last_alert_time['emotion'] = current_time
        
        # Process alerts if any threat detected
        if threat_detected:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            full_message = f"[{timestamp}] {alert_message}"
            self.log_message(full_message)
            
            # Save alert to file
            alert_data = self.save_alert(results, frame, alert_message)
            
            # Send specific email alert based on threat type
            if self.email_config['enabled'] and alert_data:
                email_sent = self.send_threat_email(threat_type, alert_message, results, alert_data['frame_path'])
                if email_sent:
                    self.log_message(f"📧 {threat_type} email alert sent!")
                else:
                    self.log_message(f"❌ Failed to send {threat_type} email alert")
            
            # Play specific sound alert based on threat type
            self.play_threat_sound(threat_type, sound_pattern)
            
            self.stats['alerts_generated'] += 1
            
            # Visual alert in GUI
            self.show_visual_alert(threat_type, alert_message)
    
    def save_alert(self, results, frame, message):
        """Save alert data and frame to files"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save frame
        frame_path = self.alerts_folder / f"alert_frame_{timestamp}.jpg"
        cv2.imwrite(str(frame_path), frame)
        
        # Save alert data
        alert_data = {
            'timestamp': timestamp,
            'message': message,
            'detection_results': results,
            'frame_path': str(frame_path)
        }
        
        alert_path = self.alerts_folder / f"alert_data_{timestamp}.json"
        with open(alert_path, 'w') as f:
            json.dump(alert_data, f, indent=2)
        
        return alert_data
    
    def update_stats(self, results):
        """Update GUI statistics"""
        def update_gui():
            self.status_labels["Weapons Detected"].config(text=str(len(results['weapons'])))
            self.status_labels["People Count"].config(text=str(len(results['people'])))
            
            threat_level = results['threat_level']
            color = {'Low': '#27ae60', 'Medium': '#f39c12', 'High': '#e74c3c'}[threat_level]
            self.status_labels["Threat Level"].config(text=threat_level, fg=color)
        
        self.root.after(0, update_gui)
    
    def update_video(self):
        """Update video display"""
        if not self.running or not self.cap:
            return
        
        ret, frame = self.cap.read()
        if ret:
            # Add frame to processing queue
            if not self.frame_queue.full():
                self.frame_queue.put(frame.copy())
            
            # Draw detections if available
            if hasattr(self, 'detection_results'):
                frame = self.draw_detections(frame, self.detection_results)
            
            # Convert frame for display
            frame = cv2.resize(frame, (640, 480))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(image)
            
            self.video_label.config(image=photo)
            self.video_label.image = photo
        
        # Schedule next update
        if self.running:
            self.root.after(30, self.update_video)  # ~30 FPS
    
    def draw_detections(self, frame, results):
        """Draw detection boxes on frame"""
        # Draw weapons (red boxes)
        for weapon in results.get('weapons', []):
            bbox = weapon['bbox']
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 3)
            cv2.putText(frame, f"WEAPON: {weapon['class']}", 
                       (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Draw people (green boxes with green labels)
        for i, person_bbox in enumerate(results.get('people', []), 1):
            cv2.rectangle(frame, (person_bbox[0], person_bbox[1]), 
                        (person_bbox[2], person_bbox[3]), (0, 255, 0), 2)
            cv2.putText(frame, f"PERSON {i}", 
                    (person_bbox[0], person_bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw faces with emotions
        for face in results.get('faces', []):
            bbox = face['bbox']
            emotion = face['emotion']
            confidence = face['confidence']
            color = (0, 0, 255) if emotion in ['angry', 'fear'] else (0, 255, 255)
            
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            cv2.putText(frame, f"{emotion}: {confidence:.2f}", (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Add info overlay
        overlay_text = f"People: {len(results.get('people', []))} | Weapons: {len(results.get('weapons', []))} | Faces: {len(results.get('faces', []))}"
        cv2.putText(frame, overlay_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return frame
    
    def save_frame(self):
        """Save current frame"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"saved_frame_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                self.log_message(f"💾 Frame saved: {filename}")
                messagebox.showinfo("Frame Saved", f"Frame saved as {filename}")
    
    def clear_alerts(self):
        """Clear alert messages"""
        self.alert_text.delete(1.0, tk.END)
    
    def configure_email(self):
        """Configure email settings for alerts"""
        if not EMAIL_AVAILABLE:
            messagebox.showerror("Email Not Available", 
                                "Email libraries not installed. Install with: pip install secure-smtplib")
            return
        
        # Create email configuration dialog
        email_window = tk.Toplevel(self.root)
        email_window.title("📧 Email Alert Configuration")
        email_window.geometry("500x400")
        email_window.configure(bg='#34495e')
        email_window.resizable(False, False)
        
        # Center the window
        email_window.transient(self.root)
        email_window.grab_set()
        
        # Title
        tk.Label(email_window, text="📧 Email Alert Configuration", 
                font=('Arial', 16, 'bold'), bg='#34495e', fg='white').pack(pady=10)
        
        # Main frame
        main_frame = tk.Frame(email_window, bg='#34495e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Gmail setup instructions
        info_frame = tk.Frame(main_frame, bg='#2c3e50', relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(info_frame, text="📱 Gmail Setup Instructions:", 
                font=('Arial', 12, 'bold'), bg='#2c3e50', fg='#3498db').pack(pady=5)
        
        instructions = [
            "1. Enable 2-Factor Authentication in Google Account",
            "2. Go to Security → App passwords",
            "3. Generate password for 'Mail'",
            "4. Use the App Password (not your regular password)"
        ]
        
        for instruction in instructions:
            tk.Label(info_frame, text=instruction, font=('Arial', 9), 
                    bg='#2c3e50', fg='white').pack(anchor='w', padx=10)
        
        # Email configuration form
        form_frame = tk.Frame(main_frame, bg='#34495e')
        form_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Sender email
        tk.Label(form_frame, text="Your Gmail Address:", bg='#34495e', fg='white').pack(anchor='w')
        sender_entry = tk.Entry(form_frame, width=50, font=('Arial', 10))
        sender_entry.pack(fill=tk.X, pady=(0, 10))
        sender_entry.insert(0, self.email_config['sender_email'])
        
        # App password
        tk.Label(form_frame, text="Gmail App Password:", bg='#34495e', fg='white').pack(anchor='w')
        password_entry = tk.Entry(form_frame, width=50, font=('Arial', 10), show='*')
        password_entry.pack(fill=tk.X, pady=(0, 10))
        password_entry.insert(0, self.email_config['sender_password'])
        
        # Recipients
        tk.Label(form_frame, text="Alert Recipients (one per line):", bg='#34495e', fg='white').pack(anchor='w')
        recipients_text = tk.Text(form_frame, height=4, font=('Arial', 10))
        recipients_text.pack(fill=tk.X, pady=(0, 10))
        recipients_text.insert('1.0', '\n'.join(self.email_config['recipient_emails']))
        
        # Enable/disable checkbox
        enable_var = tk.BooleanVar(value=self.email_config['enabled'])
        enable_check = tk.Checkbutton(form_frame, text="Enable Email Alerts", 
                                    variable=enable_var, bg='#34495e', fg='white',
                                    selectcolor='#2c3e50', font=('Arial', 10))
        enable_check.pack(anchor='w', pady=5)
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg='#34495e')
        btn_frame.pack(fill=tk.X, pady=10)
        
        def test_email():
            """Test email configuration"""
            sender = sender_entry.get().strip()
            password = password_entry.get().strip()
            recipients = [line.strip() for line in recipients_text.get('1.0', tk.END).split('\n') if line.strip()]
            
            if not sender or not password or not recipients:
                messagebox.showerror("Missing Information", "Please fill all fields")
                return
            
            # Test email sending
            try:
                import smtplib
                from email.mime.text import MIMEText
                
                msg = MIMEText("🛡️ Smart Surveillance System - Email Alert Test\n\nThis is a test email to verify your email configuration is working correctly.")
                msg['Subject'] = "🧪 Smart Surveillance System - Email Test"
                msg['From'] = sender
                msg['To'] = recipients[0]
                
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(sender, password)
                    server.send_message(msg)
                
                messagebox.showinfo("Test Successful", f"Test email sent successfully to {recipients[0]}!")
                
            except Exception as e:
                messagebox.showerror("Test Failed", f"Email test failed:\n{str(e)}\n\nCheck your credentials and internet connection.")
        
        def save_config():
            """Save email configuration"""
            self.email_config['sender_email'] = sender_entry.get().strip()
            self.email_config['sender_password'] = password_entry.get().strip()
            self.email_config['recipient_emails'] = [line.strip() for line in recipients_text.get('1.0', tk.END).split('\n') if line.strip()]
            self.email_config['enabled'] = enable_var.get()
            
            # Save to file
            try:
                config_path = Path("email_config.json")
                with open(config_path, 'w') as f:
                    # Don't save password to file for security
                    safe_config = self.email_config.copy()
                    safe_config['sender_password'] = '***SAVED***' if safe_config['sender_password'] else ''
                    json.dump(safe_config, f, indent=2)
                
                messagebox.showinfo("Configuration Saved", "Email configuration saved successfully!")
                self.log_message(f"📧 Email alerts {'enabled' if enable_var.get() else 'disabled'}")
                self.update_email_status()
                email_window.destroy()
                
            except Exception as e:
                messagebox.showerror("Save Failed", f"Failed to save configuration:\n{str(e)}")
        
        # Buttons
        tk.Button(btn_frame, text="🧪 Test Email", command=test_email,
                 bg='#3498db', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="💾 Save Configuration", command=save_config,
                 bg='#27ae60', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="❌ Cancel", command=email_window.destroy,
                 bg='#e74c3c', fg='white', font=('Arial', 10)).pack(side=tk.RIGHT, padx=5)
        
        # Load existing configuration if available
        self.load_email_config()
    
    def load_email_config(self):
        """Load email configuration from file"""
        try:
            config_path = Path("email_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                    self.email_config.update(saved_config)
                    # Don't load the saved password placeholder
                    if self.email_config['sender_password'] == '***SAVED***':
                        self.email_config['sender_password'] = ''
        except Exception as e:
            self.log_message(f"Failed to load email config: {e}")
    
    def update_email_status(self):
        """Update email status in GUI"""
        if self.email_config['enabled'] and self.email_config['recipient_emails']:
            status = f"Enabled ({len(self.email_config['recipient_emails'])} recipients)"
            color = '#27ae60'  # Green
        else:
            status = "Disabled"
            color = '#e74c3c'  # Red
        
        if "Email Alerts" in self.status_labels:
            self.status_labels["Email Alerts"].config(text=status, fg=color)
    
    def play_threat_sound(self, threat_type, sound_pattern):
        """Play specific sound alerts based on threat type"""
        if not SOUND_AVAILABLE:
            return
        
        try:
            import winsound
            
            if threat_type == "WEAPON":
                # Urgent rapid beeps for weapons
                for freq, duration in sound_pattern:
                    winsound.Beep(freq, duration)
                    time.sleep(0.1)
                    
            elif threat_type in ["OVERCROWDING", "CROWD_MEDIUM"]:
                # Lower pitch beeps for crowd
                for freq, duration in sound_pattern:
                    winsound.Beep(freq, duration)
                    time.sleep(0.2)
                    
            elif threat_type == "SUSPICIOUS_BEHAVIOR":
                # Warning beeps for suspicious behavior
                for freq, duration in sound_pattern:
                    winsound.Beep(freq, duration)
                    time.sleep(0.15)
                    
        except Exception as e:
            self.log_message(f"Sound alert failed: {e}")
    
    def show_visual_alert(self, threat_type, message):
        """Show visual alert popup for critical threats"""
        if threat_type == "WEAPON":
            # Critical weapon alert popup
            messagebox.showwarning("🚨 CRITICAL WEAPON ALERT", 
                                 f"WEAPON DETECTED!\n\nTime: {datetime.datetime.now().strftime('%H:%M:%S')}\n\n{message}\n\nIMMEDIATE ACTION REQUIRED!")
    
    def send_threat_email(self, threat_type, alert_message, detection_results, frame_path):
        """Send specific email based on threat type"""
        if not EMAIL_AVAILABLE or not self.email_config['enabled'] or not self.email_config['recipient_emails']:
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.image import MIMEImage
            
            # Create message based on threat type
            msg = MIMEMultipart()
            
            # Set subject based on threat severity
            if threat_type == "WEAPON":
                msg['Subject'] = "🚨 CRITICAL SECURITY ALERT - WEAPON DETECTED"
                priority = "HIGH"
            elif threat_type in ["OVERCROWDING", "CROWD_MEDIUM"]:
                msg['Subject'] = "⚠️ CROWD ALERT - Smart Surveillance System"
                priority = "MEDIUM"
            elif threat_type == "SUSPICIOUS_BEHAVIOR":
                msg['Subject'] = "😠 SUSPICIOUS BEHAVIOR - Smart Surveillance System"
                priority = "MEDIUM"
            else:
                msg['Subject'] = "🚨 SECURITY ALERT - Smart Surveillance System"
                priority = "MEDIUM"
            
            msg['From'] = self.email_config['sender_email']
            msg['To'] = ', '.join(self.email_config['recipient_emails'])
            msg['X-Priority'] = '1' if priority == "HIGH" else '3'  # Email priority
            
            # Create detailed email body
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            body = f"""
🛡️ SMART SURVEILLANCE SYSTEM - SECURITY ALERT

⚠️ ALERT TYPE: {threat_type.replace('_', ' ')}
⏰ DETECTION TIME: {timestamp}
🚨 PRIORITY LEVEL: {priority}

📋 ALERT DETAILS:
{alert_message}

📊 TECHNICAL INFORMATION:
"""
            
            # Add specific detection details
            if 'weapons' in detection_results and detection_results['weapons']:
                body += "\n🔫 WEAPONS DETECTED:\n"
                for i, weapon in enumerate(detection_results['weapons'], 1):
                    body += f"   {i}. {weapon['class'].upper()} - Confidence: {weapon['confidence']:.2%}\n"
                body += f"   Total weapons: {len(detection_results['weapons'])}\n"
            
            if 'people' in detection_results:
                people_count = len(detection_results['people'])
                body += f"\n👥 PEOPLE COUNT: {people_count}\n"
                if people_count > 15:
                    body += "   ⚠️ CRITICAL OVERCROWDING!\n"
                elif people_count > 10:
                    body += "   ⚠️ High crowd density detected\n"
            
            if 'faces' in detection_results:
                suspicious_faces = [f for f in detection_results['faces'] 
                                  if f['emotion'] in ['angry', 'fear', 'disgust'] and f['confidence'] > 0.7]
                if suspicious_faces:
                    body += "\n😠 SUSPICIOUS BEHAVIOR:\n"
                    for i, face in enumerate(suspicious_faces, 1):
                        body += f"   {i}. {face['emotion'].title()} emotion - Confidence: {face['confidence']:.2%}\n"
            
            # Add action recommendations
            if threat_type == "WEAPON":
                body += """
🚨 IMMEDIATE ACTIONS REQUIRED:
✓ Contact security personnel immediately
✓ Verify the threat through live surveillance
✓ Consider evacuating the area if confirmed
✓ Contact law enforcement if necessary
✓ Document the incident for reports

⚡ THIS IS A CRITICAL SECURITY ALERT!
"""
            elif threat_type in ["OVERCROWDING", "CROWD_MEDIUM"]:
                body += """
👥 RECOMMENDED ACTIONS:
✓ Monitor crowd movement and behavior
✓ Consider crowd control measures
✓ Ensure emergency exits are clear
✓ Alert security staff to monitor area
✓ Implement crowd management if needed
"""
            elif threat_type == "SUSPICIOUS_BEHAVIOR":
                body += """
😠 RECOMMENDED ACTIONS:
✓ Monitor individuals with suspicious behavior
✓ Alert security personnel to observe area
✓ Be prepared for potential incidents
✓ Consider increasing security presence
✓ Document behavior patterns
"""
            
            body += f"""
📍 SYSTEM INFORMATION:
   Location: Smart Surveillance System
   Camera: {"IP Webcam" if "192.168" in self.ip_webcam_url else "Local Camera"}
   Evidence: Photo attached
   Alert ID: {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}

📧 This is an automated alert from Smart Surveillance System
🕒 Generated at: {timestamp}
"""
            
            # Attach text body
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach evidence image
            if frame_path and os.path.exists(frame_path):
                try:
                    with open(frame_path, 'rb') as f:
                        img_data = f.read()
                        image = MIMEImage(img_data)
                        image.add_header('Content-Disposition', 'attachment', 
                                       filename=f'{threat_type}_evidence_{timestamp.replace(":", "-")}.jpg')
                        msg.attach(image)
                except Exception as e:
                    self.log_message(f"Failed to attach evidence image: {e}")
            
            # Send email
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], self.email_config['sender_password'])
                server.send_message(msg)
            
            self.log_message(f"📧 {threat_type} email sent to {len(self.email_config['recipient_emails'])} recipients")
            return True
            
        except Exception as e:
            self.log_message(f"❌ {threat_type} email failed: {e}")
            return False
    
    def send_email_alert(self, alert_message, detection_results, frame_path):
        """Send email alert with threat information"""
        if not EMAIL_AVAILABLE or not self.email_config['enabled'] or not self.email_config['recipient_emails']:
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.image import MIMEImage
            
            # Create message
            msg = MIMEMultipart()
            msg['Subject'] = "🚨 SECURITY ALERT - Smart Surveillance System"
            msg['From'] = self.email_config['sender_email']
            msg['To'] = ', '.join(self.email_config['recipient_emails'])
            
            # Email body
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            body = f"""
🛡️ SMART SURVEILLANCE SYSTEM - SECURITY ALERT

⏰ TIME: {timestamp}
🚨 ALERT: {alert_message.strip()}

📊 DETECTION DETAILS:
"""
            
            # Add detection details
            if 'weapons' in detection_results and detection_results['weapons']:
                body += f"🔫 WEAPONS DETECTED: {len(detection_results['weapons'])}\n"
                for weapon in detection_results['weapons']:
                    body += f"   - {weapon['class']} (Confidence: {weapon['confidence']:.2f})\n"
            
            if 'people' in detection_results:
                people_count = len(detection_results['people'])
                body += f"👥 PEOPLE COUNT: {people_count}\n"
                if people_count > 15:
                    body += "   ⚠️ OVERCROWDING DETECTED!\n"
            
            if 'faces' in detection_results:
                suspicious_faces = [f for f in detection_results['faces'] 
                                  if f['emotion'] in ['angry', 'fear'] and f['confidence'] > 0.8]
                if suspicious_faces:
                    body += f"😠 SUSPICIOUS BEHAVIOR: {len(suspicious_faces)} suspicious faces\n"
                    for face in suspicious_faces:
                        body += f"   - {face['emotion'].title()} (Confidence: {face['confidence']:.2f})\n"
            
            body += f"""
📍 LOCATION: Smart Surveillance System
🖼️ EVIDENCE: See attached image

⚡ IMMEDIATE ACTION REQUIRED:
- Check the surveillance system immediately
- Verify the threat level
- Take appropriate security measures

---
Smart Surveillance System - Automated Security Alert
Generated at: {timestamp}
"""
            
            # Attach text
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach image if available
            if frame_path and os.path.exists(frame_path):
                try:
                    with open(frame_path, 'rb') as f:
                        img_data = f.read()
                        image = MIMEImage(img_data)
                        image.add_header('Content-Disposition', 'attachment', filename='threat_evidence.jpg')
                        msg.attach(image)
                except Exception as e:
                    self.log_message(f"Failed to attach image: {e}")
            
            # Send email
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], self.email_config['sender_password'])
                server.send_message(msg)
            
            self.log_message(f"📧 Email alert sent to {len(self.email_config['recipient_emails'])} recipients")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Email alert failed: {e}")
            return False
    
    def log_message(self, message):
        """Add message to alert log"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        def update_text():
            self.alert_text.insert(tk.END, full_message)
            self.alert_text.see(tk.END)
        
        self.root.after(0, update_text)
        print(message)  # Also print to console
    
    def on_closing(self):
        """Handle window closing"""
        if self.running:
            self.stop_monitoring()
        self.root.destroy()
    
    def run(self):
        """Start the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Show IP setup dialog
        self.show_ip_setup()
        
        # Start the GUI
        self.log_message("🛡️ Smart Surveillance System started!")
        self.log_message("📱 Make sure IP Webcam app is running on your mobile")
        self.root.mainloop()
    
    def show_ip_setup(self):
        """Show IP setup dialog"""
        current_ip = self.ip_entry.get()
        new_ip = simpledialog.askstring("IP Webcam Setup", 
                                       f"Enter your mobile IP address:\n(Current: {current_ip})\n\nOr press Cancel to use default",
                                       initialvalue="192.168.0.107")
        if new_ip:
            if not new_ip.startswith("http"):
                new_ip = f"http://{new_ip}:8080/video"
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, new_ip)
            self.ip_webcam_url = new_ip

def main():
    """Main function"""
    print("🛡️ Starting Smart Surveillance System")
    print("Make sure your mobile IP Webcam app is running!")
    
    app = MobileIPWebcamGUI()
    app.run()

if __name__ == "__main__":
    main()