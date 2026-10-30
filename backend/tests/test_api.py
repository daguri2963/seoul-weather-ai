import os

from fastapi.testclient import TestClient

from app.main import app
from app.routers import chat
from app.services import store
from app.services.summary import summarize


def test_summary_uses_current_sorted_values():
    rows = [{"date": f"2024-01-{day:02}", "value": value} for day, value in enumerate(range(1, 15), 1)]
    result = summarize(list(reversed(rows)))
    assert result["count"] == 14
    assert result["metrics"] == {"average": 7.5, "max": 14.0, "min": 1.0}
    assert result["trend"] == "상승"
    assert result["recent_change_c"] == 7.0


def test_validation_and_routes(monkeypatch):
    monkeypatch.delenv("API_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(store, "data_rows", lambda: [{"id": "2024-01-01", "date": "2024-01-01", "value": 7.3, "memo": "source"}])
    monkeypatch.setattr(store, "add_data", lambda item: {"id": item["date"], **item})
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/docs").status_code == 200
    assert client.get("/api/data/summary").json()["count"] == 1
    assert client.post("/api/data", json={"date": "2024-01-02", "value": 4.3, "memo": "ok"}).status_code == 201
    assert client.post("/api/data", json={"date": "bad", "value": "nan"}).status_code == 422


def test_chat_injects_summary_and_saves(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://copa.codyssey.kr/v1")
    monkeypatch.delenv("API_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(store, "data_rows", lambda: [{"id": "2024-01-01", "date": "2024-01-01", "value": 7.3}])
    saved = []
    monkeypatch.setattr(store, "save_conversation", lambda item: saved.append(item) or {"id": "conversation-1", **item})

    class FakeCompletions:
        def create(self, **kwargs):
            assert "건수: 1" in kwargs["messages"][0]["content"]
            assert kwargs["max_completion_tokens"] == 350
            return type("Result", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "평균은 7.3°C입니다."})()})()]})()

    class FakeOpenAI:
        def __init__(self, **kwargs):
            assert kwargs["base_url"] == "https://copa.codyssey.kr/v1"
            self.chat = type("Chat", (), {"completions": FakeCompletions()})()

    monkeypatch.setattr(chat, "OpenAI", FakeOpenAI)
    response = TestClient(app).post("/api/chat", json={"message": "평균은?"})
    assert response.status_code == 200
    assert response.json()["conversation_id"] == "conversation-1"
    assert saved[0]["messages"][-1]["content"] == "평균은 7.3°C입니다."


def test_access_token(monkeypatch):
    monkeypatch.setenv("API_ACCESS_TOKEN", "secret-test-value")
    client = TestClient(app)
    assert client.get("/api/data").status_code == 401
    assert client.get("/health").status_code == 200
