from fastapi import FastAPI
from .routes import router

app = FastAPI(title="API Dashboard Crypto")


app.include_router(router, prefix="/api")
