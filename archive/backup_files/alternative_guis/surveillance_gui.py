import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import cv2
import threading
import queue
import numpy as np
from PIL import Image, ImageTk
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from datetime import datetime
import json
import os

# Import your detection modules
try:
    from ultralytics import YOLO
    from fer import FER
    import torch
    import pytorchvideo.models.hub as hub
    import torchvision.transforms as transforms
except ImportError as e:
    print(f"Warning: Some modules not installed: {e}")

class SmartSurveillanceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Surveillance System")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e1e')
        
        # Initialize variables
        self.cap = None
        self.is_running = False
        self.frame_queue = queue.Queue()
        self.current_frame = None
        
        # Detection results
        self.results = {
            "object": "Initializing...",
            "violence": "Initializing...",
            "crowd": "Initializing...",
            "expression": "Initializing..."
        }
        
        # Threat flags
        self.threat_detected = {
            "weapon": False,
            "violence": False,
            "overcrowd": False,
            "suspicious_expression": False
        }
        
        # Email configuration
        self.email_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "",
            "sender_password": "",
            "recipient_email": ""
        }
        
        # Load models
        self.load_models()
        
        # Create GUI
        self.create_widgets()
        
        # Start video processing thread
        self.processing_thread = threading.Thread(target=self.process_frames, daemon=True)
        self.processing_thread.start()
        
        # Start GUI update
        self.update_gui()
    
    def load_models(self):
        """Load all AI models"""
        try:
            # Object detection model
            self.object_model = YOLO("Object_detection/best.pt")
            print("✅ Object detection model loaded")
        except Exception as e:
            print(f"❌ Failed to load object model: {e}")
            self.object_model = None
        
        try:
            # Crowd detection model
            self.crowd_model = YOLO("crowddetection/yolov8s.pt")
            print("✅ Crowd detection model loaded")
        except Exception as e:
            print(f"❌ Failed to load crowd model: {e}")
            self.crowd_model = None
        
        try:
            # Facial expression detector
            self.expression_detector = FER(mtcnn=True)
            print("✅ Expression detection model loaded")
        except Exception as e:
            print(f"❌ Failed to load expression model: {e}")
            self.expression_detector = None
        
        # Violence detection model (placeholder - implement based on your model)
        self.violence_model = None
        print("⚠️ Violence detection model not implemented yet")
    
    def create_widgets(self):
        """Create the main GUI layout"""
        # Main title
        title_frame = tk.Frame(self.root, bg='#1e1e1e')
        title_frame.pack(fill='x', padx=10, pady=5)
        
        title_label = tk.Label(title_frame, text="🛡️ Smart Surveillance System", 
                              font=('Arial', 24, 'bold'), fg='#00ff88', bg='#1e1e1e')
        title_label.pack()
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - Video feed
        self.create_video_panel(main_frame)
        
        # Right panel - Controls and results
        self.create_control_panel(main_frame)
        
        # Bottom panel - Logs
        self.create_log_panel(main_frame)
    
    def create_video_panel(self, parent):
        """Create video display panel"""
        video_frame = tk.LabelFrame(parent, text="Live Video Feed", font=('Arial', 12, 'bold'),
                                   fg='#00ff88', bg='#2d2d2d', bd=2)
        video_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Video display
        self.video_label = tk.Label(video_frame, bg='black', text="Camera Feed Will Appear Here",
                                   fg='white', font=('Arial', 16))
        self.video_label.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Video controls
        controls_frame = tk.Frame(video_frame, bg='#2d2d2d')
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        self.start_btn = tk.Button(controls_frame, text="▶️ Start Camera", 
                                  command=self.start_camera, bg='#00ff88', fg='black',
                                  font=('Arial', 10, 'bold'), relief='raised')
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = tk.Button(controls_frame, text="⏹️ Stop Camera", 
                                 command=self.stop_camera, bg='#ff4444', fg='white',
                                 font=('Arial', 10, 'bold'), relief='raised', state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        # Camera source entry
        tk.Label(controls_frame, text="Camera:", fg='white', bg='#2d2d2d').pack(side='left', padx=(20, 5))
        self.camera_var = tk.StringVar(value="0")
        camera_entry = tk.Entry(controls_frame, textvariable=self.camera_var, width=30)
        camera_entry.pack(side='left', padx=5)
    
    def create_control_panel(self, parent):
        """Create control and results panel"""
        right_frame = tk.Frame(parent, bg='#1e1e1e')
        right_frame.pack(side='right', fill='y', padx=(10, 0))
        
        # Detection Results
        results_frame = tk.LabelFrame(right_frame, text="Detection Results", 
                                     font=('Arial', 12, 'bold'), fg='#00ff88', 
                                     bg='#2d2d2d', bd=2, width=350)
        results_frame.pack(fill='x', pady=(0, 10))
        results_frame.pack_propagate(False)
        
        # Create result displays
        self.result_labels = {}
        colors = {'object': '#ff6b35', 'violence': '#ff1744', 'crowd': '#ffa726', 'expression': '#42a5f5'}
        
        for i, (key, color) in enumerate(colors.items()):
            frame = tk.Frame(results_frame, bg='#2d2d2d')
            frame.pack(fill='x', padx=10, pady=5)
            
            icon_label = tk.Label(frame, text=self.get_icon(key), font=('Arial', 16), 
                                 fg=color, bg='#2d2d2d')
            icon_label.pack(side='left', padx=(0, 10))
            
            text_label = tk.Label(frame, text=f"{key.title()}: Initializing...", 
                                 font=('Arial', 10), fg='white', bg='#2d2d2d', anchor='w')
            text_label.pack(side='left', fill='x', expand=True)
            
            self.result_labels[key] = text_label
        
        # Threat Status
        threat_frame = tk.LabelFrame(right_frame, text="Threat Status", 
                                    font=('Arial', 12, 'bold'), fg='#ff1744', 
                                    bg='#2d2d2d', bd=2)
        threat_frame.pack(fill='x', pady=(0, 10))
        
        self.threat_label = tk.Label(threat_frame, text="🟢 All Clear", 
                                    font=('Arial', 14, 'bold'), fg='#00ff88', bg='#2d2d2d')
        self.threat_label.pack(pady=10)
        
        # Email Configuration
        email_frame = tk.LabelFrame(right_frame, text="Email Alerts", 
                                   font=('Arial', 12, 'bold'), fg='#00ff88', 
                                   bg='#2d2d2d', bd=2)
        email_frame.pack(fill='x', pady=(0, 10))
        
        # Email entries
        tk.Label(email_frame, text="Your Email:", fg='white', bg='#2d2d2d').pack(anchor='w', padx=10)
        self.sender_email_var = tk.StringVar()
        tk.Entry(email_frame, textvariable=self.sender_email_var, width=35).pack(padx=10, pady=2)
        
        tk.Label(email_frame, text="App Password:", fg='white', bg='#2d2d2d').pack(anchor='w', padx=10)
        self.sender_password_var = tk.StringVar()
        tk.Entry(email_frame, textvariable=self.sender_password_var, show='*', width=35).pack(padx=10, pady=2)
        
        tk.Label(email_frame, text="Alert Email:", fg='white', bg='#2d2d2d').pack(anchor='w', padx=10)
        self.recipient_email_var = tk.StringVar()
        tk.Entry(email_frame, textvariable=self.recipient_email_var, width=35).pack(padx=10, pady=2)
        
        test_email_btn = tk.Button(email_frame, text="Test Email", command=self.test_email,
                                  bg='#2196f3', fg='white', font=('Arial', 9))
        test_email_btn.pack(pady=5)
        
        # Statistics
        stats_frame = tk.LabelFrame(right_frame, text="Statistics", 
                                   font=('Arial', 12, 'bold'), fg='#00ff88', 
                                   bg='#2d2d2d', bd=2)
        stats_frame.pack(fill='both', expand=True)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=8, bg='#1e1e1e', 
                                                   fg='white', font=('Courier', 9))
        self.stats_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    def create_log_panel(self, parent):
        """Create log panel"""
        log_frame = tk.LabelFrame(self.root, text="System Logs", 
                                 font=('Arial', 12, 'bold'), fg='#00ff88', 
                                 bg='#2d2d2d', bd=2, height=150)
        log_frame.pack(fill='x', padx=10, pady=(10, 10))
        log_frame.pack_propagate(False)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, bg='#1e1e1e', 
                                                 fg='#00ff88', font=('Courier', 9))
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.log_message("System initialized successfully")
    
    def get_icon(self, detection_type):
        """Get icon for detection type"""
        icons = {
            'object': '🔍',
            'violence': '⚠️',
            'crowd': '👥',
            'expression': '😊'
        }
        return icons.get(detection_type, '❓')
    
    def start_camera(self):
        """Start camera capture"""
        camera_source = self.camera_var.get()
        
        # Try to convert to int (for webcam index) or use as string (for IP camera)
        try:
            camera_source = int(camera_source)
        except ValueError:
            pass  # Keep as string for IP cameras
        
        self.cap = cv2.VideoCapture(camera_source)
        
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot open camera source!")
            return
        
        self.is_running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.log_message(f"Camera started: {camera_source}")
        
        # Start capture thread
        self.capture_thread = threading.Thread(target=self.capture_frames, daemon=True)
        self.capture_thread.start()
    
    def stop_camera(self):
        """Stop camera capture"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.video_label.config(image='', text="Camera Stopped")
        self.log_message("Camera stopped")
    
    def capture_frames(self):
        """Capture frames from camera"""
        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                # Resize frame for processing
                frame = cv2.resize(frame, (640, 480))
                self.current_frame = frame.copy()
                
                # Add frame to processing queue
                if not self.frame_queue.full():
                    try:
                        self.frame_queue.put(frame, timeout=0.1)
                    except queue.Full:
                        pass
            else:
                break
    
    def process_frames(self):
        """Process frames for detection"""
        while True:
            try:
                frame = self.frame_queue.get(timeout=1)
                
                # Run detections
                self.detect_objects(frame)
                self.detect_violence(frame)
                self.detect_crowd(frame)
                self.detect_expression(frame)
                
                # Check for threats
                self.check_threats()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.log_message(f"Processing error: {e}")
    
    def detect_objects(self, frame):
        """Object/Weapon detection"""
        if self.object_model is None:
            self.results["object"] = "Model not loaded"
            return
        
        try:
            results = self.object_model.predict(frame, conf=0.5, verbose=False)
            
            detections = []
            weapon_detected = False
            
            for result in results:
                if result.boxes is not None:
                    for box, cls, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                        class_name = self.object_model.names[int(cls)]
                        confidence = float(conf)
                        
                        detections.append(f"{class_name}: {confidence:.2f}")
                        
                        # Check for weapons (adjust class names based on your model)
                        if class_name.lower() in ['weapon', 'gun', 'knife', 'pistol']:
                            weapon_detected = True
            
            self.threat_detected["weapon"] = weapon_detected
            self.results["object"] = f"Objects: {len(detections)}" + (", WEAPON DETECTED!" if weapon_detected else "")
            
        except Exception as e:
            self.results["object"] = f"Error: {e}"
    
    def detect_violence(self, frame):
        """Violence detection (placeholder - implement based on your model)"""
        # This is a placeholder implementation
        # Replace with your actual violence detection code
        self.results["violence"] = "No violence detected"
        self.threat_detected["violence"] = False
    
    def detect_crowd(self, frame):
        """Crowd detection"""
        if self.crowd_model is None:
            self.results["crowd"] = "Model not loaded"
            return
        
        try:
            results = self.crowd_model.predict(frame, conf=0.5, verbose=False)
            
            person_count = 0
            for result in results:
                if result.boxes is not None:
                    for cls in result.boxes.cls:
                        if int(cls) == 0:  # Person class
                            person_count += 1
            
            # Determine crowd level
            if person_count > 20:
                crowd_level = "OVERCROWDED"
                self.threat_detected["overcrowd"] = True
            elif person_count > 10:
                crowd_level = "High"
                self.threat_detected["overcrowd"] = False
            elif person_count > 5:
                crowd_level = "Medium"
                self.threat_detected["overcrowd"] = False
            else:
                crowd_level = "Low"
                self.threat_detected["overcrowd"] = False
            
            self.results["crowd"] = f"People: {person_count}, Level: {crowd_level}"
            
        except Exception as e:
            self.results["crowd"] = f"Error: {e}"
    
    def detect_expression(self, frame):
        """Facial expression detection"""
        if self.expression_detector is None:
            self.results["expression"] = "Model not loaded"
            return
        
        try:
            results = self.expression_detector.detect_emotions(frame)
            
            if results:
                emotions = []
                suspicious = False
                
                for result in results:
                    emotion_scores = result['emotions']
                    dominant_emotion = max(emotion_scores, key=emotion_scores.get)
                    emotions.append(dominant_emotion)
                    
                    # Check for suspicious emotions
                    if dominant_emotion in ['angry', 'fear'] and emotion_scores[dominant_emotion] > 0.7:
                        suspicious = True
                
                self.threat_detected["suspicious_expression"] = suspicious
                emotion_text = ", ".join(emotions) if emotions else "None detected"
                self.results["expression"] = f"Emotions: {emotion_text}" + (" - SUSPICIOUS!" if suspicious else "")
            else:
                self.results["expression"] = "No faces detected"
                self.threat_detected["suspicious_expression"] = False
                
        except Exception as e:
            self.results["expression"] = f"Error: {e}"
    
    def check_threats(self):
        """Check for threats and send alerts"""
        threat_detected = any(self.threat_detected.values())
        
        if threat_detected:
            self.send_email_alert()
    
    def send_email_alert(self):
        """Send email alert for threats"""
        sender_email = self.sender_email_var.get()
        sender_password = self.sender_password_var.get()
        recipient_email = self.recipient_email_var.get()
        
        if not all([sender_email, sender_password, recipient_email]):
            return
        
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = "🚨 SECURITY ALERT - Smart Surveillance System"
            
            # Create email body
            threats = [key for key, value in self.threat_detected.items() if value]
            body = f"""
            SECURITY ALERT DETECTED!
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Threats Detected:
            {chr(10).join([f"- {threat.replace('_', ' ').title()}" for threat in threats])}
            
            Current Status:
            - Object Detection: {self.results['object']}
            - Violence Detection: {self.results['violence']}
            - Crowd Detection: {self.results['crowd']}
            - Expression Detection: {self.results['expression']}
            
            Please check the surveillance system immediately.
            
            This is an automated message from Smart Surveillance System.
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"])
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()
            
            self.log_message("🚨 ALERT EMAIL SENT!")
            
        except Exception as e:
            self.log_message(f"Failed to send email: {e}")
    
    def test_email(self):
        """Test email configuration"""
        sender_email = self.sender_email_var.get()
        sender_password = self.sender_password_var.get()
        recipient_email = self.recipient_email_var.get()
        
        if not all([sender_email, sender_password, recipient_email]):
            messagebox.showwarning("Warning", "Please fill in all email fields!")
            return
        
        try:
            msg = MimeMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = "Test Email - Smart Surveillance System"
            
            body = f"""
            This is a test email from Smart Surveillance System.
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            If you received this email, the configuration is working correctly!
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"])
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()
            
            messagebox.showinfo("Success", "Test email sent successfully!")
            self.log_message("✅ Test email sent successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send test email: {e}")
            self.log_message(f"❌ Test email failed: {e}")
    
    def update_gui(self):
        """Update GUI elements"""
        # Update video display
        if self.current_frame is not None:
            frame = self.current_frame.copy()
            
            # Add detection results overlay
            y = 30
            for key, result in self.results.items():
                color = (0, 0, 255) if any(self.threat_detected.values()) else (0, 255, 0)
                cv2.putText(frame, f"{key.title()}: {result}", (10, y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                y += 25
            
            # Convert to PIL and display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((640, 480), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.config(image=imgtk, text="")
            self.video_label.image = imgtk
        
        # Update result labels
        for key, label in self.result_labels.items():
            label.config(text=f"{key.title()}: {self.results[key]}")
        
        # Update threat status
        if any(self.threat_detected.values()):
            self.threat_label.config(text="🔴 THREAT DETECTED!", fg='#ff1744')
        else:
            self.threat_label.config(text="🟢 All Clear", fg='#00ff88')
        
        # Update statistics
        stats = f"""Detection Statistics:
        
Objects Detected: {self.results['object']}
Violence Status: {self.results['violence']}
Crowd Level: {self.results['crowd']}
Expressions: {self.results['expression']}

Threat Status:
- Weapon: {'YES' if self.threat_detected['weapon'] else 'NO'}
- Violence: {'YES' if self.threat_detected['violence'] else 'NO'}
- Overcrowd: {'YES' if self.threat_detected['overcrowd'] else 'NO'}
- Suspicious: {'YES' if self.threat_detected['suspicious_expression'] else 'NO'}
        """
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, stats)
        
        # Schedule next update
        self.root.after(100, self.update_gui)
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)

def main():
    root = tk.Tk()
    app = SmartSurveillanceGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application terminated by user")
    finally:
        if app.cap:
            app.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()