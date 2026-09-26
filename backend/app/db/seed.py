import datetime
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.security import get_password_hash

from app.models.patient import Bed

logger = logging.getLogger("pulseguard.seed")


async def seed_initial_data(session: AsyncSession, force: bool = False):
    """
    Seeds only the bare-minimum bootstrap data required to start the system:
    1. One default admin account so the first user can log in and create others.
    2. Available empty physical ward beds (no patients, no synthetic medical data)
       so that clinical admissions have beds to assign into.

    All clinical data (patients, doctors, transfers, notes, alerts) is
    entered through the application by authenticated users and stored in the database.
    """
    now = datetime.datetime.utcnow()

    # 1. Admin account
    stmt = select(User).where(User.role == "admin").limit(1)
    res = await session.execute(stmt)
    if not res.scalars().first():
        logger.info("First run detected — seeding bootstrap admin account...")
        admin = User(
            id="usr_bootstrap_admin",
            name="System Administrator",
            email="admin@pulseguard.local",
            role="admin",
            status="active",
            credentials_ref=get_password_hash("Admin@PulseGuard2026"),
            created_at=now,
        )
        session.add(admin)
        await session.commit()
        logger.info(
            "Bootstrap admin created — "
            "email: admin@pulseguard.local | "
            "password: Admin@PulseGuard2026 | "
            "CHANGE THIS IMMEDIATELY after first login."
        )

    # 2. Empty physical ICU beds (01-10) ready for patient admission
    stmt_bed = select(Bed).limit(1)
    res_bed = await session.execute(stmt_bed)
    if not res_bed.scalars().first():
        logger.info("Initializing 10 available ward beds (all empty, ready for admissions)...")
        for i in range(1, 11):
            bed_num = f"{i:02d}"
            bed = Bed(
                id=bed_num,
                ward="Critical Care Unit 4",
                device_id=f"IOT-MON-B{bed_num}",
                status="available",
                patient_id=None,
            )
            session.add(bed)
        await session.commit()
        logger.info("Initialized 10 physical ward beds (01 to 10).")

