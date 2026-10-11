from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from meddocass.api.routes import router


app = FastAPI()
app.include_router(router)