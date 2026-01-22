"""
Violence Detection Adapter for integrated surveillance system.

Provides a clean interface to run violence detection in a separate thread
and post results to a queue for the main GUI to consume.
"""

import os
import threading
import time
from collections import deque
from typing import Callable, Optional

import cv2
import torch
import pytorchvideo.models.hub as hub
import torchvision.transforms as transforms


class ViolenceDetector:
    """Threaded violence detection using SlowFast model."""
    
    def __init__(self, model_path: Optional[str] = None, device: str = "auto"):
        self.device = torch.device(
            "cuda" if (device == "auto" and torch.cuda.is_available()) else 
            ("cuda" if device == "cuda" else "cpu")
        )
        
        # Load label map
        label_path = os.path.join(os.path.dirname(__file__), "label_map.txt")
        with open(label_path, "r", encoding="utf-8") as f:
            self.labels = [x.strip() for x in f if x.strip()]
        
        # Load model
        self.model = hub.slowfast_r50(pretrained=True)
        self.model = self.model.to(self.device).eval()
        
        # Transform
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((256, 256)),
            transforms.Normalize((0.45, 0.45, 0.45), (0.225, 0.225, 0.225)),
        ])
        
        # Config
        self.alpha = 4
        self.buffer_size = 32
        self.violence_threshold = 0.65
        self.smoothing_window = 3
        self.confidence_floor = 0.20
        
        self.violence_keywords = [
            "punch", "punching", "fight", "fighting", 
            "kicking", "wrestling", "boxing", "slapping",
            "hitting", "violence", "assault"
        ]
        
        # State
        self.frame_buffer = deque(maxlen=self.buffer_size)
        self.violence_history = deque(maxlen=self.smoothing_window)
        self.last_prediction = {"label": "", "prob": 0.0, "is_violence": False}
    
    def preprocess_frame(self, frame):
        """Convert BGR -> RGB and apply transform."""
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.transform(frame)
    
    def make_slowfast_inputs(self, frames):
        """Build SlowFast inputs [slow, fast]."""
        video = torch.stack(frames)
        video = video.permute(1, 0, 2, 3)
        fast = video
        slow = video[:, ::self.alpha, :, :]
        return [slow.unsqueeze(0), fast.unsqueeze(0)]
    
    def detect(self, frame):
        """
        Run violence detection on a single frame.
        Returns dict with prediction and violence flag.
        """
        self.frame_buffer.append(self.preprocess_frame(frame))
        
        result = {
            "label": self.last_prediction["label"],
            "prob": self.last_prediction["prob"],
            "is_violence": False,  # Only set True if smoothed detection triggers
            "buffer_ready": len(self.frame_buffer) == self.buffer_size
        }
        
        if len(self.frame_buffer) == self.buffer_size:
            inputs = self.make_slowfast_inputs(list(self.frame_buffer))
            inputs = [x.to(self.device) for x in inputs]
            
            with torch.no_grad():
                logits = self.model(inputs)
                probs = torch.softmax(logits, dim=1)[0]
            
            top_prob, top_idx = torch.max(probs, dim=0)
            top_prob = float(top_prob.item())
            idx = int(top_idx.item())
            top_label = self.labels[idx] if idx < len(self.labels) else str(idx)
            
            is_violence = (
                top_prob >= self.violence_threshold and 
                top_prob >= self.confidence_floor and
                any(kw in top_label.lower() for kw in self.violence_keywords)
            )
            
            self.violence_history.append(is_violence)
            is_violence_smooth = (
                len(self.violence_history) == self.smoothing_window and 
                all(self.violence_history)
            )
            
            self.last_prediction = {
                "label": top_label,
                "prob": top_prob,
                "is_violence": is_violence
            }
            
            result.update({
                "label": top_label,
                "prob": top_prob,
                "is_violence": is_violence_smooth
            })
        
        return result


class ViolenceDetectorThread(threading.Thread):
    """Background thread for violence detection."""
    
    def __init__(self, camera_source=0, result_queue=None, stop_event=None):
        super().__init__(daemon=True)
        self.camera_source = camera_source
        self.result_queue = result_queue
        self.stop_event = stop_event or threading.Event()
        self.detector = ViolenceDetector()
        self.cap = None
        self.fps_counter = 0
        self.fps_time = time.time()
        self.current_fps = 0
    
    def run(self):
        """Main detection loop."""
        try:
            self.cap = cv2.VideoCapture(self.camera_source)
            if not self.cap.isOpened():
                if self.result_queue:
                    self.result_queue.put({
                        "error": f"Could not open camera: {self.camera_source}"
                    })
                return
            
            while not self.stop_event.is_set():
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                result = self.detector.detect(frame)
                result["frame"] = frame
                
                # Calculate FPS
                self.fps_counter += 1
                current_time = time.time()
                if current_time - self.fps_time >= 1.0:
                    self.current_fps = self.fps_counter / (current_time - self.fps_time)
                    self.fps_counter = 0
                    self.fps_time = current_time
                
                result["fps"] = self.current_fps
                
                if self.result_queue:
                    try:
                        self.result_queue.put_nowait(result)
                    except:
                        pass
        
        finally:
            if self.cap:
                self.cap.release()
    
    def stop(self):
        """Stop the detection thread."""
        self.stop_event.set()
