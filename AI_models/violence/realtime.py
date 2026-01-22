"""
Real-time violence detection using SlowFast (Kinetics-400).

IMPORTANT: This model is trained on general actions (Kinetics-400), NOT specifically
for violence. For better accuracy:
- Fine-tune on a violence dataset (RWF-2000, Hockey Fight, etc.)
- Or use a dedicated violence detection model

Current approach uses temporal smoothing + strict thresholds to reduce false positives.
"""

import os
import sys
import time
from collections import deque

import cv2
import torch
import pytorchvideo.models.hub as hub
import torchvision.transforms as transforms


# -------------------------------
# Configuration
# -------------------------------
ALPHA = 4                       # Slow pathway temporal stride
BUFFER_SIZE = 32                # Fast pathway frames per clip
VIOLENCE_THRESHOLD = 0.65       # Raised to reduce false positives (was 0.35)
SMOOTHING_WINDOW = 3            # Require violence detected N times consecutively
CONFIDENCE_FLOOR = 0.20         # Ignore predictions below this confidence
FONT = cv2.FONT_HERSHEY_SIMPLEX

# ===== CAMERA SOURCE =====
# Option 1: Laptop webcam (default)
CAMERA_SOURCE = 0

# Option 2: IP Webcam - uncomment and set your IP camera URL
# CAMERA_SOURCE = "http://192.168.0.107:8080/video"
# OR for RTSP:
# CAMERA_SOURCE = "rtsp://username:password@192.168.1.100:554/stream"
# ========================

LABEL_PATH = os.path.join(os.path.dirname(__file__), "label_map.txt")

# More strict violence keywords
VIOLENCE_KEYWORDS = [
    "punch", "punching", "fight", "fighting", 
    "kicking", "wrestling", "boxing", "slapping",
    "hitting", "violence", "assault"
]

# -------------------------------
# Setup
# -------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

with open(LABEL_PATH, "r", encoding="utf-8") as f:
    LABELS = [x.strip() for x in f if x.strip()]

model = hub.slowfast_r50(pretrained=True)
model = model.to(device).eval()

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize((256, 256)),
    transforms.Normalize((0.45, 0.45, 0.45), (0.225, 0.225, 0.225)),
])

frame_buffer: deque = deque(maxlen=BUFFER_SIZE)
violence_history: deque = deque(maxlen=SMOOTHING_WINDOW)  # Track recent detections


def preprocess_frame(frame):
    """Convert BGR -> RGB and apply SlowFast transform."""
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return transform(frame)  # [C, H, W]


def make_slowfast_inputs(frames):
    """Build SlowFast input list [slow, fast] with shapes [1, C, T, H, W]."""
    video = torch.stack(frames)            # [T, C, H, W]
    video = video.permute(1, 0, 2, 3)      # [C, T, H, W]
    fast = video
    slow = video[:, ::ALPHA, :, :]
    return [slow.unsqueeze(0), fast.unsqueeze(0)]


def draw_overlay(frame, label, prob, is_violence_smooth, fps):
    """Draw prediction + violence alert if smoothed detection triggers."""
    
    # Show current prediction
    color = (0, 200, 0) if not is_violence_smooth else (0, 0, 255)
    text = f"{label} ({prob:.2f})"
    cv2.putText(frame, text, (20, 40), FONT, 1, color, 2)
    
    # Violence alert (only if smoothed detection)
    if is_violence_smooth:
        cv2.rectangle(frame, (5, 5), (frame.shape[1]-5, frame.shape[0]-5), (0, 0, 255), 3)
        cv2.putText(frame, "!!! VIOLENCE DETECTED !!!", (20, 90), 
                    FONT, 1.2, (0, 0, 255), 3)
    
    # FPS
    cv2.putText(frame, f"FPS: {fps:.1f}", (20, frame.shape[0]-20), 
                FONT, 0.6, (255, 255, 255), 2)


def main():
    print("Model and labels are ready ✅")
    print(f"Camera source: {CAMERA_SOURCE}")
    print(f"Violence threshold: {VIOLENCE_THRESHOLD}")
    print(f"Smoothing window: {SMOOTHING_WINDOW} consecutive detections required")
    
    cap = cv2.VideoCapture(CAMERA_SOURCE)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera source: {CAMERA_SOURCE}")

    print("🎥 Starting camera stream... Press 'q' to quit.")

    while True:
        loop_start = time.time()
        ret, frame = cap.read()
        if not ret:
            print("Frame grab failed, exiting.")
            break

        frame_buffer.append(preprocess_frame(frame))

        if len(frame_buffer) == BUFFER_SIZE:
            inputs = make_slowfast_inputs(list(frame_buffer))
            inputs = [x.to(device) for x in inputs]

            with torch.no_grad():
                logits = model(inputs)
                probs = torch.softmax(logits, dim=1)[0]

            # Get top prediction
            top_prob, top_idx = torch.max(probs, dim=0)
            top_prob = float(top_prob.item())
            idx = int(top_idx.item())
            top_label = LABELS[idx] if idx < len(LABELS) else str(idx)
            
            # Only flag if prob is high AND keyword matches
            is_violence = (
                top_prob >= VIOLENCE_THRESHOLD and 
                top_prob >= CONFIDENCE_FLOOR and
                any(kw in top_label.lower() for kw in VIOLENCE_KEYWORDS)
            )
            
            # Add to smoothing history
            violence_history.append(is_violence)
            
            # Trigger alert only if violence detected consecutively
            is_violence_smooth = (
                len(violence_history) == SMOOTHING_WINDOW and 
                all(violence_history)
            )

            fps = 1.0 / max(time.time() - loop_start, 1e-6)
            draw_overlay(frame, top_label, top_prob, is_violence_smooth, fps)

        cv2.imshow("Real-time Violence Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

