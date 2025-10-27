"""SlowFast violence detection helpers.

This module exposes simple, import-safe helpers to load the SlowFast model and
run inference on a video file or a tensor of frames. The previous version ran a
test at import time which caused side-effects; this refactor avoids that and
returns functions the main app can call when ready.
"""

import os
from typing import List, Tuple

try:
    import torch
    import pytorchvideo.models.hub as hub
    import torchvision.transforms as transforms
    import cv2
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False


LABEL_PATH = os.path.join(os.path.dirname(__file__), "label_map.txt")


def _load_labels() -> List[str]:
    if os.path.exists(LABEL_PATH):
        with open(LABEL_PATH, "r", encoding="utf-8") as f:
            return [x.strip() for x in f if x.strip()]
    return []


def load_model(pretrained: bool = True):
    """Load and return the SlowFast model (or raise ImportError).

    Returns the model in eval() mode.
    """
    if not TORCH_AVAILABLE:
        raise ImportError("pytorch/pytorchvideo not available in this environment")
    model = hub.slowfast_r50(pretrained=pretrained)
    model.eval()
    return model


def default_transform():
    return transforms.Compose([
        transforms.ToTensor(),
        transforms.Resize((256, 256)),
        transforms.Normalize((0.45, 0.45, 0.45), (0.225, 0.225, 0.225)),
    ])


def load_video_frames(video_path: str, num_frames: int = 32, transform=None) -> torch.Tensor:
    """Extract up to num_frames from video_path and return a tensor shaped
    (1, C, T, H, W) compatible with SlowFast (C, T, H, W inside batch).
    """
    if not TORCH_AVAILABLE:
        raise ImportError("torch is required to load video frames")

    if transform is None:
        transform = default_transform()

    cap = cv2.VideoCapture(video_path)
    frames = []
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    step = max(total_frames // num_frames, 1) if total_frames > 0 else 1

    for i in range(0, total_frames or num_frames, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = transform(frame)   
        frames.append(frame)
        if len(frames) == num_frames:
            break

    cap.release()
    if len(frames) == 0:
        raise ValueError("No frames extracted from video")

    video = torch.stack(frames)  
    video = video.permute(1, 0, 2, 3) 
    return video.unsqueeze(0)  


def predict_from_video(model, video_path: str, num_frames: int = 32) -> List[Tuple[str, float]]:
    """Run the SlowFast model on a video file and return a list of (label, prob)
    sorted by probability descending.
    """
    labels = _load_labels()
    video_tensor = load_video_frames(video_path, num_frames=num_frames)

    # Slow & fast pathways
    fast_path = video_tensor
    slow_path = video_tensor[:, :, ::4, :, :]
    inputs = [slow_path, fast_path]

    with torch.no_grad():
        preds = model(inputs)

    probs = torch.nn.functional.softmax(preds[0], dim=0)
    sorted_indices = torch.argsort(probs, descending=True)
    results = []
    for idx in sorted_indices.tolist():
        label = labels[idx] if idx < len(labels) else str(idx)
        results.append((label, float(probs[idx].item())))
    return results


__all__ = [
    "load_model",
    "load_video_frames",
    "predict_from_video",
    "default_transform",
]
