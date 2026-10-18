"""Regression: media runner must enforce agent authority when an identity is supplied."""
import unittest
from content_factory_core import ProductionJob
from content_factory_media_production import MediaProductionPlan, MediaProductionRunner, MediaStep, MediaStage
from content_factory_handoff import HandoffError, ToolResult

class Machine:
    name = "mock"
    def __init__(self):
        self.calls = 0
    def run(self, task):
        self.calls += 1
        return ToolResult(task.job_id, task.revision, task.task_id, [], self.name)

class MediaRunnerAgentTests(unittest.TestCase):
    def setUp(self):
        self.job = ProductionJob("test")
        self.plan = MediaProductionPlan(self.job.job_id, self.job.revision, "brief",
            (MediaStep("step1", MediaStage.RENDER, "mock", ()),))
        self.machine = Machine()

    def test_authorized_agent_executes(self):
        MediaProductionRunner().execute(self.job,self.plan,{"mock":self.machine},
            agent_role_id="07_video_optimization")
        self.assertEqual(self.machine.calls, 1)

    def test_ambiguous_agent_does_not_execute(self):
        with self.assertRaises(HandoffError):
            MediaProductionRunner().execute(self.job,self.plan,{"mock":self.machine},
                agent_role_id="15")
        self.assertEqual(self.machine.calls, 0)

    def test_unauthorized_agent_does_not_execute(self):
        with self.assertRaises(HandoffError):
            MediaProductionRunner().execute(self.job,self.plan,{"mock":self.machine},
                agent_role_id="15_finance_planner")
        self.assertEqual(self.machine.calls, 0)

if __name__ == "__main__":
    unittest.main()
