"""B6: factory-to-OpenMontage authorization contract."""
import unittest
from unittest.mock import patch

from content_factory_core import JobStatus, ProductionJob
from content_factory_handoff import HandoffError
from content_factory_media_production import MediaProductionError
from integrations.openmontage.factory_dispatch import dispatch_openmontage


class OpenMontageDispatchTests(unittest.TestCase):
    def setUp(self):
        self.job = ProductionJob("dispatch-test")
        self.job.status = JobStatus.STORYBOARDING
        self.args = dict(research={}, storyboard={}, media_manifest={}, storage=object())
        self.called = []

    def test_authorized_agent_dispatches_through_runner(self):
        with patch("integrations.openmontage.factory_dispatch.MediaProductionRunner.execute") as execute:
            execute.return_value = ("ok",)
            result = dispatch_openmontage(self.job, agent_role_id="07_video_optimization", **self.args)
            self.assertEqual(result, ("ok",))
            args, kwargs = execute.call_args
            self.assertEqual(kwargs["agent_role_id"], "07_video_optimization")
            self.assertEqual(args[1].steps[0].machine, "openmontage")
            self.assertEqual(args[1].steps[0].input_media_ids, ())

    def test_missing_agent_fails_closed(self):
        with patch("integrations.openmontage.factory_dispatch.MediaProductionRunner.execute") as execute:
            with self.assertRaises(HandoffError):
                dispatch_openmontage(self.job, agent_role_id=None, **self.args)
            execute.assert_not_called()

    def test_wrong_job_state_fails_closed(self):
        self.job.status = JobStatus.READY_FOR_HUMAN
        with patch("integrations.openmontage.factory_dispatch.MediaProductionRunner.execute") as execute:
            with self.assertRaises(MediaProductionError):
                dispatch_openmontage(self.job, agent_role_id="07_video_optimization", **self.args)
            execute.assert_not_called()

    def test_bad_payload_fails_closed(self):
        with self.assertRaises(MediaProductionError):
            dispatch_openmontage(self.job, agent_role_id="07_video_optimization",
                research=[], storyboard={}, media_manifest={}, storage=object())

    def test_unauthorized_role_does_not_call_producer(self):
        called = []
        def producer(**kwargs):
            called.append(1)
        with self.assertRaises(HandoffError):
            dispatch_openmontage(self.job, agent_role_id="15_finance_planner",
                producer=producer, **self.args)
        self.assertEqual(called, [])


if __name__ == "__main__":
    unittest.main()
