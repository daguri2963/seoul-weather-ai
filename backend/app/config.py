import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@lru_cache
def allowed_origins() -> list[str]:
    default = "http://localhost:5500,http://127.0.0.1:5500,https://seoul-weather-ai-frontend.vercel.app"
    return [item.strip().rstrip("/") for item in os.getenv("ALLOWED_ORIGINS", default).split(",") if item.strip()]
