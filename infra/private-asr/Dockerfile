# Dedicated offline ASR image; NEVER overwrite the existing OpenChatCut image.
# Only deploy after existing Cloudflare instance/cost and private R2 credentials
# have been independently verified. No personal audio in build or CI.
FROM python:3.11-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HUB_OFFLINE=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN python -m pip install --no-cache-dir faster-whisper==1.2.1 boto3==1.40.56
COPY content_factory_private_asr.py content_factory_private_asr_runtime.py content_factory_private_asr_r2_bridge.py /app/
# The model must be mounted or pre-provisioned privately before runtime;
# no remote download or GitHub personal voice artifacts.
COPY infra/private-asr/run_private_asr.py /app/
RUN useradd --uid 10001 --create-home asr && chown -R asr:asr /app
USER asr
CMD ["python","-c","import faster_whisper, boto3, content_factory_private_asr_r2_bridge; print('PRIVATE_ASR_IMAGE_READY_NO_MODEL_NO_AUDIO')"]
