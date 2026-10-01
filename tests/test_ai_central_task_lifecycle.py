import unittest
from scripts.ai_central_task_lifecycle import build_status,persist
class Fake:
  def __init__(self):self.sent=[]
  def put_object(self,**kw):self.sent.append(kw)
class StatusTests(unittest.TestCase):
  def test_safe_status_and_stable_r2_location(self):
    d=build_status("a"*24,"123456","PENDING_REVIEW")
    self.assertEqual(d["report_expected"],True)
    c=Fake()
    key=persist(c,"private",d)
    self.assertEqual(key,"ai-central/v1/tasks/"+"a"*24+"/status.json")
    self.assertEqual(c.sent[0]["Bucket"],"private")
  def test_invalid_status_or_task_id(self):
    for task,run,status in [("../danger","100","RUNNING"),("b"*24,"not-id","RUNNING"),("b"*24,"100","DONE")]:
      with self.subTest(task=task,status=status),self.assertRaises(ValueError):
        build_status(task,run,status)
if __name__=="__main__":unittest.main()
