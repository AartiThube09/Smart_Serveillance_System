#!/usr/bin/env python3
"""
🛡️ Mobile IP Webcam Surveillance System
Integrates all detection models with mobile camera input and alert generation
"""

import cv2
import os
import threading
import queue
import time
import datetime
import json
from pathlib import Path

# Import detection libraries
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    print("⚠️ YOLO not available - object and crowd detection disabled")
    YOLO_AVAILABLE = False

try:
    from fer import FER
    FER_AVAILABLE = True
except ImportError:
    print("⚠️ FER not available - facial expression detection disabled")
    FER_AVAILABLE = False

try:
    import importlib.util
    torch_spec = importlib.util.find_spec("torch")
    pytorchvideo_spec = importlib.util.find_spec("pytorchvideo")
    TORCH_AVAILABLE = torch_spec is not None and pytorchvideo_spec is not None
    if TORCH_AVAILABLE:
        print("✅ PyTorch/PyTorchVideo available for violence detection")
except ImportError:
    print("⚠️ PyTorch/PyTorchVideo not available - violence detection disabled")
    TORCH_AVAILABLE = False

try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

class MobileSurveillanceSystem:
    def __init__(self):
        print("🛡️ Smart Surveillance System - Initializing...")
        
        # Configuration
        self.config = {
            "ip_webcam_url": "http://192.0.0.4:8080/video",  # Default IP
            "backup_camera": 1,  # Fallback to laptop webcam
            "frame_skip": 2,  # Process every nth frame for performance
            "alert_cooldown": 10,  # Seconds between alerts
            "thresholds": {
                "weapon_confidence": 0.6,
                "crowd_size": 5,
                "violence_confidence": 0.7,
                "suspicious_emotion": 0.8
            }
        }
        
        # Initialize models
        self.models = {}
        self.load_models()
        
        # Video capture
        self.cap = None
        self.frame_queue = queue.Queue(maxsize=5)
        self.results_queue = queue.Queue()
        
        # Alert system
        self.alerts_folder = Path("alerts")
        self.alerts_folder.mkdir(exist_ok=True)
        self.last_alert_time = {}
        
        # Threading
        self.detection_thread = None
        self.running = False
        
        # Statistics
        self.stats = {
            "frames_processed": 0,
            "alerts_generated": 0,
            "detections": {
                "weapons": 0,
                "people": 0,
                "violence": 0,
                "suspicious_emotions": 0
            }
        }

    def load_models(self):
        """Load all available AI models"""
        print("Loading AI models...")
        
        # Object/Weapon Detection Model
        if YOLO_AVAILABLE:
            object_model_path = "Object_detection/best.pt"
            if os.path.exists(object_model_path):
                try:
                    self.models['object'] = YOLO(object_model_path)
                    print("✅ Weapon detection model loaded")
                except Exception as e:
                    print(f"❌ Error loading weapon model: {e}")
            
            # Crowd Detection Model
            crowd_model_path = "crowddetection/yolov8s.pt"
            if os.path.exists(crowd_model_path):
                try:
                    self.models['crowd'] = YOLO(crowd_model_path)
                    print("✅ Crowd detection model loaded")
                except Exception as e:
                    print(f"❌ Error loading crowd model: {e}")
        
        # Facial Expression Model
        if FER_AVAILABLE:
            try:
                self.models['expression'] = FER(mtcnn=True)
                print("✅ Facial expression model loaded")
            except Exception as e:
                print(f"❌ Error loading expression model: {e}")
        
        # Violence Detection Model (placeholder for now)
        if TORCH_AVAILABLE:
            try:
                # Load violence detection labels
                label_path = "violence/label_map.txt"
                if os.path.exists(label_path):
                    with open(label_path, 'r') as f:
                        self.violence_labels = [x.strip() for x in f.readlines()]
                    print("✅ Violence detection labels loaded")
                else:
                    print("⚠️ Violence labels not found")
            except Exception as e:
                print(f"❌ Error loading violence model: {e}")
        
        print(f"Models loaded: {list(self.models.keys())}")

    def setup_camera(self, ip_url=None):
        """Setup camera connection with IP webcam or fallback"""
        if ip_url:
            self.config["ip_webcam_url"] = ip_url
        
        print(f"Attempting to connect to IP webcam: {self.config['ip_webcam_url']}")
        
        # Try IP webcam first
        self.cap = cv2.VideoCapture(self.config["ip_webcam_url"])
        
        if not self.cap.isOpened():
            print("❌ IP webcam connection failed, trying laptop camera...")
            self.cap = cv2.VideoCapture(self.config["backup_camera"])
            
            if not self.cap.isOpened():
                print("❌ No camera available!")
                return False
            else:
                print("✅ Using laptop camera")
        else:
            print("✅ Connected to IP webcam")
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        return True

    def detect_weapons_objects(self, frame):
        """Detect weapons and objects using custom trained model"""
        if 'object' not in self.models:
            return {"weapons": [], "objects": [], "threat_level": "none"}
        
        try:
            results = self.models['object'].predict(frame, conf=self.config["thresholds"]["weapon_confidence"], verbose=False)
            
            weapons = []
            objects = []
            threat_level = "none"
            
            for result in results:
                if result.boxes is not None:
                    for box, cls, conf in zip(result.boxes.xyxy, result.boxes.cls, result.boxes.conf):
                        class_name = self.models['object'].names[int(cls)]
                        confidence = float(conf)
                        bbox = [int(x) for x in box]
                        
                        detection = {
                            "class": class_name,
                            "confidence": confidence,
                            "bbox": bbox
                        }
                        
                        # Classify as weapon or object
                        if any(weapon in class_name.lower() for weapon in ['weapon', 'gun', 'knife', 'pistol', 'rifle']):
                            weapons.append(detection)
                            threat_level = "high"
                            self.stats["detections"]["weapons"] += 1
                        else:
                            objects.append(detection)
            
            return {
                "weapons": weapons,
                "objects": objects,
                "threat_level": threat_level
            }
            
        except Exception as e:
            print(f"Weapon detection error: {e}")
            return {"weapons": [], "objects": [], "threat_level": "error"}

    def detect_crowd(self, frame):
        """Detect crowd density and people count"""
        if 'crowd' not in self.models:
            return {"people_count": 0, "crowd_level": "unknown", "threat_level": "none"}
        
        try:
            results = self.models['crowd'].predict(frame, conf=0.5, verbose=False)
            
            people_count = 0
            people_boxes = []
            
            for result in results:
                if result.boxes is not None:
                    for box, cls in zip(result.boxes.xyxy, result.boxes.cls):
                        if int(cls) == 0:  # Person class
                            people_count += 1
                            people_boxes.append([int(x) for x in box])
            
            # Determine crowd level
            if people_count >= 15:
                crowd_level = "critical"
                threat_level = "high"
            elif people_count >= 10:
                crowd_level = "high"
                threat_level = "medium"
            elif people_count >= self.config["thresholds"]["crowd_size"]:
                crowd_level = "medium"
                threat_level = "low"
            else:
                crowd_level = "low"
                threat_level = "none"
            
            self.stats["detections"]["people"] = people_count
            
            return {
                "people_count": people_count,
                "people_boxes": people_boxes,
                "crowd_level": crowd_level,
                "threat_level": threat_level
            }
            
        except Exception as e:
            print(f"Crowd detection error: {e}")
            return {"people_count": 0, "crowd_level": "error", "threat_level": "error"}

    def detect_expressions(self, frame):
        """Detect facial expressions and suspicious behavior"""
        if 'expression' not in self.models:
            return {"faces": [], "suspicious": False, "threat_level": "none"}
        
        try:
            results = self.models['expression'].detect_emotions(frame)
            
            faces = []
            suspicious = False
            threat_level = "none"
            
            if results:
                for result in results:
                    emotions = result['emotions']
                    bbox = result['box']
                    dominant_emotion = max(emotions, key=emotions.get)
                    confidence = emotions[dominant_emotion]
                    
                    face_data = {
                        "emotion": dominant_emotion,
                        "confidence": confidence,
                        "bbox": bbox,
                        "all_emotions": emotions
                    }
                    faces.append(face_data)
                    
                    # Check for suspicious emotions
                    if dominant_emotion in ['angry', 'fear', 'disgust'] and confidence > self.config["thresholds"]["suspicious_emotion"]:
                        suspicious = True
                        threat_level = "medium"
                        self.stats["detections"]["suspicious_emotions"] += 1
            
            return {
                "faces": faces,
                "suspicious": suspicious,
                "threat_level": threat_level
            }
            
        except Exception as e:
            print(f"Expression detection error: {e}")
            return {"faces": [], "suspicious": False, "threat_level": "error"}

    def detect_violence(self, frame):
        """Placeholder for violence detection - can be enhanced with actual model"""
        # This is a simplified implementation
        # You can integrate your actual violence detection model here
        return {
            "violence_detected": False,
            "confidence": 0.0,
            "threat_level": "none"
        }

    def generate_alert(self, detection_results, frame):
        """Generate alert messages and save to files"""
        timestamp = datetime.datetime.now()
        alert_data = {
            "timestamp": timestamp.isoformat(),
            "detection_results": detection_results,
            "alert_level": "none"
        }
        
        # Determine overall threat level
        threat_levels = []
        for category, results in detection_results.items():
            if isinstance(results, dict) and 'threat_level' in results:
                threat_levels.append(results['threat_level'])
        
        # Calculate overall threat
        if "high" in threat_levels:
            alert_data["alert_level"] = "HIGH"
        elif "medium" in threat_levels:
            alert_data["alert_level"] = "MEDIUM"
        elif "low" in threat_levels:
            alert_data["alert_level"] = "LOW"
        
        # Generate alert only if there's a threat
        if alert_data["alert_level"] != "none":
            # Check cooldown
            current_time = time.time()
            alert_type = alert_data["alert_level"]
            
            if alert_type not in self.last_alert_time or \
               current_time - self.last_alert_time[alert_type] > self.config["alert_cooldown"]:
                
                # Save alert data
                alert_filename = f"alert_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
                alert_path = self.alerts_folder / alert_filename
                
                with open(alert_path, 'w') as f:
                    json.dump(alert_data, f, indent=2)
                
                # Save frame
                frame_filename = f"frame_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
                frame_path = self.alerts_folder / frame_filename
                cv2.imwrite(str(frame_path), frame)
                
                # Generate alert message
                self.create_alert_message(alert_data, detection_results)
                
                # Update cooldown
                self.last_alert_time[alert_type] = current_time
                self.stats["alerts_generated"] += 1
                
                # Sound alert
                if SOUND_AVAILABLE:
                    winsound.Beep(1200, 500)
                
                return True
        
        return False

    def create_alert_message(self, alert_data, detection_results):
        """Create detailed alert message"""
        timestamp = alert_data["timestamp"]
        alert_level = alert_data["alert_level"]
        
        message = f"""
🚨 SECURITY ALERT - {alert_level} THREAT DETECTED 🚨
=================================================
Time: {timestamp}
Alert Level: {alert_level}

DETECTION SUMMARY:
"""
        
        # Weapons
        if 'weapons' in detection_results and detection_results['weapons']['weapons']:
            message += f"\n⚠️ WEAPONS DETECTED: {len(detection_results['weapons']['weapons'])}"
            for weapon in detection_results['weapons']['weapons']:
                message += f"\n  - {weapon['class']} (Confidence: {weapon['confidence']:.2f})"
        
        # Crowd
        if 'crowd' in detection_results:
            crowd_data = detection_results['crowd']
            message += f"\n👥 PEOPLE COUNT: {crowd_data.get('people_count', 0)}"
            message += f"\n📊 CROWD LEVEL: {crowd_data.get('crowd_level', 'unknown').upper()}"
        
        # Expressions
        if 'expressions' in detection_results and detection_results['expressions']['suspicious']:
            message += "\n😠 SUSPICIOUS BEHAVIOR DETECTED"
            for face in detection_results['expressions']['faces']:
                if face['emotion'] in ['angry', 'fear', 'disgust']:
                    message += f"\n  - {face['emotion'].title()} expression (Confidence: {face['confidence']:.2f})"
        
        # Violence
        if 'violence' in detection_results and detection_results['violence']['violence_detected']:
            message += f"\n🥊 VIOLENCE DETECTED (Confidence: {detection_results['violence']['confidence']:.2f})"
        
        message += f"\n\nAlert saved to: {self.alerts_folder}"
        message += f"\nTotal alerts today: {self.stats['alerts_generated']}"
        message += "\n=================================================\n"
        
        print(message)
        
        # Save message to file
        message_file = self.alerts_folder / f"alert_message_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(message_file, 'w') as f:
            f.write(message)

    def detection_worker(self):
        """Background thread for running detections"""
        frame_count = 0
        
        while self.running:
            try:
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get(timeout=1)
                    frame_count += 1
                    
                    # Skip frames for performance
                    if frame_count % self.config["frame_skip"] != 0:
                        continue
                    
                    # Run all detections
                    detection_results = {}
                    
                    detection_results['weapons'] = self.detect_weapons_objects(frame)
                    detection_results['crowd'] = self.detect_crowd(frame)
                    detection_results['expressions'] = self.detect_expressions(frame)
                    detection_results['violence'] = self.detect_violence(frame)
                    
                    # Generate alerts if needed
                    alert_generated = self.generate_alert(detection_results, frame)
                    
                    # Put results in queue for display
                    self.results_queue.put({
                        'results': detection_results,
                        'alert': alert_generated,
                        'frame_count': frame_count
                    })
                    
                    self.stats["frames_processed"] += 1
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Detection worker error: {e}")
                time.sleep(0.1)

    def draw_detections(self, frame, detection_results):
        """Draw detection results on frame"""
        # Draw weapons
        if 'weapons' in detection_results:
            for weapon in detection_results['weapons']['weapons']:
                bbox = weapon['bbox']
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 3)
                cv2.putText(frame, f"WEAPON: {weapon['class']}", 
                           (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Draw people
        if 'crowd' in detection_results:
            for bbox in detection_results['crowd'].get('people_boxes', []):
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
        
        # Draw faces with emotions
        if 'expressions' in detection_results:
            for face in detection_results['expressions']['faces']:
                bbox = face['bbox']
                emotion = face['emotion']
                confidence = face['confidence']
                color = (0, 0, 255) if emotion in ['angry', 'fear', 'disgust'] else (0, 255, 0)
                
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
                cv2.putText(frame, f"{emotion}: {confidence:.2f}", 
                           (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return frame

    def draw_status_overlay(self, frame, detection_results):
        """Draw status information overlay"""
        height, width = frame.shape[:2]
        
        # Background for status
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (width-10, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Title
        cv2.putText(frame, "Mobile Surveillance System", (20, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        # Status info
        y = 60
        line_height = 20
        
        # Connection status
        connection_text = "IP Webcam Connected" if "192.168" in str(self.cap.getBackendName()) else "Laptop Camera"
        cv2.putText(frame, f"Camera: {connection_text}", (20, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        y += line_height
        
        # Detection counts
        if 'weapons' in detection_results:
            weapon_count = len(detection_results['weapons']['weapons'])
            color = (0, 0, 255) if weapon_count > 0 else (0, 255, 0)
            cv2.putText(frame, f"Weapons: {weapon_count}", (20, y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        if 'crowd' in detection_results:
            people_count = detection_results['crowd']['people_count']
            crowd_level = detection_results['crowd']['crowd_level']
            color = (0, 0, 255) if crowd_level in ['high', 'critical'] else (0, 255, 0)
            cv2.putText(frame, f"People: {people_count} ({crowd_level})", (150, y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        y += line_height
        
        if 'expressions' in detection_results:
            face_count = len(detection_results['expressions']['faces'])
            suspicious = detection_results['expressions']['suspicious']
            color = (0, 0, 255) if suspicious else (0, 255, 0)
            status = "SUSPICIOUS" if suspicious else "Normal"
            cv2.putText(frame, f"Faces: {face_count} ({status})", (20, y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Stats
        cv2.putText(frame, f"Frames: {self.stats['frames_processed']} | Alerts: {self.stats['alerts_generated']}", 
                   (150, y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return frame

    def run(self, ip_url=None):
        """Main execution loop"""
        if not self.setup_camera(ip_url):
            return
        
        print("🚀 Starting Mobile Surveillance System...")
        print("📱 Make sure your IP Webcam app is running on your mobile")
        print("Press 'q' to quit, 'r' to reconnect camera, 's' to save frame")
        print("=" * 60)
        
        self.running = True
        self.detection_thread = threading.Thread(target=self.detection_worker, daemon=True)
        self.detection_thread.start()
        
        # Display window
        window_name = "Mobile Surveillance System"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1024, 768)
        
        current_results = {}
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("⚠️ Failed to read frame, attempting reconnection...")
                    self.setup_camera()
                    continue
                
                # Add frame to processing queue
                if not self.frame_queue.full():
                    self.frame_queue.put(frame.copy())
                
                # Get latest detection results
                try:
                    while not self.results_queue.empty():
                        result_data = self.results_queue.get_nowait()
                        current_results = result_data['results']
                        if result_data['alert']:
                            print(f"🚨 ALERT GENERATED at frame {result_data['frame_count']}")
                except queue.Empty:
                    pass
                
                # Draw detections and status
                if current_results:
                    frame = self.draw_detections(frame, current_results)
                
                frame = self.draw_status_overlay(frame, current_results)
                
                # Display
                cv2.imshow(window_name, frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    print("🔄 Reconnecting camera...")
                    self.setup_camera()
                elif key == ord('s'):
                    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_path = f"saved_frame_{timestamp}.jpg"
                    cv2.imwrite(save_path, frame)
                    print(f"💾 Frame saved: {save_path}")
                elif key == ord('c'):
                    # Change IP camera URL
                    print("Enter new IP webcam URL (or press Enter to skip):")
                    # In a real implementation, you'd use a GUI input dialog
                    
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
        
        finally:
            print("🧹 Cleaning up...")
            self.running = False
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()
            print("✅ Cleanup complete")

def main():
    """Main function with user input for IP configuration"""
    print("🛡️ Mobile Surveillance System")
    print("=" * 40)
    
    # Get IP webcam URL from user
    default_ip = "192.168.0.107"
    print(f"Default IP Webcam URL: http://{default_ip}:8080/video")
    
    user_input = input("Enter your mobile IP (or press Enter for default): ").strip()
    
    if user_input:
        if not user_input.startswith("http"):
            ip_url = f"http://{user_input}:8080/video"
        else:
            ip_url = user_input
    else:
        ip_url = None  # Use default from config
    
    # Initialize and run system
    surveillance = MobileSurveillanceSystem()
    surveillance.run(ip_url)

if __name__ == "__main__":
    main()