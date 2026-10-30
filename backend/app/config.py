import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@lru_cache
def allowed_origins() -> list[str]:
    return [item.strip().rstrip("/") for item in os.getenv("ALLOWED_ORIGINS", "http://localhost:5500").split(",") if item.strip()]
