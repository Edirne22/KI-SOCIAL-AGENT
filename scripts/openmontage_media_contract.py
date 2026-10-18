"""B70: Fail-closed contract for licensed scene media before renderer handoff.

This module validates metadata only. It does not download remote media or grant
publishing rights. A later adapter must resolve and probe approved assets.
"""
from __future__ import annotations

from urllib.parse import urlsplit


class MediaContractError(RuntimeError):
    """An actionable media handoff failure."""


def validate_scene_media(storyboard: dict, media_manifest: dict) -> list[dict]:
    scenes = storyboard.get("scenes", [])
    items = media_manifest.get("manifest", [])
    if not isinstance(scenes, list) or not scenes or not isinstance(items, list):
        raise MediaContractError("MEDIA_RESEARCH_INCOMPLETE: empty scene or media list")
    if len(scenes) != len(items):
        raise MediaContractError("MEDIA_RESEARCH_INCOMPLETE: scene/media count mismatch")
    if media_manifest.get("all_rights_verified") is not True:
        raise MediaContractError("MEDIA_RESEARCH_INCOMPLETE: rights verification missing")

    accepted = []
    for index, (scene, item) in enumerate(zip(scenes, items), start=1):
        if not isinstance(scene, dict) or not isinstance(item, dict):
            raise MediaContractError(f"MEDIA_RESEARCH_INCOMPLETE: malformed scene {index}")
        if scene.get("scene_number") != item.get("scene_number"):
            raise MediaContractError(f"MEDIA_RESEARCH_INCOMPLETE: scene identity mismatch {index}")
        url = item.get("media_url")
        license_name = str(item.get("media_license", "")).casefold().strip()
        if (item.get("external_media_accepted") is not True
                or item.get("rights_verified") is not True
                or license_name not in {"owned_content", "cc0", "public_domain", "explicit_permission_granted"}
                or not isinstance(url, str) or not url.strip()):
            raise MediaContractError(f"MEDIA_RESEARCH_INCOMPLETE: licensed media missing for scene {index}")
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise MediaContractError(f"MEDIA_RESEARCH_INCOMPLETE: unsafe media URL in scene {index}")
        accepted.append({"scene_number": index, "media_url": url,
                         "media_license": license_name, "media_source": item.get("media_source", "")})
    return accepted


def validate_local_scene_media(storyboard: dict, media_manifest: dict) -> list[dict]:
    """Local handoff; remote metadata contract remains unchanged."""
    scenes = storyboard.get('scenes', [])
    items = media_manifest.get('manifest', [])
    if (not isinstance(scenes, list) or not scenes or not isinstance(items, list)
            or len(scenes) != len(items) or media_manifest.get('all_rights_verified') is not True):
        raise MediaContractError('LOCAL_MEDIA_INVALID: scene/media count or rights mismatch')
    for index, (scene, item) in enumerate(zip(scenes, items), 1):
        if (not isinstance(scene, dict) or not isinstance(item, dict)
                or scene.get('scene_number') != index or item.get('scene_number') != index
                or item.get('rights_verified') is not True
                or item.get('media_license') not in
                {'owned_content', 'cc0', 'public_domain', 'explicit_permission_granted'}
                or not item.get('local_path')):
            raise MediaContractError(f'LOCAL_MEDIA_INVALID: licensed local media missing for scene {index}')
    return items
