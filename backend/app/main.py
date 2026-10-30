import hmac
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import allowed_origins
from app.routers import chat, conversations, data

app = FastAPI(title="서울 기온 데이터 AI", version="1.0.0")


@app.middleware("http")
async def access_guard(request: Request, call_next):
    token = os.getenv("API_ACCESS_TOKEN")
    if token and request.url.path.startswith("/api/") and request.method != "OPTIONS":
        supplied = request.headers.get("X-Access-Token", "")
        if not hmac.compare_digest(supplied, token):
            return JSONResponse({"detail": "접근 토큰을 확인하세요"}, status_code=401)
    return await call_next(request)


app.add_middleware(CORSMiddleware, allow_origins=allowed_origins(), allow_credentials=False, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type", "X-Access-Token"])
app.include_router(data.router)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
