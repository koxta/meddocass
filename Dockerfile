FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies only: this layer stays cached until uv.lock or pyproject.toml change
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["fastapi", "run", "--port", "8000"]