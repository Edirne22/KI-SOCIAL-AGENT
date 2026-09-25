import unittest
import tempfile
import os
from io import BytesIO
from unittest.mock import MagicMock, patch
from pathlib import Path
from PIL import Image

from instagram_publish import process_image_for_instagram, extract_og_image_url, download_og_image_for_instagram, generate_buelent_caption

class TestInstagramImageResize(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def test_portrait_story_1080x1920_crops_to_4_5(self):
        # 1080x1920 (ratio 0.5625 -> crops to 4:5 i.e. 1080x1350)
        img_path = Path("assets/test/sample_story.jpg")
        img_path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (1080, 1920), color="blue")
        img.save(img_path, "JPEG")
        self.addCleanup(lambda: img_path.unlink(missing_ok=True))

        res_path_str = process_image_for_instagram(img_path.as_posix())
        res_path = Path(res_path_str)
        self.addCleanup(lambda: res_path.unlink(missing_ok=True))

        self.assertTrue(res_path.name.endswith("-ig-resized.jpg"))
        with Image.open(res_path) as res_img:
            w, h = res_img.size
            self.assertEqual((w, h), (1080, 1350))
            ratio = w / h
            self.assertAlmostEqual(ratio, 0.8, delta=0.02)

    def test_compliant_1080x1350_remains_unchanged(self):
        # 1080x1350 (ratio 0.8 -> compliant)
        img_path = Path("assets/test/sample_compliant.jpg")
        img_path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (1080, 1350), color="green")
        img.save(img_path, "JPEG")
        self.addCleanup(lambda: img_path.unlink(missing_ok=True))

        res_path_str = process_image_for_instagram(img_path.as_posix())
        self.assertEqual(res_path_str, img_path.as_posix())

    def test_landscape_1920x1080_crops_to_1_91(self):
        # 1920x1080 (ratio 1.777 -> closest target is 1.91:1 i.e. 1920x1005)
        img_path = Path("assets/test/sample_landscape.jpg")
        img_path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (1920, 1080), color="red")
        img.save(img_path, "JPEG")
        self.addCleanup(lambda: img_path.unlink(missing_ok=True))

        res_path_str = process_image_for_instagram(img_path.as_posix())
        res_path = Path(res_path_str)
        self.addCleanup(lambda: res_path.unlink(missing_ok=True))

        self.assertTrue(res_path.name.endswith("-ig-resized.jpg"))
        with Image.open(res_path) as res_img:
            w, h = res_img.size
            ratio = w / h
            self.assertAlmostEqual(ratio, 1.91, delta=0.02)


class TestInstagramOgImage(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    @patch("instagram_publish.requests.get")
    def test_og_image_present_is_used_and_padded_1080x1350(self, mock_get):
        html = MagicMock()
        html.text = '<html><head><meta property="og:image" content="/media/race.jpg"></head></html>'
        html.raise_for_status.return_value = None

        source = Image.new("RGB", (1600, 900), color="red")
        payload = BytesIO()
        source.save(payload, "JPEG")
        image_response = MagicMock()
        image_response.content = payload.getvalue()
        image_response.raise_for_status.return_value = None
        mock_get.side_effect = [html, image_response]

        target = Path(self.temp_dir.name) / "og.jpg"
        result = download_og_image_for_instagram("https://example.com/story", target)
        self.assertEqual(result, target.as_posix())
        with Image.open(target) as converted:
            self.assertEqual(converted.size, (1080, 1350))

    @patch("instagram_publish.requests.get")
    def test_og_image_missing_returns_none_for_agnes_fallback(self, mock_get):
        html = MagicMock()
        html.text = "<html><head><title>No OG image</title></head></html>"
        html.raise_for_status.return_value = None
        mock_get.return_value = html
        self.assertIsNone(extract_og_image_url("https://example.com/story"))

    @patch("llm_router.quick_chat")
    def test_buelent_caption_uses_llm_result(self, mock_quick_chat):
        mock_quick_chat.return_value = "Bülent-Stil Caption"
        self.assertEqual(generate_buelent_caption("Facebook Caption"), "Bülent-Stil Caption")
        prompt = mock_quick_chat.call_args.args[0]
        self.assertIn("KEINE neue Tatsacheninformation", prompt)
        self.assertIn("Facebook Caption", prompt)

    @patch("llm_router.quick_chat")
    def test_caption_failure_falls_back_to_facebook_caption(self, mock_quick_chat):
        mock_quick_chat.side_effect = RuntimeError("provider down")
        original = "Facebook Caption mit Quelle: https://example.com"
        self.assertEqual(generate_buelent_caption(original), original)

if __name__ == "__main__":
    unittest.main()
