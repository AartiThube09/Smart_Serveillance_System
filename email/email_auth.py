from __future__ import annotations

import json
import os
import threading
import queue
import time
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / 'configs'
CONFIG_DIR.mkdir(exist_ok=True)
EMAIL_CONFIG_PATH = CONFIG_DIR / 'email_config.json'
VERIF_LOG = CONFIG_DIR / 'verification_log.txt'


def append_verification_log(line: str):
    try:
        ts = time.strftime('%Y-%m-%d %H:%M:%S')
        VERIF_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(VERIF_LOG, 'a', encoding='utf-8') as f:
            f.write(f'[{ts}] {line}\n')
    except Exception:
        pass


def load_email_config() -> dict:
    default = {"enabled": False, "sender_email": "", "sender_password": ""}
    if EMAIL_CONFIG_PATH.exists():
        try:
            return json.loads(EMAIL_CONFIG_PATH.read_text(encoding='utf-8'))
        except Exception:
            return default
    EMAIL_CONFIG_PATH.write_text(json.dumps(default, indent=2), encoding='utf-8')
    return default


def save_email_config(cfg: dict):
    EMAIL_CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding='utf-8')


def send_verification_code(pending_codes: dict, email: str, ttl: int = 300) -> tuple[bool, str]:
    """Send a 6-digit verification code using the admin SMTP credentials.

    pending_codes is a dict-like object that will be updated with the code
    (email -> (code, expiry_ts)). Returns (ok, err_message).
    """
    try:
        append_verification_log(f'SEND_ATTEMPT {email}')
    except Exception:
        pass
    cfg = load_email_config()
    sender = cfg.get('sender_email')
    pwd = cfg.get('sender_password')
    if not sender or not pwd:
        return False, 'Admin sender not configured'
    import random
    code = f"{random.randint(100000, 999999)}"
    now = time.time()
    expiry = now + ttl
    try:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = email
        msg['Subject'] = 'Your Surveillance System Verification Code'
        body = f'Your verification code is: {code}\n\nThis code will expire in {int(ttl/60)} minutes.'
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo()
            s.starttls()
            s.login(sender, pwd)
            s.sendmail(sender, [email], msg.as_string())
        # store code
        try:
            pending_codes[email] = (code, expiry)
        except Exception:
            # best-effort only
            pass
        try:
            append_verification_log(f'SEND {email} OK ttl={int(ttl)}s')
            if os.environ.get('SURVEILLANCE_DEBUG_SHOW_CODE') == '1':
                append_verification_log(f'DEBUG_CODE {email} {code}')
        except Exception:
            pass
        return True, ''
    except Exception as e:
        try:
            append_verification_log(f'SEND {email} FAIL {e}')
        except Exception:
            pass
        return False, str(e)


def send_verification_code_async(master, pending_codes: dict, email: str, ttl: int = 300, callback=None):
    """Send verification code on a background thread and call callback(ok, err)
    on the Tk main thread (master.after)."""
    q = queue.Queue()

    def _worker():
        ok, err = send_verification_code(pending_codes, email, ttl=ttl)
        try:
            append_verification_log(f'SEND_WORKER_DONE {email} ok={ok}')
        except Exception:
            pass
        try:
            q.put((ok, err))
        except Exception:
            try:
                append_verification_log(f'QUEUE_PUT_FAIL {email}')
            except Exception:
                pass

    threading.Thread(target=_worker, daemon=True).start()

    def _poll():
        try:
            ok, err = q.get_nowait()
        except Exception:
            try:
                master.after(100, _poll)
            except Exception:
                try:
                    append_verification_log(f'POLL_SCHEDULE_FAIL {email}')
                except Exception:
                    pass
            return
        if callback:
            try:
                callback(ok, err)
            except Exception as e:
                try:
                    append_verification_log(f'CALLBACK_RUN_FAIL {email} {e}')
                except Exception:
                    pass

    try:
        master.after(50, _poll)
    except Exception:
        try:
            append_verification_log(f'POLL_START_FAIL {email}')
        except Exception:
            pass


__all__ = [
    'load_email_config', 'save_email_config', 'append_verification_log',
    'send_verification_code', 'send_verification_code_async'
]

