# Dedicated offline ASR image; NEVER overwrite the existing OpenChatCut image.
# Only deploy after existing Cloudflare instance/cost and private R2 credentials
# have been independently verified. No personal audio in build or CI.
FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 \
    EDIRNE22_LOCAL_WHISPER_MODEL=/opt/private-asr-model
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates fonts-dejavu-core git nodejs npm \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# OpenCode is baked into the paid container image once; never install it per chat request.
# Pinning prevents an upstream latest release from silently changing the production machine.
ARG OPENCODE_VERSION=2.0.21
RUN npm install --global "@opencode/cli@${OPENCODE_VERSION}" \
 && opencode --version | grep -F "${OPENCODE_VERSION}" \
 && npm cache clean --force
# Claude-only read-only config is immutable in the runtime image; no provider key is baked in.
COPY infra/ai-central-tools/claude-only/opencode.jsonc /etc/opencode/opencode.json
COPY infra/ai-central-tools/claude-code-readonly/opencode.jsonc /etc/opencode/code.json
RUN chmod 0444 /etc/opencode/opencode.json /etc/opencode/code.json \
 && sha256sum /etc/opencode/opencode.json | cut -d' ' -f1 > /etc/opencode/opencode.json.sha256 \
 && sha256sum /etc/opencode/code.json | cut -d' ' -f1 > /etc/opencode/code.json.sha256 \
 && chmod 0444 /etc/opencode/opencode.json.sha256 /etc/opencode/code.json.sha256
RUN python -m pip install --no-cache-dir faster-whisper==1.2.1 boto3==1.40.56 requests==2.32.5 huggingface-hub==0.35.3 scenedetect[opencv-headless]==0.6.7
# Fetch multilingual tiny model at IMAGE BUILD only. Runtime is offline; no user audio in image.
RUN HF_HUB_OFFLINE=0 python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Systran/faster-whisper-tiny', local_dir='/opt/private-asr-model', allow_patterns=['config.json','model.bin','tokenizer.json','vocabulary.*'])" \
 && test -s /opt/private-asr-model/model.bin \
 && test -s /opt/private-asr-model/config.json
COPY content_factory_private_asr.py content_factory_private_asr_runtime.py content_factory_private_asr_r2_bridge.py /app/
COPY music_agent.py content_factory_private_video_orchestrator.py /app/
COPY scripts/private_birthday_first_production.py scripts/ai_central_shared_inbox.py scripts/r2_media_warehouse.py /app/scripts/
COPY assets/musik/chill/hypnotic-ambient.mp3 /app/assets/musik/chill/hypnotic-ambient.mp3
COPY config/MUSIC_LIBRARY.json /app/config/MUSIC_LIBRARY.json
# Bundled model runs offline; never include personal audio in build or CI.
COPY search_provider.py /app/search_provider.py
COPY infra/private-asr/research_gateway.py /app/research_gateway.py
COPY infra/private-asr/run_private_asr.py infra/private-asr/service.py infra/private-asr/verify_opencode_image.py /app/
RUN useradd --uid 10001 --create-home asr && chown -R asr:asr /app /opt/private-asr-model
USER asr
RUN python /app/verify_opencode_image.py
EXPOSE 5200
CMD ["python", "/app/service.py"]
