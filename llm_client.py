"""Einheitlicher Client fuer konfigurierbare Text-, Bild- und Video-Aufgaben."""
from __future__ import annotations
import argparse,re
from pathlib import Path
from typing import Sequence
import requests
from router import get_api_key,get_provider_config,get_provider_for_task,get_task_config
ROOT=Path(__file__).resolve().parent
PRO_STANDARD=ROOT/'config'/'PROFESSIONAL_AGENT_STANDARD.md';HUMAN_STANDARD=ROOT/'config'/'HUMAN_WRITING_PROTOCOL.md'
SECRET_PATTERNS=((re.compile(r"AIza[0-9A-Za-z_-]{35}"),"[ENTFERNT]"),(re.compile(r"AQ\.[A-Za-z0-9_-]{40,}"),"[ENTFERNT]"),(re.compile(r"sk-[A-Za-z0-9_-]{20,}"),"[ENTFERNT]"),(re.compile(r"\b[A-Za-z0-9_-]{50,}\b"),"[ENTFERNT]"))
def redact_secrets(value):
 for p,r in SECRET_PATTERNS:value=p.sub(r,value)
 return value
def _read_standard(path):
 try:return path.read_text(encoding='utf-8').strip()
 except FileNotFoundError:return ''
def global_professional_context():return '\n\n'.join(x for x in (_read_standard(PRO_STANDARD),_read_standard(HUMAN_STANDARD)) if x)
def _with_global_standard(prompt):
 ctx=global_professional_context();return f"GLOBALER VERBINDLICHER PROFESSIONAL-/SCHREIBSTANDARD:\n{ctx}\n\nAUFGABE:\n{prompt}" if ctx else prompt
def load_agent(agent_file):
 name=agent_file.strip();name=name[:-3] if name.endswith('.md') else name
 if not name or '/' in name or '\\' in name or name in {'.','..'}:raise ValueError('Agenten-Datei muss als einfacher Name ohne Pfad angegeben werden.')
 agents=ROOT/'agents';path=(agents/f'{name}.md').resolve()
 if path.parent!=agents.resolve():raise ValueError('Ungueltiger Agenten-Dateiname.')
 try:return path.read_text(encoding='utf-8').strip()
 except FileNotFoundError as e:raise FileNotFoundError(f'Agenten-Datei nicht gefunden: {path.name}') from e
def get_agent_context(agent_names:Sequence[str]):
 contexts=[f"--- GLOBALER STANDARD ---\n{global_professional_context()}"]
 for agent_name in agent_names:
  n=agent_name[:-3] if agent_name.endswith('.md') else agent_name;contexts.append(f'--- Agent: {n} ---\n{load_agent(n)}')
 return '\n\n'.join(contexts)
def _request_json(method,url,headers,payload,timeout):
 r=requests.request(method,url,headers=headers,json=payload,timeout=timeout)
 if not r.ok:raise RuntimeError(f"Provider-Anfrage fehlgeschlagen (HTTP {r.status_code}): {redact_secrets(r.text[:500])}")
 return r.json()
def _generate_gemini(prompt,provider,key):
 headers={'Content-Type':'application/json','X-goog-api-key':key};payload={'contents':[{'parts':[{'text':prompt}]}]};errors=[]
 for model in provider['text_models']:
  try:
   data=_request_json('POST',f"{provider['base_url']}/models/{model}:generateContent",headers,payload,provider['timeout_seconds']);return redact_secrets(data['candidates'][0]['content']['parts'][0]['text']).strip()
  except (KeyError,IndexError,TypeError) as e:errors.append(f'{model}: unvollstaendige Antwort ({e})')
  except RuntimeError as e:errors.append(f'{model}: {e}')
 raise RuntimeError('Kein Gemini-Modell konnte die Aufgabe ausfuehren. '+' | '.join(errors))
def _generate_agnes_text(prompt,provider,key):
 data=_request_json('POST',f"{provider['base_url']}/chat/completions",{'Authorization':f'Bearer {key}','Content-Type':'application/json'},{'model':provider['chat_model'],'messages':[{'role':'user','content':prompt}],'stream':False},provider['timeout_seconds']);return redact_secrets(data['choices'][0]['message']['content']).strip()
def _generate_agnes_image(prompt,provider,key):return _request_json('POST',f"{provider['base_url']}/images/generations",{'Authorization':f'Bearer {key}','Content-Type':'application/json'},{'model':provider['image_model'],'prompt':prompt,'size':'1024x1024','n':1},provider['timeout_seconds'])
def _start_agnes_video(prompt,provider,key):return _request_json('POST',f"{provider['base_url']}/videos",{'Authorization':f'Bearer {key}','Content-Type':'application/json'},{'model':provider['video_model'],'prompt':prompt,'duration':5,'size':'720x1280'},provider['timeout_seconds'])
def generate(task_name,prompt):
 task=get_task_config(task_name);provider_name=get_provider_for_task(task_name);provider=get_provider_config(provider_name);key=get_api_key(provider_name)
 if task['response_type']=='text':prompt=_with_global_standard(prompt)
 if provider_name=='gemini':
  if task['response_type']!='text':raise ValueError(f"Gemini unterstuetzt im Router keine Aufgabe vom Typ {task['response_type']}.")
  return _generate_gemini(prompt,provider,key)
 if provider_name=='agnes':
  if task['response_type']=='text':return _generate_agnes_text(prompt,provider,key)
  if task['response_type']=='image':return _generate_agnes_image(prompt,provider,key)
  if task['response_type']=='video':return _start_agnes_video(prompt,provider,key)
 raise ValueError(f"Keine Client-Implementierung fuer Provider '{provider_name}'.")
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--task',default='content_ideas');p.add_argument('--prompt',default='Nenne eine kurze Motorrad-Content-Idee.');a=p.parse_args();r=generate(a.task,a.prompt);print(r if isinstance(r,str) else redact_secrets(str(r)))
