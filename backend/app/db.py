import json
import os
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv


load_dotenv()


@lru_cache
def get_db():
    if not firebase_admin._apps:
        raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        if raw:
            credential = credentials.Certificate(json.loads(raw))
        elif path:
            credential = credentials.Certificate(path)
        else:
            raise RuntimeError("Firebase service account is not configured")
        firebase_admin.initialize_app(credential)
    return firestore.client()
