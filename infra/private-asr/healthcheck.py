"""Offline model readiness probe. Never reads private audio."""
import os
import sys

model = os.environ.get('EDIRNE22_LOCAL_WHISPER_MODEL', '')
ready = bool(model and os.path.isfile(os.path.join(model, 'model.bin')) and os.path.isfile(os.path.join(model, 'config.json')))
print('PRIVATE_ASR_READY' if ready else 'PRIVATE_ASR_NOT_READY')
sys.exit(0 if ready else 1)
