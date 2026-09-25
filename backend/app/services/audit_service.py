import hashlib
import datetime
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog

logger = logging.getLogger("pulseguard.audit")

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

# In-memory buffer for write resilience (flushed upon DB reconnect)
_resilience_audit_buffer: List[Dict[str, Any]] = []


def calculate_hash(previous_hash: str, timestamp: datetime.datetime, action: str, bed_id: Optional[str], clinician_id: Optional[str]) -> str:
    raw = f"{previous_hash}{timestamp.isoformat()}{action}{bed_id or ''}{clinician_id or ''}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


async def append_audit_log(
    session: AsyncSession,
    action: str,
    bed_id: Optional[str] = None,
    clinician_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Appends a cryptographically linked SHA-256 audit entry.
    Resilience invariant: if DB write times out, buffers write in memory with gap_marker="true"
    so clinical alarm paths are never blocked by upstream DB stalls.
    """
    now = datetime.datetime.utcnow()

    # Flush any buffered logs first
    if _resilience_audit_buffer:
        try:
            for item in list(_resilience_audit_buffer):
                buffered_row = AuditLog(
                    timestamp=item["timestamp"],
                    action=item["action"],
                    bed_id=item["bed_id"],
                    clinician_id=item["clinician_id"],
                    previous_hash=item["previous_hash"],
                    hash=item["hash"],
                    metadata_json=item["metadata"],
                    gap_marker="true"
                )
                session.add(buffered_row)
                _resilience_audit_buffer.remove(item)
            await session.commit()
            logger.info("Flushed resilience audit buffer to PostgreSQL.")
        except Exception as e:
            logger.warning(f"Could not flush audit buffer: {e}")

    try:
        # Fetch the latest block to get previous_hash
        stmt = select(AuditLog).order_by(AuditLog.seq_id.desc()).limit(1)
        res = await session.execute(stmt)
        last_block = res.scalars().first()

        prev_hash = last_block.hash if last_block else GENESIS_HASH
        curr_hash = calculate_hash(prev_hash, now, action, bed_id, clinician_id)

        log_entry = AuditLog(
            timestamp=now,
            action=action,
            bed_id=bed_id,
            clinician_id=clinician_id,
            previous_hash=prev_hash,
            hash=curr_hash,
            metadata_json=metadata or {}
        )
        session.add(log_entry)
        await session.commit()
        await session.refresh(log_entry)
        return log_entry

    except Exception as e:
        logger.error(f"PostgreSQL write timeout/failure during audit logging: {e}. Buffering in memory.")
        # Calculate with known previous hash if possible
        prev_hash = GENESIS_HASH
        curr_hash = calculate_hash(prev_hash, now, action, bed_id, clinician_id)
        _resilience_audit_buffer.append({
            "timestamp": now,
            "action": action,
            "bed_id": bed_id,
            "clinician_id": clinician_id,
            "previous_hash": prev_hash,
            "hash": curr_hash,
            "metadata": metadata,
        })
        # Return transient object without raising to keep clinical path non-blocking
        return AuditLog(
            timestamp=now,
            action=action,
            bed_id=bed_id,
            clinician_id=clinician_id,
            previous_hash=prev_hash,
            hash=curr_hash,
            gap_marker="true"
        )


async def verify_chain(session: AsyncSession) -> Dict[str, Any]:
    """
    Walks the entire audit ledger from Genesis block to verify cryptographic SHA-256 integrity.
    Returns whether chain is intact or reports exact sequence divergence.
    """
    stmt = select(AuditLog).order_by(AuditLog.seq_id.asc())
    res = await session.execute(stmt)
    blocks = res.scalars().all()

    if not blocks:
        return {
            "intact": True,
            "total_blocks": 0,
            "message": "Audit ledger is empty (Genesis state)."
        }

    expected_prev = GENESIS_HASH

    for b in blocks:
        # Verify previous_hash link
        if b.previous_hash != expected_prev:
            return {
                "intact": False,
                "total_blocks": len(blocks),
                "broken_at_seq": b.seq_id,
                "reason": f"Block #{b.seq_id} previous_hash '{b.previous_hash}' does not match expected '{expected_prev}'.",
                "message": f"Tampering detected at block #{b.seq_id}."
            }

        # Verify current hash computation
        recomputed = calculate_hash(b.previous_hash, b.timestamp, b.action, b.bed_id, b.clinician_id)
        if b.hash != recomputed:
            return {
                "intact": False,
                "total_blocks": len(blocks),
                "broken_at_seq": b.seq_id,
                "reason": f"Block #{b.seq_id} payload corrupted: stored hash '{b.hash}' != computed '{recomputed}'.",
                "message": f"Hash divergence detected at block #{b.seq_id}."
            }

        expected_prev = b.hash

    return {
        "intact": True,
        "total_blocks": len(blocks),
        "latest_hash": blocks[-1].hash,
        "message": f"Chain intact ✓ — {len(blocks)} blocks cryptographically verified from Genesis."
    }
