from datetime import datetime, timezone

from fastapi import HTTPException
from google.cloud.exceptions import Conflict

from app.db import get_db


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def data_rows() -> list[dict]:
    return sorted(({"id": doc.id, **doc.to_dict()} for doc in get_db().collection("data").stream()), key=lambda row: row["date"], reverse=True)


def add_data(payload: dict) -> dict:
    # Date is the document ID so imports can be safely repeated.
    doc_id = payload["date"]
    ref = get_db().collection("data").document(doc_id)
    try:
        ref.create(payload)
    except Conflict:
        raise HTTPException(409, "해당 날짜의 데이터가 이미 있습니다")
    return {"id": doc_id, **payload}


def change_data(doc_id: str, payload: dict) -> dict:
    ref = get_db().collection("data").document(doc_id)
    if not ref.get().exists:
        raise HTTPException(404, "데이터를 찾을 수 없습니다")
    if payload["date"] != doc_id:
        raise HTTPException(400, "날짜는 변경할 수 없습니다")
    ref.set(payload)
    return {"id": doc_id, **payload}


def remove_data(doc_id: str) -> None:
    ref = get_db().collection("data").document(doc_id)
    if not ref.get().exists:
        raise HTTPException(404, "데이터를 찾을 수 없습니다")
    ref.delete()


def save_conversation(payload: dict) -> dict:
    stamp = now_iso()
    data = {**payload, "created_at": stamp, "updated_at": stamp}
    _, ref = get_db().collection("conversations").add(data)
    return {"id": ref.id, **data}


def conversation(doc_id: str) -> dict:
    snap = get_db().collection("conversations").document(doc_id).get()
    if not snap.exists:
        raise HTTPException(404, "대화를 찾을 수 없습니다")
    return {"id": snap.id, **snap.to_dict()}


def conversations() -> list[dict]:
    rows = [{"id": doc.id, **doc.to_dict()} for doc in get_db().collection("conversations").stream()]
    return sorted(({key: value for key, value in row.items() if key != "messages"} for row in rows), key=lambda row: row.get("updated_at", ""), reverse=True)


def remove_conversation(doc_id: str) -> None:
    ref = get_db().collection("conversations").document(doc_id)
    if not ref.get().exists:
        raise HTTPException(404, "대화를 찾을 수 없습니다")
    ref.delete()


def append_exchange(doc_id: str, user_text: str, answer: str) -> dict:
    ref = get_db().collection("conversations").document(doc_id)
    snap = ref.get()
    if not snap.exists:
        raise HTTPException(404, "대화를 찾을 수 없습니다")
    current = snap.to_dict()
    messages = current.get("messages", [])
    messages.extend([{"role": "user", "content": user_text}, {"role": "assistant", "content": answer}])
    # A bounded history also bounds future OpenAI input and Firestore document size.
    ref.update({"messages": messages[-30:], "updated_at": now_iso()})
    return conversation(doc_id)
