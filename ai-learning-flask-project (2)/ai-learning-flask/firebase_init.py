import os

# ✅ FIXED: Use absolute path so serviceAccountKey.json is always found
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def init_firebase():
    """Initialize Firebase Admin SDK. Safe to call even if key is missing."""
    try:
        import firebase_admin
        from firebase_admin import credentials

        # ✅ Look for key file next to this script (not relative to CWD)
        key_path = os.path.join(BASE_DIR, 'serviceAccountKey.json')

        # If key file doesn't exist, skip Firebase silently
        if not os.path.exists(key_path):
            print(f"[Firebase] serviceAccountKey.json not found at {key_path} — Firebase disabled.")
            return False

        # Don't re-initialize if already done
        if not firebase_admin._apps:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            print("[Firebase] Initialized successfully.")
        return True

    except ImportError:
        print("[Firebase] firebase-admin not installed — Firebase disabled.")
        return False
    except Exception as e:
        print(f"[Firebase] Init error: {e}")
        return False


def verify_token(id_token):
    """Verify a Firebase ID token. Returns decoded token dict or None."""
    try:
        import firebase_admin
        from firebase_admin import auth

        if not firebase_admin._apps:
            print("[Firebase] Not initialized — cannot verify token.")
            return None

        decoded = auth.verify_id_token(id_token)
        return decoded

    except Exception as e:
        print(f"[Firebase] Token verification failed: {e}")
        return None
