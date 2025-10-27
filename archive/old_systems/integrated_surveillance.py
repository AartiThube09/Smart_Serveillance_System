"""
Enhanced Integration Script with GUI and Email Alerts
Smart Surveillance System - Unified Detection
"""

import cv2
import threading
import queue
import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from surveillance_gui import SmartSurveillanceGUI
    GUI_AVAILABLE = True
except ImportError as e:
    print(f"GUI not available: {e}")
    GUI_AVAILABLE = False

# Import detection modules
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    print("YOLO not available - object and crowd detection disabled")
    YOLO_AVAILABLE = False

try:
    from fer import FER
    FER_AVAILABLE = True
except ImportError:
    print("FER not available - facial expression detection disabled")
    FER_AVAILABLE = False

class ConsoleIntegration:
    """Fallback console-based integration when GUI is not available"""
    
    def __init__(self):
        self.cap = None
        self.frame_queue = queue.Queue()
        self.results = {
            "object": "Initializing...",
            "violence": "Initializing...",
            "crowd": "Initializing...",
            "expression": "Initializing..."
        }
        
        # Load models
        self.load_models()
        
    def load_models(self):
        """Load detection models"""
        try:
            if YOLO_AVAILABLE:
                self.object_model = YOLO("Object_detection/best.pt")
                self.crowd_model = YOLO("crowddetection/yolov8s.pt")
                print("✅ YOLO models loaded")
            else:
                self.object_model = None
                self.crowd_model = None
        except Exception as e:
            print(f"❌ Failed to load YOLO models: {e}")
            self.object_model = None
            self.crowd_model = None
        
        try:
            if FER_AVAILABLE:
                self.expression_detector = FER(mtcnn=True)
                print("✅ Expression model loaded")
            else:
                self.expression_detector = None
        except Exception as e:
            print(f"❌ Failed to load expression model: {e}")
            self.expression_detector = None
    
    def detect_objects(self, frame):
        """Object detection"""
        if self.object_model is None:
            return "Model not loaded"
        
        try:
            results = self.object_model.predict(frame, conf=0.5, verbose=False)
            detections = []
            
            for result in results:
                if result.boxes is not None:
                    for cls in result.boxes.cls:
                        class_name = self.object_model.names[int(cls)]
                        detections.append(class_name)
            
            return f"Objects: {', '.join(detections) if detections else 'None'}"
        except Exception as e:
            return f"Error: {e}"
    
    def detect_violence(self, frame):
        """Violence detection (placeholder)"""
        return "Violence: No"
    
    def detect_crowd(self, frame):
        """Crowd detection"""
        if self.crowd_model is None:
            return "Model not loaded"
        
        try:
            results = self.crowd_model.predict(frame, conf=0.5, verbose=False)
            person_count = 0
            
            for result in results:
                if result.boxes is not None:
                    for cls in result.boxes.cls:
                        if int(cls) == 0:  # Person class
                            person_count += 1
            
            if person_count > 10:
                level = "High"
            elif person_count > 5:
                level = "Medium"
            else:
                level = "Low"
            
            return f"People: {person_count}, Level: {level}"
        except Exception as e:
            return f"Error: {e}"
    
    def detect_expression(self, frame):
        """Facial expression detection"""
        if self.expression_detector is None:
            return "Model not loaded"
        
        try:
            results = self.expression_detector.detect_emotions(frame)
            if results:
                emotions = []
                for result in results:
                    emotion_scores = result['emotions']
                    dominant_emotion = max(emotion_scores, key=emotion_scores.get)
                    emotions.append(dominant_emotion)
                
                return f"Expressions: {', '.join(emotions)}"
            else:
                return "No faces detected"
        except Exception as e:
            return f"Error: {e}"
    
    def worker(self):
        """Worker thread for processing frames"""
        while True:
            try:
                frame = self.frame_queue.get(timeout=1)
                if frame is None:
                    break
                
                # Run all detections
                self.results["object"] = self.detect_objects(frame)
                self.results["violence"] = self.detect_violence(frame)
                self.results["crowd"] = self.detect_crowd(frame)
                self.results["expression"] = self.detect_expression(frame)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Processing error: {e}")
    
    def run(self):
        """Run console-based surveillance"""
        print("Starting Smart Surveillance System (Console Mode)")
        print("Press 'q' to quit")
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("❌ Cannot open camera")
            return
        
        # Start worker thread
        worker_thread = threading.Thread(target=self.worker, daemon=True)
        worker_thread.start()
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                # Resize frame
                frame = cv2.resize(frame, (640, 480))
                
                # Send frame to processing queue
                if not self.frame_queue.full():
                    try:
                        self.frame_queue.put(frame, timeout=0.1)
                    except queue.Full:
                        pass
                
                # Overlay results on frame
                y = 30
                for key, val in self.results.items():
                    text = f"{key}: {val}" if val else f"{key}: ..."
                    cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 
                               0.6, (0, 255, 0), 2)
                    y += 25
                
                # Display frame
                cv2.imshow("Smart Surveillance - Console Mode", frame)
                
                # Check for quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        except KeyboardInterrupt:
            print("\nShutting down...")
        
        finally:
            # Cleanup
            self.frame_queue.put(None)
            self.cap.release()
            cv2.destroyAllWindows()

def main():
    """Main function to choose between GUI and console mode"""
    print("🛡️ Smart Surveillance System")
    print("=" * 50)
    
    if GUI_AVAILABLE:
        print("Starting GUI mode...")
        try:
            root = tk.Tk()
            app = SmartSurveillanceGUI(root)
            root.mainloop()
        except Exception as e:
            print(f"GUI failed: {e}")
            print("Falling back to console mode...")
            console_app = ConsoleIntegration()
            console_app.run()
    else:
        print("GUI not available, starting console mode...")
        console_app = ConsoleIntegration()
        console_app.run()

if __name__ == "__main__":
    main()