import hashlib,hmac,os,unittest
from unittest.mock import patch
import meta_engagement_webhook as mw
class Tests(unittest.TestCase):
 def test_signature(self):
  raw=b'{"object":"page"}';secret="s";sig="sha256="+hmac.new(secret.encode(),raw,hashlib.sha256).hexdigest()
  with patch.dict(os.environ,{"META_APP_SECRET":secret}):self.assertTrue(mw.valid_signature(raw,sig));self.assertFalse(mw.valid_signature(raw,sig+"x"))
 def test_instagram_comment(self):
  p={"object":"instagram","entry":[{"time":1,"changes":[{"field":"comments","value":{"id":"c1","text":"Hi","from":{"username":"u"},"media":{"id":"m"}}}]}]}
  self.assertEqual(mw.normalize(p)[0]["platform"],"instagram")
 def test_facebook_comment(self):
  p={"object":"page","entry":[{"time":1,"changes":[{"field":"feed","value":{"item":"comment","comment_id":"c","post_id":"p","message":"Hi","from":{"name":"N"}}}]}]}
  self.assertEqual(mw.normalize(p)[0]["platform"],"facebook")
if __name__=="__main__":unittest.main()
