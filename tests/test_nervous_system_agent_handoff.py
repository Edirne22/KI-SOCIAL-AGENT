"""Small, offline authorization regressions for the factory handoff boundary."""
import unittest
from content_factory_core import ProductionJob
from content_factory_handoff import (
    HandoffError, ToolResult, ToolTask, run_authorized_agent_machine,
)

class DummyMachine:
    name = "dummy"
    def __init__(self):
        self.calls = 0
    def run(self, task):
        self.calls += 1
        return ToolResult(task.job_id, task.revision, task.task_id, [], self.name)

class AgentMachineHandoffTests(unittest.TestCase):
    def setUp(self):
        self.job = ProductionJob("safe test")
        self.machine = DummyMachine()
        self.task = ToolTask(self.job.job_id, self.job.revision, "t-1")

    def test_canonical_authorized_role_can_dispatch(self):
        result = run_authorized_agent_machine(
            self.job, self.machine, self.task,
            agent_role_id="07_video_optimization", required_capability="media_tools")
        self.assertEqual(result.task_id, "t-1")
        self.assertEqual(self.machine.calls, 1)

    def test_ambiguous_15_is_blocked_before_machine_call(self):
        with self.assertRaisesRegex(HandoffError, "identity"):
            run_authorized_agent_machine(
                self.job, self.machine, self.task,
                agent_role_id="15", required_capability="media_tools")
        self.assertEqual(self.machine.calls, 0)

    def test_unauthorized_capability_is_blocked(self):
        with self.assertRaisesRegex(HandoffError, "capability"):
            run_authorized_agent_machine(
                self.job, self.machine, self.task,
                agent_role_id="15_finance_planner", required_capability="media_tools")
        self.assertEqual(self.machine.calls, 0)

    def test_cross_job_is_still_blocked(self):
        other = ToolTask("another-job", self.job.revision, "t-1")
        with self.assertRaisesRegex(HandoffError, "envelope"):
            run_authorized_agent_machine(
                self.job, self.machine, other,
                agent_role_id="07_video_optimization", required_capability="media_tools")
        self.assertEqual(self.machine.calls, 0)

if __name__ == "__main__":
    unittest.main()
