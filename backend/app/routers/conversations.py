from fastapi import APIRouter, status

from app.models import ConversationInput
from app.services import store

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_conversation(item: ConversationInput):
    return store.save_conversation(item.model_dump())


@router.get("")
def list_conversations():
    """List metadata only. Use GET /{id} for the full messages."""
    return store.conversations()


@router.get("/{doc_id}")
def get_conversation(doc_id: str):
    return store.conversation(doc_id)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(doc_id: str):
    store.remove_conversation(doc_id)
