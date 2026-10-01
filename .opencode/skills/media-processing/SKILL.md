---
name: FFmpeg Media Processing
description: Deterministic audio/video trimming, mixing and overlays after an approved job.
---
1. Use FFmpeg for deterministic edits. Start from only approved, rights-cleared and sandboxed uploaded files.
2. FFmpeg and ffprobe are installed on the ephemeral GitHub Runner and tested with synthetic audio and video in ai-central-model-skills.yml.
3. Reject arbitrary model-supplied shell commands. A template runner must construct fixed ffmpeg argument arrays and enforce CPU/runtime/media size limits.
4. Validate resulting audio/video streams with ffprobe; archive original/source provenance and result in private R2.
5. OpenChatCut is independent and currently fails separate Cloudflare stability tests; never route ordinary FFmpeg jobs to it unless its readiness gate passes.
