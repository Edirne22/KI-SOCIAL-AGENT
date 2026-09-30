FROM python:3.11-slim
ARG SUPOCLIP_COMMIT=3cbe23d25acdca15a3f46b28a9700a244559ab26
RUN apt-get update && apt-get install -y --no-install-recommends git ffmpeg curl ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /opt
RUN git clone https://github.com/FujiwaraChoki/supoclip.git supoclip \
 && cd supoclip \
 && git checkout "$SUPOCLIP_COMMIT" \
 && test "$(git rev-parse HEAD)" = "$SUPOCLIP_COMMIT"
WORKDIR /opt/supoclip/backend
RUN pip install --no-cache-dir uv && uv venv .venv && uv sync
EXPOSE 8000
CMD [".venv/bin/uvicorn","src.main:app","--host","0.0.0.0","--port","8000"]
