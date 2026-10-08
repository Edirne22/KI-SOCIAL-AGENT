"""Synthetic R2 adapter E2E; fixture classifier, actual FFmpeg and independent QM.
Real offline model inference is tested separately with pinned weights.
"""
from dataclasses import replace
import io
import os
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
from PIL import Image
from content_factory_private_video_orchestrator import (
    analyze_private_media,build_plan,preflight_private_machine_contract,
    PrivateQM,verify_render_contract,
)
from scripts import private_birthday_first_production as birthday
from tests.test_private_birthday_timeline import MemoryR2

@unittest.skipUnless(shutil.which('ffmpeg'),'FFmpeg required')
class CreativeE2ETests(unittest.TestCase):
    def test_synthetic_r2_analysis_storyboard_batched_render_qm(self):
        objects={};assets=[]
        for i in range(9):
            buf=io.BytesIO();Image.new('RGB',(180,320),(i*25,40,220-i*20)).save(buf,format='PNG')
            objects[str(i)]=buf.getvalue();assets.append({'key':str(i),'mime':'image/png'})
        client=MemoryR2(objects)
        index=iter(range(9))
        def fixture_classifier(jpeg):
            i=next(index)
            return {'story_beat':('build','action','home')[i%3],
                    'asset_role':'synthetic-scene','observations':['Synthetic fixture, not real image classification']}
        classified=analyze_private_media(client,'synthetic',assets,infer=fixture_classifier)
        plan=replace(build_plan('synthetic','Dünya 12 Geburtstag',classified),duration_seconds=24)
        self.assertEqual(preflight_private_machine_contract(plan,classified)['decision'],'READY_FOR_MEDIA')
        self.assertNotEqual(plan.asset_order,tuple(range(9)))
        with patch.object(birthday,'client_from_env',return_value=(client,'synthetic')), \
             patch.dict(os.environ,TELEGRAM_BOT_TOKEN='synthetic',TELEGRAM_CHAT_ID='synthetic'), \
             patch.object(birthday.requests,'post') as send:
            result=birthday.run(task_id='synthetic',plan=plan,assets_override=classified)
        send.assert_not_called()
        self.assertAlmostEqual(result['duration'],24,delta=.5)
        evidence=result['creative_evidence']
        self.assertTrue(verify_render_contract(plan,classified,evidence))
        qm=PrivateQM().checks(duration=result['duration'],has_audio=result['has_audio'],
                             has_video=result['has_video'],creative={**evidence,
                             'expected_effects':plan.asset_effects,'privacy':plan.privacy})
        self.assertTrue(qm['passed'],qm)
        evidence['asset_evidence'][0]['source_sha256']='0'*64
        self.assertFalse(verify_render_contract(plan,classified,evidence))

    def test_uncertainty_duplicates_and_source_integrity(self):
        from hashlib import sha256
        buf=io.BytesIO();Image.new('RGB',(160,288),'blue').save(buf,format='PNG')
        raw=buf.getvalue();client=MemoryR2({'a':raw,'b':raw})
        assets=[{'key':x,'mime':'image/png'} for x in ('a','b')]
        report=[]
        result=analyze_private_media(client,'test',assets,infer=lambda _: {'accepted':False},report=report)
        self.assertEqual(result,[])
        self.assertEqual([x['decision'] for x in report],['uncertain-excluded','duplicate'])
        with self.assertRaisesRegex(RuntimeError,'SOURCE_HASH_MISMATCH'):
            analyze_private_media(client,'test',[{**assets[0],'sha256':'0'*64}],infer=lambda _: {})
