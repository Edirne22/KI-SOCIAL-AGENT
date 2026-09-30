FROM node:24-bookworm
ARG OPENCHATCUT_COMMIT=d1af1ade45521e8ed9a5be09e3acad823f269453
RUN apt-get update && apt-get install -y --no-install-recommends git ffmpeg ca-certificates chromium && rm -rf /var/lib/apt/lists/*
WORKDIR /opt
RUN git clone https://github.com/0xsline/OpenChatCut.git openchatcut \
 && cd openchatcut \
 && git checkout "$OPENCHATCUT_COMMIT" \
 && test "$(git rev-parse HEAD)" = "$OPENCHATCUT_COMMIT"
WORKDIR /opt/openchatcut
ENV ONNXRUNTIME_NODE_INSTALL=skip
RUN npm ci
ENV NODE_ENV=production
ENV OPENCHATCUT_DISABLE_HARDWARE_ENCODING=1
ENV OPENCHATCUT_RENDER_CONCURRENCY=50%
ENV OPENCHATCUT_MAX_ACTIVE_EXPORTS=1
EXPOSE 5199
CMD ["npm","run","dev:shared","--","--host","0.0.0.0"]
