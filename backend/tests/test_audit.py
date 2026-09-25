import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.audit_service import append_audit_log, verify_chain
from app.models.audit import AuditLog


@pytest.mark.asyncio
async def test_audit_chain_verification_and_tamper_detection(test_db: AsyncSession):
    # 1. Append sequential audit events
    log1 = await append_audit_log(test_db, action="LOGIN", bed_id=None, clinician_id="doc_1")
    log2 = await append_audit_log(test_db, action="ALERT_ACKNOWLEDGED", bed_id="01", clinician_id="doc_1")
    log3 = await append_audit_log(test_db, action="TRANSFER_APPROVED", bed_id="01", clinician_id="admin_1")

    # 2. Verify pristine chain
    result_clean = await verify_chain(test_db)
    assert result_clean["intact"] is True
    assert result_clean["total_blocks"] >= 3

    # 3. Deliberately tamper with block #2 hash to simulate unauthorized ledger modification
    stmt = select(AuditLog).where(AuditLog.seq_id == log2.seq_id)
    res = await test_db.execute(stmt)
    corrupt_block = res.scalars().first()
    corrupt_block.hash = "00000000000000000000000000000000000000000000000000000000tampered"
    await test_db.commit()

    # 4. Verify chain detects tampering
    result_tampered = await verify_chain(test_db)
    assert result_tampered["intact"] is False
    assert result_tampered["broken_at_seq"] == log2.seq_id
    assert "Tampering detected" in result_tampered["message"] or "Hash divergence" in result_tampered["message"]
