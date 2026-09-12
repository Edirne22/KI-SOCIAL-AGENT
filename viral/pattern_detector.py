"""Kombiniert externe und interne Muster zu sicheren Viral-Learnings."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from .analyze_external import analyze as external
from .analyze_internal import analyze as internal
OUT=Path("memory/VIRAL_PATTERNS.md")
def main():
 report=f"# Viral-Muster\n\nStand: {datetime.now():%Y-%m-%d %H:%M}\n\n{external()}\n{internal()}\n## Arbeitsregel\n- Türkische Racer zuerst, Hooks testen, keine fremden Beiträge kopieren.\n"
 OUT.write_text(report,encoding="utf-8")
 for path,title in ((Path("memory/HOOKS_THAT_WORK.md"),"# Hooks, die wirken"),(Path("memory/LESSONS_LEARNED.md"),"# Lessons Learned")):
  old=path.read_text(encoding="utf-8") if path.exists() else title+"\n";path.write_text(old.rstrip()+f"\n\n- {datetime.now():%Y-%m-%d}: Viral-Muster aktualisiert; erst mit belastbaren Daten verfeinern.\n",encoding="utf-8")
if __name__=="__main__":main()
