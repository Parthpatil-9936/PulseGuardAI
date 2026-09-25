import asyncio
import pytest
import pytest_asyncio
import datetime
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.core.config import settings
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.patient import Patient, Bed
from app.models.assignment import PatientAssignment
from app.main import app

# In-memory SQLite for high-speed isolated unit/integration tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        # Seed test fixtures
        doc1 = User(id="doc_1", name="Dr. Alice", email="alice@ward.icu", role="doctor", status="active", credentials_ref=get_password_hash("pass123"))
        doc2 = User(id="doc_2", name="Dr. Bob", email="bob@ward.icu", role="doctor", status="active", credentials_ref=get_password_hash("pass123"))
        nurse = User(id="nurse_1", name="Nurse Carol", email="carol@ward.icu", role="nurse", status="active", credentials_ref=get_password_hash("pass123"))
        admin = User(id="admin_1", name="Admin Dave", email="dave@ward.icu", role="admin", status="active", credentials_ref=get_password_hash("pass123"))

        patient = Patient(id="pat_1", external_ref="MRN-001", demographics={"name": "John Doe", "age": 60}, status="admitted")
        bed = Bed(id="01", ward="ICU 4", device_id="IOT-B1", status="occupied", patient_id="pat_1")
        assignment = PatientAssignment(id="asgn_1", patient_id="pat_1", doctor_id="doc_1", status="active")

        session.add_all([doc1, doc2, nurse, admin, patient, bed, assignment])
        await session.commit()
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    def _headers(user_id: str, role: str):
        token = create_access_token(subject=user_id, role=role)
        return {"Authorization": f"Bearer {token}"}
    return _headers
