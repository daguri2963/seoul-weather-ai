from fastapi import APIRouter, status

from app.models import DataInput
from app.services import store
from app.services.summary import summarize

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/summary")
def get_summary():
    return summarize(store.data_rows())


@router.post("", status_code=status.HTTP_201_CREATED)
def create_data(item: DataInput):
    return store.add_data({**item.model_dump(), "date": item.date.isoformat()})


@router.get("")
def list_data():
    return store.data_rows()


@router.put("/{doc_id}")
def update_data(doc_id: str, item: DataInput):
    return store.change_data(doc_id, {**item.model_dump(), "date": item.date.isoformat()})


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_data(doc_id: str):
    store.remove_data(doc_id)
