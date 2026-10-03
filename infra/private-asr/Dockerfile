# Dedicated offline ASR image; NEVER overwrite the existing OpenChatCut image.
# Only deploy after existing Cloudflare instance/cost and private R2 credentials
# have been independently verified. No personal audio in build or CI.
FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1 \
    EDIRNE22_LOCAL_WHISPER_MODEL=/opt/private-asr-model
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN python -m pip install --no-cache-dir faster-whisper==1.2.1 boto3==1.40.56 huggingface-hub==0.35.3 scenedetect[opencv-headless]==0.6.7
# Fetch multilingual tiny model at IMAGE BUILD only. Runtime is offline; no user audio in image.
RUN HF_HUB_OFFLINE=0 python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Systran/faster-whisper-tiny', local_dir='/opt/private-asr-model', allow_patterns=['config.json','model.bin','tokenizer.json','vocabulary.*'])" \
 && test -s /opt/private-asr-model/model.bin \
 && test -s /opt/private-asr-model/config.json
COPY content_factory_private_asr.py content_factory_private_asr_runtime.py content_factory_private_asr_r2_bridge.py /app/
# Bundled model runs offline; never include personal audio in build or CI.
COPY infra/private-asr/run_private_asr.py infra/private-asr/service.py /app/
RUN useradd --uid 10001 --create-home asr && chown -R asr:asr /app /opt/private-asr-model
USER asr
EXPOSE 5200
CMD ["python", "/app/service.py"]
