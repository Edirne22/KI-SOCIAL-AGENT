"""Actual R2-only conditional publication ledger smoke, NO SOCIAL NETWORK CALL.

Requires existing private R2 secrets, explicit test opt-in and test-only
object prefix. NEVER runs publisher.publish or stores a synthetic canonical
human-approved job. Tests only shared S3 first-writer/receipt mechanics.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4
import os
import tempfile

from content_factory_core import JobStatus, ProductionJob
from content_factory_control_center import PublishReceipt
from content_factory_publish_ledger import AmbiguousPublication
from content_factory_r2_publish_ledger import R2PublishLedger, SMOKE_PREFIX
from media_storage import R2Storage


def run():
    if os.environ.get("BLOCK9_R2_SMOKE_APPROVED") != "true":
        raise RuntimeError("REAL_PRIVATE_R2_SMOKE_NOT_APPROVED")
    with tempfile.TemporaryDirectory(prefix="block9-smoke-") as folder:
        storage=R2Storage.from_env(cache_root=Path(folder)/"cache")
        # This ephemeral state-machine specimen is NEVER put into canonical
        # Factory storage and never touches any Meta/IG publishing endpoint.
        specimen=ProductionJob("BLOCK9_LEDGER_ISOLATED_SMOKE_NO_USER_POST")
        specimen.status=JobStatus.READY_FOR_HUMAN
        specimen.publish_payload={"caption":"NO REAL PLATFORM POST -- R2 CAS TEST ONLY"}
        specimen.transition(JobStatus.APPROVED,actor="human")
        specimen.publish_handoff()

        def claim(_):
            try:
                R2PublishLedger(storage,prefix=SMOKE_PREFIX).reserve(specimen,"facebook")
                return "FIRST_WRITER_RESERVED"
            except AmbiguousPublication:
                return "DUPLICATE_CORRECTLY_BLOCKED"

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcome=sorted(pool.map(claim,(1,2)))
        if outcome!=sorted(("FIRST_WRITER_RESERVED","DUPLICATE_CORRECTLY_BLOCKED")):
            raise RuntimeError("REAL_R2_CAS_FIRST_WRITER_CONTRACT_FAILED")
        ledger=R2PublishLedger(storage,prefix=SMOKE_PREFIX)
        receipt=PublishReceipt(specimen.publish_handoff_key,"facebook",
            "smoke-only-"+str(uuid4()),"SMOKE_PRIVATE_R2_CAS_NO_PLATFORM")
        ledger.record_receipt(specimen.publish_handoff_key,"facebook",receipt)
        recovered=R2PublishLedger(storage,prefix=SMOKE_PREFIX).reserve(specimen,"facebook")
        if recovered!=receipt:
            raise RuntimeError("REAL_R2_RECEIPT_RECOVERY_FAILED")
        print("BLOCK9_PRIVATE_R2_ATOMIC_SMOKE_PASS "
              "parallel_first_writer=1 blocked_duplicate=1 "
              "restart_receipt=verified private_test_only=true "
              "real_platform_requests=0")


if __name__=="__main__":
    run()
