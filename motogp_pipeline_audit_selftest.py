"""Offline tests for diagnostic audit. No network, LLM, Telegram, memory or publisher."""
from pathlib import Path
import tempfile,os
import motogp_pipeline_audit as a

def check(v,msg):
 if not v:raise AssertionError(msg)

def row(pos,name=None,**kw):return {'position':pos,'rider':name or f'Rider {pos}','series':'MotoGP',**kw}

def main():
 with tempfile.TemporaryDirectory() as d:
  os.chdir(d);a.ART=Path('artifacts');a.AUDIT=a.ART/'motogp-pipeline-audit.jsonl';a.SUMMARY=a.ART/'motogp-stage-summary.json';a.REJECTIONS=a.ART/'motogp-rejections.jsonl';a.TOP10=a.ART/'motogp-top10.json'
  roster=[f'Rider {i}' for i in range(1,23)]
  # 270 raw records, including 22 valid riders. Duplicates must not prevent deterministic Top 10.
  rows=[row(i,f'Rider {i}') for i in range(1,23)]
  rows += [row(((i-22)%22)+1,f'Rider {((i-22)%22)+1}') for i in range(22,270)]
  r=a.deterministic_top10(rows,'test-270',active_roster=roster);check(r['top10_count']==10,'270/22 must yield 10');check([x['position'] for x in r['top10']]==list(range(1,11)),'positions 1..10 expected')
  x=a.deterministic_top10([row(i,team=None,time=None,points=None) for i in range(1,11)],'test-optional');check(x['top10_count']==10,'optional fields must not remove riders');check(x['top10'][0]['team'] is None and x['top10'][0]['time'] is None and x['top10'][0]['points'] is None,'optional nulls preserved')
  x=a.deterministic_top10([row(i) for i in range(1,9)],'test-eight');check(x['top10_count']==8 and x['warning'],'8 rows must warn')
  x=a.deterministic_top10([row(1),row(1)],'test-duplicate');check(x['top10_count']==1,'duplicate must merge')
  x=a.deterministic_top10([row(1,'Wildcard')],'test-roster',active_roster=roster);check(x['top10_count']==1 and 'NOT_IN_ACTIVE_ROSTER' in x['top10'][0]['warnings'],'roster miss is warning, not deletion')
  x=a.deterministic_top10([row(1),{'position':2,'rider':'Moto2 Rider','series':'Moto2'}],'test-class');check(x['top10_count']==1,'wrong class excluded')
  x=a.deterministic_top10([{'position':1,'rider':'','series':'MotoGP'}],'test-rider');check(x['top10_count']==0,'missing rider excluded')
  x=a.deterministic_top10([row('abc')],'test-position');check(x['top10_count']==0,'invalid position excluded')
  # Rotation/QM are intentionally absent from this module: raw Top10 cannot be mutated by them.
  print('MOTOGP PIPELINE AUDIT SELFTEST: PASS')
if __name__=='__main__':main()
