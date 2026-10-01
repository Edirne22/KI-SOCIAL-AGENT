import base64
import os
import unittest
from unittest.mock import patch
from scripts.ai_central_gemini_image import generate,image_from_response,ImageGenerationError

PNG=b"\\x89PNG\\r\\n\\x1a\\n"+b"x"*120
class Response:
    status_code=200
    def json(self):return {"interaction":{"output_image":{"data":base64.b64encode(PNG).decode()}}}
class Tests(unittest.TestCase):
    def test_no_unapproved_costs(self):
        with self.assertRaises(ImageGenerationError):
            generate("Create a sample",requester_approved=False)
    def test_real_image_output_checks(self):
        raw,mime=image_from_response(Response().json())
        self.assertEqual(mime,"image/png")
        self.assertEqual(raw,PNG)
        with self.assertRaises(ImageGenerationError):
            image_from_response({"interaction":{"output_image":{"data":"a"}}})
    def test_existing_key_and_explicit_model(self):
        log=[]
        def fake(url,**kwargs):
            log.append((url,kwargs))
            return Response()
        with patch.dict(os.environ,{"GEMINI_API_KEY":"mock-secret"}):
            out=generate("Create a sample",requester_approved=True,tier="standard",transport=fake)
        self.assertEqual(out["model"],"gemini-3.1-flash-image")
        self.assertEqual(log[0][1]["json"]["model"],out["model"])
        self.assertEqual(log[0][1]["headers"]["x-goog-api-key"],"mock-secret")
    def test_no_hidden_model_fallback(self):
        class Reject:status_code=403
        with patch.dict(os.environ,{"GEMINI_API_KEY":"mock-secret"}):
            with self.assertRaisesRegex(ImageGenerationError,"403"):
                generate("Create sample",tier="pro",requester_approved=True,transport=lambda *a,**kw:Reject())
if __name__=="__main__":unittest.main()
