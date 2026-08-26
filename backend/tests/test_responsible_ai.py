import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
import app.models  # noqa: F401
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_responsible_ai_seed_and_contract(client):
    # 1. Seed cases first
    client.post("/api/cases/seed")

    # 2. Seed Responsible AI correction examples
    res = client.post("/api/responsible-ai/seed-examples")
    assert res.status_code == 200
    data = res.json()
    assert data["total_corrections"] >= 5
    assert data["target_met"] is True

    # 3. Retrieve Responsible AI Log
    log_res = client.get("/api/responsible-ai/")
    assert log_res.status_code == 200
    log_data = log_res.json()
    assert log_data["total_corrections"] >= 5
    assert len(log_data["records"]) >= 5

    # 4. Verify record structure contract
    for record in log_data["records"]:
        assert "case_id" in record
        assert "case_title" in record
        assert "reviewer_name" in record
        assert "decision" in record
        assert record["decision"] in ["EDITED", "REJECTED"]
        assert "ai_diagnosis" in record
        assert "human_correction" in record
        assert "why_ai_incorrect" in record
        assert len(record["why_ai_incorrect"]) > 10
        assert "root_cause" in record["ai_diagnosis"]
        assert "root_cause" in record["human_correction"]
