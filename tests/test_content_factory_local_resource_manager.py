"""Offline positive/negative controls for local two-lane resource admission."""
import unittest
from uuid import uuid4

from content_factory_local_resource_manager import (
    AdmissionError, Capacity, LocalResourceManager, ResourceClaim, ResourceLease,
)


def claim(*, job=None, task="task", lane="content", cpu=1, gpu=0, api=0, revision=1, priority=50):
    return ResourceClaim(
        job_id=job or str(uuid4()), revision=revision, task_id=task, lane=lane,
        demand=Capacity(cpu=cpu, gpu=gpu, api=api), priority=priority,
    )


class ResourceAdmissionTests(unittest.TestCase):
    def test_independent_content_and_workshop(self):
        manager = LocalResourceManager(Capacity(2, 1, 2))
        render = claim(cpu=1, gpu=1)
        research = claim(lane="workshop", cpu=1, api=1)
        first, second = manager.reserve(render), manager.reserve(research)
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertEqual(manager.snapshot()["used"], Capacity(2, 1, 1))
        self.assertEqual(manager.snapshot()["truth"], "LOCAL_EPHEMERAL_ONLY")
        manager.release(first)
        manager.release(second)
        self.assertEqual(manager.snapshot()["used"], Capacity(0, 0, 0))

    def test_gpu_exhaustion_does_not_block_api_only_work(self):
        manager = LocalResourceManager(Capacity(2, 1, 2))
        self.assertIsNotNone(manager.reserve(claim(cpu=1, gpu=1)))
        self.assertIsNone(manager.reserve(claim(cpu=1, gpu=1)))
        self.assertIsNotNone(manager.reserve(claim(lane="workshop", cpu=1, api=1)))

    def test_idempotent_retries_do_not_double_count(self):
        manager = LocalResourceManager(Capacity(1, 0, 0))
        item = claim()
        one = manager.reserve(item)
        self.assertEqual(one, manager.reserve(item))
        self.assertEqual(manager.snapshot()["used"].cpu, 1)

    def test_stale_revision_and_mutated_claim_rejected(self):
        manager = LocalResourceManager(Capacity(2, 0, 0))
        item = claim()
        lease = manager.reserve(item)
        for changed in (
            claim(job=item.job_id, task=item.task_id, revision=2),
            claim(job=item.job_id, task=item.task_id, cpu=2),
        ):
            with self.assertRaisesRegex(AdmissionError, "stale or contradictory"):
                manager.reserve(changed)
        self.assertEqual(manager.snapshot()["active"], 1)
        manager.release(lease)

    def test_wrong_lease_cannot_free_another_task(self):
        manager = LocalResourceManager(Capacity(1, 0, 0))
        lease = manager.reserve(claim())
        attacker = ResourceLease(str(uuid4()), lease.claim)
        with self.assertRaisesRegex(AdmissionError, "foreign"):
            manager.release(attacker)
        self.assertEqual(manager.snapshot()["active"], 1)
        manager.release(lease)
        with self.assertRaisesRegex(AdmissionError, "missing"):
            manager.release(lease)

    def test_batch_priority_and_first_seen_stability(self):
        manager = LocalResourceManager(Capacity(1, 0, 0))
        low = claim(priority=70)
        high = claim(priority=10)
        selected, queued = manager.reserve_batch([low, high])
        self.assertEqual([item.claim for item in selected], [high])
        self.assertEqual(queued, [low])

    def test_lane_limit_does_not_hide_free_capacity(self):
        manager = LocalResourceManager(Capacity(3, 0, 0), {"content": 1})
        self.assertIsNotNone(manager.reserve(claim(lane="content")))
        self.assertIsNone(manager.reserve(claim(lane="content")))
        self.assertIsNotNone(manager.reserve(claim(lane="workshop")))

    def test_negative_inputs_and_no_implicit_release(self):
        with self.assertRaises(AdmissionError):
            Capacity(cpu=True, gpu=0, api=0)
        with self.assertRaises(AdmissionError):
            Capacity(cpu=-1, gpu=0, api=0)
        with self.assertRaises(AdmissionError):
            claim(cpu=0)
        with self.assertRaises(AdmissionError):
            claim(lane="publisher")
        with self.assertRaises(AdmissionError):
            claim(revision=0)
        with self.assertRaises(AdmissionError):
            LocalResourceManager(Capacity(1, 0, 0), {"workshop": 0})


if __name__ == "__main__":
    unittest.main()
