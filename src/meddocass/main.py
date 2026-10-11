import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from meddocass.api.routes import router
from meddocass.config import get_settings
from meddocass.dependencies import get_datastore, get_generator
from meddocass.observability import request_id_var, setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info("starting %s", settings.app_name)
    get_datastore().ensure_collection()
    get_generator()
    yield


app = FastAPI(title="Medical Document Assistant", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    token = request_id_var.set(request_id)
    start = time.perf_counter()
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "%s %s -> %s in %.0f ms",
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter() - start) * 1000,
        )
        return response
    except Exception:
        logger.exception("%s %s failed", request.method, request.url.path)
        raise
    finally:
        request_id_var.reset(token)
