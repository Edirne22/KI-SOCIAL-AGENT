FROM node:24-bookworm
ARG OPENCHATCUT_COMMIT=d1af1ade45521e8ed9a5be09e3acad823f269453
RUN apt-get update && apt-get install -y --no-install-recommends git ffmpeg ca-certificates chromium python3 python3-venv && rm -rf /var/lib/apt/lists/*
WORKDIR /opt
RUN git clone https://github.com/0xsline/OpenChatCut.git openchatcut \
 && cd openchatcut \
 && git checkout "$OPENCHATCUT_COMMIT" \
 && test "$(git rev-parse HEAD)" = "$OPENCHATCUT_COMMIT"
WORKDIR /opt/openchatcut
ENV ONNXRUNTIME_NODE_INSTALL=skip
RUN npm ci
# Provision the small multilingual DE/TR model at image build time.
RUN python3 -m venv /opt/private-asr-venv \
 && /opt/private-asr-venv/bin/pip install --no-cache-dir faster-whisper==1.2.1 boto3==1.40.56 \
 && /opt/private-asr-venv/bin/python -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-tiny',local_dir='/opt/private-asr-model')" \
 && test -s /opt/private-asr-model/model.bin
COPY content_factory_private_asr.py content_factory_private_asr_runtime.py content_factory_private_asr_r2_bridge.py /opt/private-asr/
COPY infra/openchatcut-cloudflare/private_asr_server.py /opt/private-asr/
ENV PYTHONPATH=/opt/private-asr EDIRNE22_LOCAL_WHISPER_MODEL=/opt/private-asr-model HF_HUB_OFFLINE=1
ENV NODE_ENV=production
ENV OPENCHATCUT_DISABLE_HARDWARE_ENCODING=1
ENV OPENCHATCUT_RENDER_CONCURRENCY=50%
ENV OPENCHATCUT_MAX_ACTIVE_EXPORTS=1
EXPOSE 5199
CMD ["/bin/sh","-c","/opt/private-asr-venv/bin/python /opt/private-asr/private_asr_server.py & exec npm run dev:shared -- --host 0.0.0.0"]
