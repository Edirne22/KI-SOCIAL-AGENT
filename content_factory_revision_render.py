"""Bounded local FFmpeg edits after canonical ACK; no publisher or model calls."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from uuid import uuid4
from content_factory_core import JobStatus
from content_factory_dashboard_preview import INDEX_PREFIX, STATE_PREFIX, MAX_DASHBOARD_VIDEO_BYTES
from content_factory_golden_tablet import FinalQM, QMCheck
from content_factory_golden_media import present_verified_golden_tablet
from content_factory_revision_intake import derive_canonical_edit_request, _existing, _uuid
from content_factory_dashboard_review_ack import _read_state
from content_factory_r2_job_repository import R2JobRepository
from media_storage import R2Storage

class RevisionRenderError(RuntimeError):
    pass

def plan_edit(text):
    text=text.strip().lower().rstrip('.!').strip()
    if text in ('ton entfernen','ohne ton','stummschalten','mute','remove audio'):
        return {'operation':'mute'}
    if text in ('neu rendern','erneut rendern','re-render','rerender'):
        return {'operation':'rerender'}
    m=re.fullmatch(r'(?:bitte )?auf ([1-9][0-9]?) sekunden kürzen',text)
    return {'operation':'trim','seconds':int(m[1])} if m else None

def probe(path):
    result=subprocess.run(['ffprobe','-v','error','-protocol_whitelist','file,pipe',
        '-show_entries','format=duration,size:stream=codec_type,codec_name,width,height',
        '-of','json',str(path)],capture_output=True,text=True,timeout=20)
    try:
        doc=json.loads(result.stdout)
        duration=float(doc['format']['duration'])
        videos=[s for s in doc['streams'] if s['codec_type']=='video']
        if (result.returncode or not math.isfinite(duration) or not 0<duration<=120 or
            len(videos)!=1 or not 0<int(doc['format']['size'])<=MAX_DASHBOARD_VIDEO_BYTES or
            not 0<videos[0]['width']<=4096 or not 0<videos[0]['height']<=4096):
            raise ValueError()
        return duration,doc['streams']
    except (ValueError,KeyError,TypeError) as exc:
        raise RevisionRenderError('media outside bounded MP4 contract') from exc

def render(source,plan,storage,workdir,provenance):
    if source.mime_type!='video/mp4' or not 0<source.size_bytes<=MAX_DASHBOARD_VIDEO_BYTES:
        raise RevisionRenderError('only bounded private MP4 supported')
    src=storage.resolve_local(source)
    duration,streams=probe(src)
    target=plan.get('seconds',duration)
    if target>duration+.1:
        raise RevisionRenderError('requested trim exceeds original duration')
    out=Path(workdir)/'revision.mp4'
    out.parent.mkdir(parents=True,exist_ok=True)
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y',
         '-protocol_whitelist','file,pipe','-i',str(src),'-map','0:v:0']
    if plan['operation']=='mute':
        cmd+=['-an']
    else:
        cmd+=['-map','0:a:0?','-c:a','aac','-b:a','96k']
    cmd+=['-map_metadata','-1','-c:v','libx264','-threads','2',
          '-preset','veryfast','-crf','23','-pix_fmt','yuv420p',
          '-vf','scale=trunc(iw/2)*2:trunc(ih/2)*2','-t',str(target),
          '-movflags','+faststart',str(out)]
    result=subprocess.run(cmd,capture_output=True,timeout=180)
    if result.returncode:
        raise RevisionRenderError('FFmpeg revision failed')
    measured,produced=probe(out)
    if abs(measured-target)>.5:
        raise RevisionRenderError('render duration verification failed')
    audio=lambda ss:any(s['codec_type']=='audio' for s in ss)
    if plan['operation']=='mute' and audio(produced):
        raise RevisionRenderError('mute verification failed')
    if plan['operation']!='mute' and audio(streams)!=audio(produced):
        raise RevisionRenderError('audio preservation failed')
    ref=storage.put_file(out,provenance=provenance,mime_type='video/mp4')
    restored=storage.resolve_local(ref)
    if hashlib.sha256(restored.read_bytes()).hexdigest()!=ref.sha256:
        raise RevisionRenderError('output integrity failed')
    probe(restored)
    return ref

def _deliver(job_id,request_id,storage,repository):
    record=repository.get_job(job_id)
    job=record.job
    run=job.metadata.get('revision_render')
    if (job.status!=JobStatus.READY_FOR_HUMAN or not isinstance(run,dict) or
        run.get('request_id')!=request_id or run.get('revision')!=job.revision or
        run.get('state')!='READY_FOR_HUMAN' or len(job.media)!=1 or
        job.human_approved_revision is not None or job.publish_handoff_key is not None):
        raise RevisionRenderError('no exact completed revision to deliver')
    if (_existing(storage,run['ticket_key'])!=run['ticket'] or
        run['ticket'].get('request_id')!=request_id or run['ticket'].get('job_id')!=job_id or
        run['ticket'].get('revision')!=job.revision):
        raise RevisionRenderError('completed revision lost its immutable edit authority')
    preview=run['preview']
    if (preview['manifest']!=job.approval_manifest() or
        preview['media']['sha256']!=job.media[0].sha256 or
        preview['media']['media_id']!=job.media[0].media_id or
        preview['job_id']!=job_id or preview['revision']!=job.revision):
        raise RevisionRenderError('completed preview no longer matches canonical job')
    storage.resolve_local(job.media[0])
    state,etag=_read_state(job_id,storage)
    pointer={'schema':'FACTORY-PREVIEW-STATE-V1','job_id':job_id,
        'preview_id':preview['preview_id'],'revision':job.revision,
        'manifest':preview['manifest'],'state':'READY_FOR_HUMAN','review':run['ack_review']}
    if state==pointer:
        return 'READY_FOR_HUMAN'
    if state!=run['ack_state']:
        raise RevisionRenderError('preview state changed; cannot overwrite human decision')
    key=INDEX_PREFIX+preview['preview_id']+'.json'
    existing=_existing(storage,key)
    if existing is not None and existing!=preview:
        raise RevisionRenderError('immutable preview conflict')
    if existing is None:
        try:
            storage.client.put_object(Bucket=storage.bucket,Key=key,
                Body=json.dumps(preview,sort_keys=True).encode(),
                ContentType='application/json',IfNoneMatch='*')
        except Exception:
            if _existing(storage,key)!=preview:
                raise
    if repository.get_job(job_id).store_version!=record.store_version:
        raise RevisionRenderError('canonical job changed before preview delivery')
    try:
        storage.client.put_object(Bucket=storage.bucket,Key=STATE_PREFIX+job_id+'.json',
            Body=json.dumps(pointer,sort_keys=True).encode(),
            ContentType='application/json',IfMatch=etag)
    except Exception:
        if _read_state(job_id,storage)[0]!=pointer:
            raise
    return 'READY_FOR_HUMAN'

def produce_revision(job_id,*,storage,repository,workdir):
    _uuid(job_id)
    if not isinstance(storage,R2Storage) or not isinstance(repository,R2JobRepository):
        raise RevisionRenderError('private durable R2 required')
    record=repository.get_job(job_id)
    job=record.job
    run=job.metadata.get('revision_render')
    if isinstance(run,dict) and run.get('revision')==job.revision:
        if job.status==JobStatus.READY_FOR_HUMAN:
            return _deliver(job_id,run['request_id'],storage,repository)
        if job.status!=JobStatus.RENDERING or run.get('state')!='RENDERING':
            raise RevisionRenderError('revision resume state invalid')
        ticket=_existing(storage,run['ticket_key'])
        if ticket!=run['ticket'] or plan_edit(ticket['human_request'])!=run['plan']:
            raise RevisionRenderError('immutable render plan changed')
        state,_=_read_state(job_id,storage)
        if state!=run['ack_state'] or len(job.media)!=1 or any(
            getattr(job.media[0],k)!=v for k,v in ticket['source_media'].items()):
            raise RevisionRenderError('resume authority/source changed')
    else:
        _,key=derive_canonical_edit_request(job_id,storage=storage,repository=repository)
        ticket=_existing(storage,key)
        plan=plan_edit(ticket['human_request'])
        if plan is None:
            blocked={'request_id':ticket['request_id'],'revision':job.revision,
                     'reason':'BLOCKED_UNSUPPORTED_EDIT'}
            if job.metadata.get('revision_edit_blocked')!=blocked:
                job.metadata['revision_edit_blocked']=blocked
                repository.save_job(job,expected_store_version=record.store_version)
            return 'BLOCKED_UNSUPPORTED_EDIT'
        state,_=_read_state(job_id,storage)
        if not isinstance(job.publish_payload.get('caption'),str):
            raise RevisionRenderError('original verified caption missing')
        run={'schema':'FACTORY-REVISION-RENDER-V1','state':'RENDERING',
             'job_id':job_id,'revision':job.revision,'request_id':ticket['request_id'],
             'ticket_key':key,'ticket':ticket,'plan':plan,
             'ack_state':state,'ack_review':state['review']}
        job.metadata['revision_render']=run
        job.transition(JobStatus.RENDERING)
        record=repository.save_job(job,expected_store_version=record.store_version)
    if job.human_approved_revision is not None or job.publish_handoff_key is not None:
        raise RevisionRenderError('render must never carry publishing authority')
    output=render(job.media[0],run['plan'],storage,workdir,
                  f"ffmpeg:human-edit:{run['request_id']}:r{job.revision}")
    job.media=[output]
    caption=job.publish_payload['caption']
    job.metadata[f'creative_package:r{job.revision}']={'draft':{'caption':caption}}
    job.transition(JobStatus.QM)
    report=FinalQM().evaluate(job,[
        QMCheck('exact_canonical_human_edit',plan_edit(run['ticket']['human_request'])==run['plan']),
        QMCheck('caption_unchanged_no_new_claims',job.metadata[f'creative_package:r{job.revision}']['draft']['caption']==caption),
        QMCheck('actual_ffmpeg_probe_and_private_sha',output.size_bytes>0),
        QMCheck('human_post_authority_absent',job.human_approved_revision is None and job.publish_handoff_key is None)])
    verified=present_verified_golden_tablet(job,report,storage=storage,
                                          max_media_bytes=MAX_DASHBOARD_VIDEO_BYTES)
    preview_id=str(uuid4())
    run['state']='READY_FOR_HUMAN'
    run['qm_report_id']=report.report_id
    run['preview']={'schema':'FACTORY-MEDIA-PREVIEW-V1','preview_id':preview_id,
        'state':'READY_FOR_HUMAN','qm_passed':True,
        'expires_at':(datetime.now(timezone.utc)+timedelta(hours=2)).isoformat(),
        'job_id':job_id,'revision':job.revision,'manifest':verified.tablet.manifest,
        'caption':caption,'media':{'media_id':output.media_id,
        'key':output.uri.removeprefix(f'r2://{storage.bucket}/'),
        'mime_type':output.mime_type,'size_bytes':output.size_bytes,'sha256':output.sha256}}
    repository.save_job(job,expected_store_version=record.store_version)
    return _deliver(job_id,run['request_id'],storage,repository)

