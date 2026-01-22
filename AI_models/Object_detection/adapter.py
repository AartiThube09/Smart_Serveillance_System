from pathlib import Path
try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

ROOT = Path(__file__).parent

def _find_weight():
    for w in ('best.pt', 'yolov8n.pt', 'yolov8s.pt'):
        p = ROOT / w
        if p.exists():
            return str(p)
    return None

def load_model(pretrained: bool = False):
    if YOLO is None:
        raise ImportError('ultralytics YOLO not available')
    w = _find_weight()
    if w:
        return YOLO(w)
    return YOLO('yolov8n.pt')

__all__ = ['load_model']
