import torch
import pytorchvideo.models.hub as hub
import torchvision.transforms as transforms
import cv2

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
# Preprocessing
# -------------------------------
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Resize((256, 256)),
    transforms.Normalize((0.45, 0.45, 0.45), (0.225, 0.225, 0.225)),
])

# Violence-related keywords to filter
violence_keywords = ["fight", "fighting", "punch", "kicking", "wrestling", "boxing"]

# -------------------------------
# Frame buffer for SlowFast (needs a clip, not 1 frame)
# -------------------------------
buffer_size = 32
frame_buffer = []

def preprocess_frame(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = transform(frame)  # [C, H, W]
    return frame

def make_slowfast_inputs(frames):
    # Stack frames into [T, C, H, W] then permute → [C, T, H, W]
    video = torch.stack(frames).permute(1, 0, 2, 3)

    # Create SlowFast inputs: [slow_path, fast_path]
    fast_pathway = video
    # Slow pathway samples every 4th frame
    slow_pathway = video[:, ::4, :, :]
    return [slow_pathway.unsqueeze(0), fast_pathway.unsqueeze(0)]

# -------------------------------
# Real-time webcam loop
# -------------------------------
cap = cv2.VideoCapture(0)  # 0 = default webcam
print("🎥 Starting webcam... Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Preprocess and store in buffer
    processed = preprocess_frame(frame)
    frame_buffer.append(processed)

    # Keep only last buffer_size frames
    if len(frame_buffer) > buffer_size:
        frame_buffer.pop(0)

    # Run model only if buffer is full
    if len(frame_buffer) == buffer_size:
        inputs = make_slowfast_inputs(frame_buffer)

        with torch.no_grad():
            preds = model(inputs)

        probs = torch.nn.functional.softmax(preds[0], dim=0)

        # Find top prediction
        top_idx = torch.argmax(probs).item()
        top_label = labels[top_idx]
        top_conf = probs[top_idx].item()

        # Check if it's violence-related
        is_violence = any(k in top_label.lower() for k in violence_keywords)

        # Display on video
        text = f"{top_label} ({top_conf:.2f})"
        color = (0, 0, 255) if is_violence else (0, 255, 0)  # red for violence
        cv2.putText(frame, text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    # Show video
    cv2.imshow("Real-time Violence Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

