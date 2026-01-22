from pathlib import Path
try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

ROOT = Path(__file__).parent

def _find_weight():
    for w in ('yolov8s.pt', 'yolov8n.pt', 'best.pt'):
        p = ROOT / w
        if p.exists():
            return str(p)
    return None

def load_model(pretrained: bool = False):
    """Return a YOLO model for crowd detection. Looks for weights in this folder.

    If ultralytics isn't available, raises ImportError.
    """
    if YOLO is None:
        raise ImportError('ultralytics YOLO not available')
    w = _find_weight()
    if w:
        return YOLO(w)
    # fallback to a small default if available via name
    # try a named fallback; let any exception propagate to caller
    return YOLO('yolov8n.pt')

__all__ = ['load_model']
