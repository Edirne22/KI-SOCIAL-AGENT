"""Only new synthetic test jobs; real FFmpeg, optional real R2, never a publisher.
The owner event is simulated, not a claim of actual browser/human acceptance.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
import argparse
import json
import os
import subprocess
from content_factory_core import ProductionJob, JobStatus
from content_factory_golden_tablet import FinalQM, QMCheck
from content_factory_dashboard_preview import register_verified_video_preview, STATE_PREFIX
from content_factory_r2_job_repository import R2JobRepository
from content_factory_dashboard_review_applier import apply_review_request
from content_factory_dashboard_review_ack import acknowledge_persisted_review
from content_factory_revision_render import produce_revision, probe
from media_storage import R2Storage

def prepare(storage,root):
    source=root/'synthetic.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=c=blue:s=160x240:r=24',
        '-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','2',
        '-c:v','libx264','-threads','1','-pix_fmt','yuv420p','-c:a','aac',str(source)],check=True)
    job=ProductionJob('SYNTHETIC REVISION TEST NEVER PUBLISH')
    job.media=[storage.put_file(source,provenance='synthetic-generated-tone-no-speech',mime_type='video/mp4')]
    job.metadata['synthetic_test_only']=True
    job.metadata['creative_package:r1']={'draft':{'caption':'SYNTHETIC TEST NEVER PUBLISH'}}
    for state in (JobStatus.INGESTING,JobStatus.RESEARCHING,JobStatus.WRITING,
                  JobStatus.STORYBOARDING,JobStatus.RENDERING,JobStatus.QM):job.transition(state)
    duration,streams=probe(storage.resolve_local(job.media[0]))
    report=FinalQM().evaluate(job,[QMCheck('synthetic_probe',1.5<duration<2.5 and len(streams)==2)])
    repo=R2JobRepository(storage)
    preview=register_verified_video_preview(job,report,storage=storage,repository=repo)
    review={'schema':'FACTORY-REVIEW-INTENT-V1','request_id':str(uuid4()),
        'preview_id':preview,'job_id':job.job_id,'revision':1,'manifest':job.approval_manifest(),
        'actor':'authenticated_dashboard_owner','status':'PENDING_FACTORY_APPLICATION',
        'action':'change','text':'Ton entfernen','requested_at':job.updated_at}
    state={'schema':'FACTORY-PREVIEW-STATE-V1','job_id':job.job_id,'revision':1,
        'manifest':job.approval_manifest(),'preview_id':None,'state':'REVIEW_REQUESTED','review':review}
    key=STATE_PREFIX+job.job_id+'.json'
    old=storage.client.get_object(Bucket=storage.bucket,Key=key)
    storage.client.put_object(Bucket=storage.bucket,Key=key,Body=json.dumps(state).encode(),
        ContentType='application/json',IfMatch=old['ETag'])
    return job,repo,state,key

def run(*,live=False,evidence=None):
    if live and (os.environ.get('GITHUB_REF')!='refs/heads/main' or
                 os.environ.get('GITHUB_EVENT_NAME') not in ('push','workflow_dispatch')):
        raise RuntimeError('live smoke requires trusted main')
    with TemporaryDirectory(prefix='synthetic-revision-') as td:
        root=Path(td)
        if live:
            storage=R2Storage.from_env(cache_root=root/'cache')
        else:
            from tests.test_content_factory_revision_render import MediaS3
            storage=R2Storage(account_id='test',access_key_id='test',secret_access_key='test',
                bucket='private-test',cache_root=root/'cache',client=MediaS3())
        job,repo,state,key=prepare(storage,root)
        apply_review_request(job.job_id,storage=storage,repository=repo)
        acknowledge_persisted_review(job.job_id,storage=storage,repository=repo)
        result=produce_revision(job.job_id,storage=storage,repository=repo,workdir=root/'render')
        done=repo.get_job(job.job_id)
        if result!='READY_FOR_HUMAN' or done.job.revision!=2 or done.job.human_approved_revision is not None:
            raise RuntimeError('revision acceptance failed')
        _,tracks=probe(storage.resolve_local(done.job.media[0]))
        if any(t['codec_type']=='audio' for t in tracks):raise RuntimeError('mute failed')
        repeated=produce_revision(job.job_id,storage=storage,repository=repo,workdir=root/'render')
        if repeated!=result or repo.get_job(job.job_id).store_version!=done.store_version:
            raise RuntimeError('replay was not idempotent')
        rendering=done.job.metadata['revision_render']
        if evidence:
            keys=[repo._key(job.job_id),key,rendering['ticket_key'],
                  'ai-central/v1/previews/'+rendering['preview']['preview_id']+'.json']
            docs={k:json.loads(storage.client.get_object(Bucket=storage.bucket,Key=k)['Body'].read()) for k in keys}
            Path(evidence).write_text(json.dumps({'job_id':job.job_id,'request_id':state['review']['request_id'],'objects':docs}))
        print(json.dumps({'result':'SYNTHETIC_REVISION_LIVE_R2_PASS' if live else 'SYNTHETIC_REVISION_SIMULATED_R2_PASS',
            'ffmpeg':'REAL','job_id':job.job_id,'revision':2,'preview_id':rendering['preview']['preview_id'],
            'idempotent':True,'published':False,'human_browser_test':False}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--live-r2',action='store_true');p.add_argument('--evidence')
    args=p.parse_args();run(live=args.live_r2,evidence=args.evidence)
