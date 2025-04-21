FROM python:3.13-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.6.13 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

ARG INSTALL_DEV_DEPS=false
ENV INSTALL_DEV_DEPS=${INSTALL_DEV_DEPS}

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    if [ "$INSTALL_DEV_DEPS" = "true" ]; then \
      uv sync --frozen --no-install-project; \
    else \
      uv sync --frozen --no-install-project --no-dev; \
    fi

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$INSTALL_DEV_DEPS" = "true" ]; then \
      uv sync --frozen; \
    else \
      uv sync --frozen --no-dev; \
    fi

# Exec form CMD is required to shutdown gracefully.
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
