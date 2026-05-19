from fastapi import APIRouter, Request, Query

router = APIRouter()


@router.get("/test")
def test():
    return "Hello World"
