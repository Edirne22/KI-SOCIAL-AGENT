"""Koordiniert die drei unabhängigen Inspiration-Adapter parallel."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime
from pathlib import Path
from . import apify_agent,brightdata_agent,crawlbase_agent
from .report_builder import build
from telegram_bot import send_message
MEM=Path("memory")
def main():
 jobs={"Apify":apify_agent.run,"Bright Data":brightdata_agent.run,"Crawlbase":crawlbase_agent.run}; reports={}
 with ThreadPoolExecutor(max_workers=3) as pool:
  future={pool.submit(fn):name for name,fn in jobs.items()}
  for task in as_completed(future):
   name=future[task]
   try: reports[name]=task.result()
   except Exception as e: reports[name]=f"# {name}\nFehler: {type(e).__name__}\n"
 report=build(reports); (MEM/"INSPIRATION_IDEAS.md").write_text(report,encoding="utf-8")
 week=datetime.now().strftime("%Y-W%W"); archive=MEM/"INSPIRATION_ARCHIVE";archive.mkdir(parents=True,exist_ok=True);(archive/f"{week}.md").write_text(report,encoding="utf-8")
 log=MEM/"INSPIRATION_LOG.md"; old=log.read_text(encoding="utf-8") if log.exists() else "# Inspiration-Log\n";log.write_text(old+f"\n- {datetime.now():%Y-%m-%d %H:%M}: "+", ".join(reports)+"\n",encoding="utf-8")
 try: send_message("Inspiration-Analyse fertig. Die Top-Ideen liegen in memory/INSPIRATION_IDEAS.md.")
 except RuntimeError as e: print(f"Telegram übersprungen: {e}")
if __name__=="__main__": main()
