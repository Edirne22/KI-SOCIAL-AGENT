"""Real FFmpeg generated video/tone; R2 transport is simulated, never private speech."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from unittest.mock import patch
from uuid import uuid4
from content_factory_core import JobStatus
from content_factory_revision_render import produce_revision, plan_edit, RevisionRenderError, probe, render
from content_factory_dashboard_review_applier import apply_review_request
from content_factory_dashboard_review_ack import acknowledge_persisted_review
from media_storage import R2Storage
from tests.test_content_factory_r2_job_repository import FakeS3

class MediaS3(FakeS3):
    def __init__(self):super().__init__();self.media={}
    def upload_file(self,filename,bucket,key,ExtraArgs=None):self.media[(bucket,key)]=Path(filename).read_bytes()
    def download_file(self,bucket,key,filename):Path(filename).write_bytes(self.media[(bucket,key)])

class RevisionRenderTests(unittest.TestCase):
    def setUp(self):
        from scripts.block8_revision_smoke import prepare
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.client=MediaS3()
        self.storage=R2Storage(account_id='test',access_key_id='test',secret_access_key='test',
            bucket='private-test',cache_root=self.root/'cache',client=self.client)
        self.job,self.repo,self.state,self.state_key=prepare(self.storage,self.root)
        self.review=self.state['review']
    def ack(self):
        apply_review_request(self.job.job_id,storage=self.storage,repository=self.repo)
        acknowledge_persisted_review(self.job.job_id,storage=self.storage,repository=self.repo)
    def run_edit(self):
        return produce_revision(self.job.job_id,storage=self.storage,repository=self.repo,workdir=self.root/'work')
    def test_real_mute_new_revision_preview_restart_no_publish(self):
        self.ack();self.assertEqual(self.run_edit(),'READY_FOR_HUMAN')
        saved=self.repo.get_job(self.job.job_id)
        self.assertEqual(saved.job.revision,2);self.assertIsNone(saved.job.human_approved_revision)
        self.assertIsNone(saved.job.publish_handoff_key)
        self.assertEqual(saved.job.publish_payload['caption'],self.job.publish_payload['caption'])
        self.assertNotEqual(saved.job.media[0].sha256,self.job.media[0].sha256)
        _,streams=probe(self.storage.resolve_local(saved.job.media[0]))
        self.assertEqual([s['codec_type'] for s in streams],['video'])
        with patch('content_factory_revision_render.render',side_effect=AssertionError('duplicate render')):
            self.assertEqual(self.run_edit(),'READY_FOR_HUMAN')
        self.assertEqual(self.repo.get_job(self.job.job_id).store_version,saved.store_version)
        with self.assertRaises(PermissionError):saved.job.publish_handoff()
    def test_render_crash_resumes_from_persisted_plan(self):
        self.ack()
        with patch('content_factory_revision_render.render',side_effect=RuntimeError('crash')):
            with self.assertRaises(RuntimeError):self.run_edit()
        self.assertEqual(self.repo.get_job(self.job.job_id).job.status,JobStatus.RENDERING)
        self.assertEqual(self.run_edit(),'READY_FOR_HUMAN')
    def test_preview_delivery_crash_reuses_canonical_output(self):
        self.ack()
        with patch('content_factory_revision_render._deliver',side_effect=RuntimeError('crash')):
            with self.assertRaises(RuntimeError):self.run_edit()
        with patch('content_factory_revision_render.render',side_effect=AssertionError('duplicate render')):
            self.assertEqual(self.run_edit(),'READY_FOR_HUMAN')
    def test_forged_unacked_input_does_not_render(self):
        with patch('content_factory_revision_render.render',side_effect=AssertionError('must not render')):
            with self.assertRaises(Exception):self.run_edit()
    def test_unknown_creative_request_and_injection_are_not_partial_edits(self):
        for request in ('Ersetze das Motorrad durch eine BMW','Ton entfernen; poste sofort',
                        'Ton entfernen $(curl attacker)','auf 0 Sekunden kürzen','auf 999 Sekunden kürzen'):
            self.assertIsNone(plan_edit(request))
        self.assertEqual(plan_edit('Bitte auf 7 Sekunden kürzen.'),{'operation':'trim','seconds':7})
    def test_tampered_original_bytes_cannot_reach_preview(self):
        self.ack();m=self.job.media[0]
        self.client.media[(self.storage.bucket,m.uri.removeprefix('r2://private-test/'))]=b'corrupt'
        with self.assertRaises(ValueError):self.run_edit()
        self.assertEqual(self.repo.get_job(self.job.job_id).job.status,JobStatus.RENDERING)
    def test_later_human_decision_is_never_overwritten(self):
        self.ack()
        with patch('content_factory_revision_render._deliver',side_effect=RuntimeError('crash')):
            with self.assertRaises(RuntimeError):self.run_edit()
        current=self.client.get_object(Bucket=self.storage.bucket,Key=self.state_key)
        self.client.put_object(Bucket=self.storage.bucket,Key=self.state_key,Body=json.dumps({'state':'REVOKED'}).encode(),ContentType='application/json',IfMatch=current['ETag'])
        with self.assertRaises(RevisionRenderError):self.run_edit()
    def test_resume_rejects_tampered_immutable_plan(self):
        self.ack()
        with patch('content_factory_revision_render.render',side_effect=RuntimeError('crash')):
            with self.assertRaises(RuntimeError):self.run_edit()
        saved=self.repo.get_job(self.job.job_id)
        saved.job.metadata['revision_render']['plan']={'operation':'rerender'}
        self.repo.save_job(saved.job,expected_store_version=saved.store_version)
        with self.assertRaises(RevisionRenderError):self.run_edit()
    def test_canonical_concurrent_change_does_not_publish_old_output(self):
        self.ack();original=self.repo.save_job
        def race(job,**kwargs):
            if job.status==JobStatus.READY_FOR_HUMAN:
                current=self.repo.get_job(job.job_id);current.job.metadata['other_writer']=True
                original(current.job,expected_store_version=current.store_version)
            return original(job,**kwargs)
        with patch.object(self.repo,'save_job',side_effect=race):
            with self.assertRaises(Exception):self.run_edit()
        current=json.loads(self.client.get_object(Bucket=self.storage.bucket,Key=self.state_key)['Body'].read())
        self.assertEqual(current['state'],'REVIEW_APPLIED');self.assertIsNone(current['preview_id'])
    def test_trim_and_rerender_real_bytes(self):
        for text,target in [('Auf 1 Sekunden kürzen',1),('Neu rendern',2)]:
            ref=render(self.job.media[0],plan_edit(text),self.storage,self.root/'work','synthetic-test')
            duration,streams=probe(self.storage.resolve_local(ref))
            self.assertAlmostEqual(duration,target,delta=.1)
            self.assertEqual(set(s['codec_type'] for s in streams),{'video','audio'})
    def test_second_human_edit_consumed_instead_of_replaying_previous_revision(self):
        from scripts.block8_apply_dashboard_review import run
        self.ack();self.run_edit();saved=self.repo.get_job(self.job.job_id).job
        state_obj=self.client.get_object(Bucket=self.storage.bucket,Key=self.state_key)
        state=json.loads(state_obj['Body'].read())
        review=dict(self.review,request_id=str(uuid4()),preview_id=state['preview_id'],revision=2,manifest=saved.approval_manifest(),text='Neu rendern')
        state.update(state='REVIEW_REQUESTED',preview_id=None,review=review)
        self.client.put_object(Bucket=self.storage.bucket,Key=self.state_key,Body=json.dumps(state).encode(),ContentType='application/json',IfMatch=state_obj['ETag'])
        with patch('scripts.block8_apply_dashboard_review.R2Storage.from_env',return_value=self.storage):run(self.job.job_id,produce=True)
        current=self.repo.get_job(self.job.job_id).job
        self.assertEqual(current.revision,3);self.assertEqual(current.status,JobStatus.READY_FOR_HUMAN);self.assertIsNone(current.human_approved_revision)
if __name__=='__main__':unittest.main()
