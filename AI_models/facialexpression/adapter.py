try:
    from fer import FER
except Exception:
    FER = None

def load_model(pretrained: bool = False):
    if FER is None:
        raise ImportError('fer library not available')
    # FER detector initialization; the module's detector variable is used by callers.
    detector = FER(mtcnn=True)
    return detector

__all__ = ['load_model']
