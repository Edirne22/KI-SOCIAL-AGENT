"""Resolve explicitly licensed HTTPS scene assets into the existing local renderer.

This adapter does not discover licenses, scrape platforms or infer permission.
"""
from __future__ import annotations

import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlsplit
import requests

LICENSES = {"owned_content", "cc0", "public_domain", "explicit_permission_granted"}
SUFFIXES = {".jpg", ".jpeg", ".png", ".mp4"}
MAX_BYTES = 100 * 1024 * 1024


def _public_host(host):
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        return bool(addresses) and all(
            ipaddress.ip_address(row[4][0]).is_global for row in addresses)
    except (OSError, ValueError):
        return False


def download_licensed_scenes(items, root: Path, *, session=None):
    """Fetch one already rights-verified direct media URL per scene.

    Redirects and private-address targets are rejected. Renderer validates
    actual codec, size, dimensions and decoding after this intake.
    """
    if not isinstance(items, list) or not 1 <= len(items) <= 8:
        raise ValueError("MEDIA_INTAKE_INVALID: expected 1-8 scenes")
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    client = session or requests
    selected = []
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict) or item.get("scene_number") != index:
            raise ValueError("MEDIA_INTAKE_INVALID: scene order mismatch")
        if (item.get("rights_verified") is not True
                or item.get("external_media_accepted") is not True
                or item.get("media_license") not in LICENSES):
            raise ValueError("MEDIA_INTAKE_INVALID: explicit media rights required")
        url = item.get("media_url", "")
        parsed = urlsplit(url)
        suffix = Path(parsed.path).suffix.lower()
        if (parsed.scheme != "https" or not parsed.hostname or parsed.port not in (None, 443)
                or parsed.username or parsed.password or suffix not in SUFFIXES
                or not _public_host(parsed.hostname)):
            raise ValueError("MEDIA_INTAKE_INVALID: unsafe direct media URL")
        target = root / f"scene-{index}{suffix}"
        try:
            with client.get(url, stream=True, timeout=(8, 25), allow_redirects=False) as response:
                response.raise_for_status()
                if 300 <= response.status_code < 400:
                    raise ValueError("redirect forbidden")
                size = 0
                with target.open("wb") as output:
                    for chunk in response.iter_content(chunk_size=65536):
                        size += len(chunk)
                        if size > MAX_BYTES:
                            raise ValueError("media exceeds 100 MiB")
                        output.write(chunk)
                if size == 0:
                    raise ValueError("empty media")
        except Exception:
            target.unlink(missing_ok=True)
            raise
        selected.append({"scene_number": index, "local_path": target.name,
                         "media_license": item["media_license"], "rights_verified": True})
    return {"scenes": selected, "all_rights_verified": True}
