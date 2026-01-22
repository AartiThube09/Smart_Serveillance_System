"""
Test violence detection on a video file or image before running real-time.
This helps verify the model is working correctly.
"""

import os
import time
from collections import deque

import cv2
import torch
import pytorchvideo.models.hub as hub
import torchvision.transforms as transforms


# -------------------------------
# Configuration
# -------------------------------
ALPHA = 4
BUFFER_SIZE = 32
VIOLENCE_THRESHOLD = 0.65
SMOOTHING_WINDOW = 3
CONFIDENCE_FLOOR = 0.20
FONT = cv2.FONT_HERSHEY_SIMPLEX

# ===== INPUT VIDEO/IMAGE =====
# Put your video or image path here
INPUT_PATH = r"C:\Users\Aarti Thube\OneDrive\Desktop\test_video.mp4"
# Or use an image:
# INPUT_PATH = r"C:\Users\Aarti Thube\OneDrive\Desktop\test_image.jpg"
# ============================

LABEL_PATH = os.path.join(os.path.dirname(__file__), "label_map.txt")

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

print("Loading SlowFast model...")
model = hub.slowfast_r50(pretrained=True)
model = model.to(device).eval()
print("✅ Model loaded")

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize((256, 256)),
    transforms.Normalize((0.45, 0.45, 0.45), (0.225, 0.225, 0.225)),
])

frame_buffer: deque = deque(maxlen=BUFFER_SIZE)
violence_history: deque = deque(maxlen=SMOOTHING_WINDOW)


def preprocess_frame(frame):
    """Convert BGR -> RGB and apply SlowFast transform."""
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return transform(frame)


def make_slowfast_inputs(frames):
    """Build SlowFast input list [slow, fast] with shapes [1, C, T, H, W]."""
    video = torch.stack(frames)
    video = video.permute(1, 0, 2, 3)
    fast = video
    slow = video[:, ::ALPHA, :, :]
    return [slow.unsqueeze(0), fast.unsqueeze(0)]


def draw_overlay(frame, label, prob, is_violence_smooth, fps):
    """Draw prediction + violence alert if smoothed detection triggers."""
    color = (0, 200, 0) if not is_violence_smooth else (0, 0, 255)
    text = f"{label} ({prob:.2f})"
    cv2.putText(frame, text, (20, 40), FONT, 1, color, 2)
    
    if is_violence_smooth:
        cv2.rectangle(frame, (5, 5), (frame.shape[1]-5, frame.shape[0]-5), (0, 0, 255), 3)
        cv2.putText(frame, "!!! VIOLENCE DETECTED !!!", (20, 90), 
                    FONT, 1.2, (0, 0, 255), 3)
    
    cv2.putText(frame, f"FPS: {fps:.1f}", (20, frame.shape[0]-20), 
                FONT, 0.6, (255, 255, 255), 2)


def main():
    if not os.path.exists(INPUT_PATH):
        print(f"❌ File not found: {INPUT_PATH}")
        print("\nPlease set INPUT_PATH to your video or image file.")
        return
    
    print(f"Input: {INPUT_PATH}")
    print(f"Violence threshold: {VIOLENCE_THRESHOLD}")
    print(f"Smoothing window: {SMOOTHING_WINDOW} consecutive detections\n")
    
    # Check if image or video
    is_image = INPUT_PATH.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))
    
    if is_image:
        # Single image - repeat frame to fill buffer
        img = cv2.imread(INPUT_PATH)
        if img is None:
            print(f"❌ Could not read image: {INPUT_PATH}")
            return
        
        print("Processing image...")
        for _ in range(BUFFER_SIZE):
            frame_buffer.append(preprocess_frame(img))
        
        inputs = make_slowfast_inputs(list(frame_buffer))
        inputs = [x.to(device) for x in inputs]
        
        with torch.no_grad():
            logits = model(inputs)
            probs = torch.softmax(logits, dim=1)[0]
        
        top_prob, top_idx = torch.max(probs, dim=0)
        top_prob = float(top_prob.item())
        idx = int(top_idx.item())
        top_label = LABELS[idx] if idx < len(LABELS) else str(idx)
        
        is_violence = (
            top_prob >= VIOLENCE_THRESHOLD and 
            any(kw in top_label.lower() for kw in VIOLENCE_KEYWORDS)
        )
        
        print(f"Prediction: {top_label}")
        print(f"Confidence: {top_prob:.2f}")
        print(f"Violence: {'YES ⚠️' if is_violence else 'NO ✅'}")
        
        draw_overlay(img, top_label, top_prob, is_violence, 0)
        cv2.imshow("Violence Detection - Image", img)
        print("\nPress any key to close...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    else:
        # Video file
        cap = cv2.VideoCapture(INPUT_PATH)
        if not cap.isOpened():
            print(f"❌ Could not open video: {INPUT_PATH}")
            return
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Processing video ({total_frames} frames)...")
        print("Press 'q' to quit, 'space' to pause\n")
        
        paused = False
        
        while True:
            if not paused:
                loop_start = time.time()
                ret, frame = cap.read()
                if not ret:
                    print("End of video.")
                    break
                
                frame_buffer.append(preprocess_frame(frame))
                
                if len(frame_buffer) == BUFFER_SIZE:
                    inputs = make_slowfast_inputs(list(frame_buffer))
                    inputs = [x.to(device) for x in inputs]
                    
                    with torch.no_grad():
                        logits = model(inputs)
                        probs = torch.softmax(logits, dim=1)[0]
                    
                    top_prob, top_idx = torch.max(probs, dim=0)
                    top_prob = float(top_prob.item())
                    idx = int(top_idx.item())
                    top_label = LABELS[idx] if idx < len(LABELS) else str(idx)
                    
                    is_violence = (
                        top_prob >= VIOLENCE_THRESHOLD and 
                        top_prob >= CONFIDENCE_FLOOR and
                        any(kw in top_label.lower() for kw in VIOLENCE_KEYWORDS)
                    )
                    
                    violence_history.append(is_violence)
                    is_violence_smooth = (
                        len(violence_history) == SMOOTHING_WINDOW and 
                        all(violence_history)
                    )
                    
                    fps = 1.0 / max(time.time() - loop_start, 1e-6)
                    draw_overlay(frame, top_label, top_prob, is_violence_smooth, fps)
                    
                    if is_violence_smooth:
                        print(f"⚠️  Violence detected: {top_label} ({top_prob:.2f})")
            
            cv2.imshow("Violence Detection - Video", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):
                paused = not paused
                print("Paused" if paused else "Resumed")
        
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
