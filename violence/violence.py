import torch
import pytorchvideo.models.hub as hub
import torchvision.transforms as transforms
import cv2
import os

# -------------------------------
# Load label map
# -------------------------------
LABEL_PATH = "label_map.txt"
labels = [x.strip() for x in open(LABEL_PATH)]

# -------------------------------
# Load pretrained SlowFast model
# -------------------------------
model = hub.slowfast_r50(pretrained=True)
model.eval()
print("Model and labels are ready ✅")

# -------------------------------
# Preprocessing pipeline
# -------------------------------
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize((256, 256)),
    transforms.Normalize((0.45, 0.45, 0.45), (0.225, 0.225, 0.225)),
])

def load_video_frames(video_path, num_frames=32):
    cap = cv2.VideoCapture(video_path)
    frames = []
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(total_frames // num_frames, 1)

    for i in range(0, total_frames, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = transform(frame)   # C, H, W
        frames.append(frame)
        if len(frames) == num_frames:
            break

    cap.release()
    if len(frames) == 0:
        raise ValueError("❌ No frames extracted from video")

    video = torch.stack(frames)  # T, C, H, W
    video = video.permute(1, 0, 2, 3)  # C, T, H, W
    return video.unsqueeze(0)   # 1, C, T, H, W

# -------------------------------
# Run test on a sample video
# -------------------------------
video_path = "1.mp4"
if os.path.exists(video_path):
    video_tensor = load_video_frames(video_path)

    # ✅ Split into Slow & Fast pathways
    fast_path = video_tensor  # full frame sequence
    slow_path = video_tensor[:, :, ::4, :, :]  # subsample every 4th frame

    inputs = [slow_path, fast_path]

    with torch.no_grad():
        preds = model(inputs)

    # Convert logits → probabilities
    probs = torch.nn.functional.softmax(preds[0], dim=0)

    # Sort all predictions
    sorted_indices = torch.argsort(probs, descending=True)

    print("\nPredictions (based on actual video):")
    for idx in sorted_indices.tolist():
        print(f"{labels[idx]} ({probs[idx].item():.4f})")

else:
    print(f"⚠️ Video file {video_path} not found. Put a test video in this folder.")
