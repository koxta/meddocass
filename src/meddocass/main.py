from contextlib import asynccontextmanager

from fastapi import FastAPI
from meddocass.api.routes import router
from meddocass.dependencies import get_datastore


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_datastore()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)
