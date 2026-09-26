"""Regression for Racing run duplicate protection.

Manual workflow_dispatch runs are intentional E2E executions and must not be
suppressed by a recent different run. Scheduled daily batches remain protected.
"""
import json, os, tempfile
from datetime import datetime, timezone
from pathlib import Path
import racing_run_controller as rc

NOW=datetime(2026,9,26,10,30,tzinfo=timezone.utc)

def reset(path):
 rc.STATE=path
 path.write_text(json.dumps({"version":1,"runs":{},"last_notification_at":0,"last_notification_fingerprint":""}),encoding="utf-8")

def run():
 old=dict(os.environ)
 try:
  with tempfile.TemporaryDirectory() as td:
   state=Path(td)/"state.json";reset(state)
   os.environ["GITHUB_EVENT_NAME"]="workflow_dispatch"
   os.environ["GITHUB_RUN_ID"]="100"
   ok,bid,reason=rc.begin(NOW);assert ok,(bid,reason)
   rc.transition(bid,"READY_FOR_APPROVAL")
   os.environ["GITHUB_RUN_ID"]="101"
   ok,bid2,reason=rc.begin(NOW);assert ok,(bid2,reason)
   assert bid2!=bid

   reset(state)
   os.environ["GITHUB_EVENT_NAME"]="schedule"
   os.environ["GITHUB_RUN_ID"]="200"
   ok,daily,reason=rc.begin(NOW);assert ok,(daily,reason)
   rc.transition(daily,"READY_FOR_APPROVAL")
   os.environ["GITHUB_RUN_ID"]="201"
   ok,daily2,reason=rc.begin(NOW);assert not ok,(daily2,reason)
   assert daily2==daily and reason=="duplicate batch"
 finally:
  os.environ.clear();os.environ.update(old)
 print("MANUAL RACING RERUN REGRESSION: PASS")

if __name__=="__main__":run()
