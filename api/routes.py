from fastapi import APIRouter, Request, Query
from .socketio_event import emit_test_event

router = APIRouter()


@router.get("/test")
def test():
    payload = emit_test_event()
    return {
        "status": "ok",
        "message": "Hello World",
        "emitted": payload,
    }
