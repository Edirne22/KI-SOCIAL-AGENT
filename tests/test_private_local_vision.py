import io
import os
from pathlib import Path
import unittest
from content_factory_local_vision import CANDIDATES, classify_scores, LocalSceneVision

class VisionContractTests(unittest.TestCase):
    def test_confident_scene_and_uncertainty(self):
        scores=[0.01]*len(CANDIDATES); scores[0]=0.93
        self.assertEqual(classify_scores(scores)["asset_role"],"trampoline_action")
        self.assertTrue(classify_scores(scores)["accepted"])
        self.assertFalse(classify_scores([1/len(CANDIDATES)]*len(CANDIDATES))["accepted"])
        scores=[0.01]*len(CANDIDATES); scores[-1]=0.93
        self.assertFalse(classify_scores(scores)["accepted"])
        with self.assertRaisesRegex(RuntimeError,"INVALID_SCORES"):
            classify_scores([float('nan')]*len(CANDIDATES))

    @unittest.skipUnless(os.environ.get("PRIVATE_VISION_TEST_MODEL"),"real weights required")
    def test_actual_offline_weights_on_synthetic_images(self):
        from PIL import Image, ImageDraw
        from unittest.mock import patch
        with patch("socket.socket.connect",side_effect=AssertionError("INFERENCE_NETWORK_FORBIDDEN")):
            model=LocalSceneVision(os.environ["PRIVATE_VISION_TEST_MODEL"])
            blank=Image.new("RGB",(512,512),"black")
            cake=Image.new("RGB",(512,512),"white")
            d=ImageDraw.Draw(cake)
            d.rectangle((90,270,420,420),fill="pink",outline="brown",width=6)
            d.ellipse((90,240,420,300),fill="ivory",outline="brown",width=4)
            for x in (140,195,250,305,360):
                d.rectangle((x,185,x+12,270),fill="blue")
                d.ellipse((x-3,157,x+15,186),fill="orange")
            verdicts=[]
            for image in (blank,cake):
                buf=io.BytesIO();image.save(buf,format="JPEG")
                verdicts.append(model(buf.getvalue()))
            self.assertFalse(verdicts[0]["accepted"])
            self.assertEqual(verdicts[1]["asset_role"],"birthday_cake")
            self.assertTrue(verdicts[1]["accepted"])
            self.assertNotEqual(verdicts[0]["scores"],verdicts[1]["scores"])
