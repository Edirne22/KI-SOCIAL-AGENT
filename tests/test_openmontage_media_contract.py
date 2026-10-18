"""Regression tests for B70 media contract."""
import unittest

from scripts.openmontage_media_contract import MediaContractError, validate_scene_media


def payload(url="https://example.org/owned.mp4", licensed=True):
    storyboard = {"scenes": [{"scene_number": 1, "title": "Quickshifter"}]}
    manifest = {"all_rights_verified": True, "manifest": [{
        "scene_number": 1, "media_url": url, "media_license": "owned_content",
        "media_source": "owner", "rights_verified": True,
        "external_media_accepted": licensed,
    }]}
    return storyboard, manifest


class MediaContractTests(unittest.TestCase):
    def test_valid_owned_media(self):
        self.assertEqual(len(validate_scene_media(*payload())), 1)

    def test_missing_media_rejected(self):
        with self.assertRaisesRegex(MediaContractError, "MEDIA_RESEARCH_INCOMPLETE"):
            validate_scene_media(*payload(url=""))

    def test_unlicensed_media_rejected(self):
        with self.assertRaisesRegex(MediaContractError, "MEDIA_RESEARCH_INCOMPLETE"):
            validate_scene_media(*payload(licensed=False))

    def test_unsafe_scheme_rejected(self):
        with self.assertRaisesRegex(MediaContractError, "MEDIA_RESEARCH_INCOMPLETE"):
            validate_scene_media(*payload(url="file:///etc/passwd"))

    def test_scene_mismatch_rejected(self):
        storyboard, manifest = payload()
        manifest["manifest"][0]["scene_number"] = 2
        with self.assertRaisesRegex(MediaContractError, "MEDIA_RESEARCH_INCOMPLETE"):
            validate_scene_media(storyboard, manifest)


if __name__ == "__main__":
    unittest.main()
