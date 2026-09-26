"""Regression: technical semantic degradation must reach final Chief-QM, factual FAIL must not."""
import motogp_content_agency_v2 as agency

def base(status):
 return {"title":"Brad Binder joins BMW","url":"https://example.test/binder","caption":"Brad Binder wechselt zu BMW.","semantic_qm":status,"racing_qm":"PASS"}

def run():
 old_media,old_chief=agency.prepare_media,agency.chief_review
 calls=[]
 try:
  agency.prepare_media=lambda x,i:(calls.append(("media",x["semantic_qm"])) or "assets/images/test.jpg")
  agency.chief_review=lambda *args,**kwargs:(calls.append(("chief",args[1]["semantic_qm"])) or (True,[]))
  assert agency.finish_item(base("DEGRADED-PASS"),1) is True
  assert ("media","DEGRADED-PASS") in calls and ("chief","DEGRADED-PASS") in calls
  calls.clear()
  assert agency.finish_item(base("FAIL"),1) is False
  assert calls==[],calls
 finally:
  agency.prepare_media,agency.chief_review=old_media,old_chief
 print("DEGRADED PASS FINALIZATION REGRESSION: PASS")

if __name__=="__main__":run()
