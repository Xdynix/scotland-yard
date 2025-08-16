FROM python:3.13-slim-bookworm


WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

COPY --from=ghcr.io/astral-sh/uv:0.8.11 /uv /uvx /bin/
ENV PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_MANAGED_PYTHON=1 \
    UV_FROZEN=1 \
    UV_NO_SYNC=1

ARG INSTALL_DEV_DEPS=false

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    if [ "$INSTALL_DEV_DEPS" = "true" ]; then \
      uv sync --no-install-project; \
    else \
      uv sync --no-install-project --no-dev; \
    fi

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$INSTALL_DEV_DEPS" = "true" ]; then \
      uv sync; \
    else \
      uv sync --no-dev; \
    fi

# Exec form CMD is required to shutdown gracefully.
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
