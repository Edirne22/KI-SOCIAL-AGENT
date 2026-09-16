import unittest
import tempfile
import os
from pathlib import Path
from PIL import Image

from instagram_publish import process_image_for_instagram

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

if __name__ == "__main__":
    unittest.main()
