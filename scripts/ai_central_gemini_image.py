"""Isolated Nano Banana 2 adapter, NOT active in live image router yet.

Uses existing GEMINI_API_KEY from GitHub Secrets; a model catalog listing is not
generation authorization or proof of free quota. One call only after opt-in.
"""
from __future__ import annotations
import base64
import binascii
import os
import re
import requests

MODELS={"lite":"gemini-3.1-flash-lite-image","standard":"gemini-3.1-flash-image",
        "pro":"gemini-3-pro-image"}
MAX_IMAGE=12*1024*1024
class ImageGenerationError(RuntimeError):pass

def image_from_response(data):
    # Official Interactions API exposes interaction.output_image.
    if not isinstance(data,dict):raise ImageGenerationError("non-json interaction response")
    interaction=data.get("interaction",data)
    image=interaction.get("output_image") if isinstance(interaction,dict) else None
    if not isinstance(image,dict) or not isinstance(image.get("data"),str):
        raise ImageGenerationError("no returned output_image data")
    try:raw=base64.b64decode(image["data"],validate=True)
    except (binascii.Error,ValueError):
        raise ImageGenerationError("invalid image encoding") from None
    if not 100<=len(raw)<=MAX_IMAGE:raise ImageGenerationError("unexpected image size")
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):mime="image/png"
    elif raw.startswith(b"\xff\xd8\xff"):mime="image/jpeg"
    else:raise ImageGenerationError("unexpected image format")
    return raw,mime

def generate(prompt,*,tier="standard",requester_approved=False,transport=requests.post):
    if not requester_approved:raise ImageGenerationError("human media/usage approval required")
    if tier not in MODELS:raise ImageGenerationError("unsupported model")
    if not isinstance(prompt,str) or not 4<=len(prompt)<=2500 or re.search(
         r"(?i)(?:api[_-]?key|bearer|password)\s*[:=]\s*\S+",prompt):
        raise ImageGenerationError("invalid or sensitive prompt")
    key=os.getenv("GEMINI_API_KEY","")
    if not key:raise ImageGenerationError("GEMINI_API_KEY not configured")
    # No silent model fallback or automatic retry that might duplicate charges.
    try:
        result=transport("https://generativelanguage.googleapis.com/v1beta/interactions",
            headers={"x-goog-api-key":key,"Content-Type":"application/json"},
            json={"model":MODELS[tier],"input":[{"type":"text","text":prompt}]},timeout=120)
        if result.status_code!=200:raise ImageGenerationError("Gemini image HTTP "+str(result.status_code))
        raw,mime=image_from_response(result.json())
        return {"model":MODELS[tier],"mime":mime,"bytes":raw}
    except requests.RequestException as exc:
        raise ImageGenerationError(type(exc).__name__) from None
