FROM python:3.12-slim-bookworm AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

RUN apt-get update -qy
RUN apt-get install -qyy -o APT::Install-Recommends=false -o APT::Install-Suggests=false ca-certificates \
    git wget curl
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

WORKDIR /app


COPY uv.lock pyproject.toml .python-version ./
RUN --mount=type=secret,id=netrc,target=/root/.netrc,mode=0600 \
    uv sync --frozen --no-dev --no-install-project

COPY . /app

FROM python:3.12-slim-bookworm

COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:${PYTHONPATH:-}"

WORKDIR /app

CMD alembic upgrade head && python app/main.py
