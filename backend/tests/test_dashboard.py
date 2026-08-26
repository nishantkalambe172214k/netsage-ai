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


def test_dashboard_metrics_real_calculations(client):
    # 1. Seed 30 cases and 5 responsible AI examples
    client.post("/api/cases/seed")
    client.post("/api/responsible-ai/seed-examples")

    # 2. Add an ACCEPT review to test agreement rate calculation
    client.post("/api/reviews/CASE-VLAN-001", json={
        "reviewer_name": "Engineer Alice",
        "decision": "ACCEPTED",
        "review_notes": "Valid diagnosis"
    })

    # 3. Query Dashboard endpoint
    res = client.get("/api/dashboard/")
    assert res.status_code == 200
    d = res.json()

    kpis = d["kpis"]
    assert kpis["total_cases"] == 30
    assert kpis["human_reviewed"] >= 6  # 5 edited + 1 accepted
    assert kpis["accepted"] >= 1
    assert kpis["edited"] >= 5
    assert kpis["responsible_ai_corrections"] >= 5
    assert kpis["ai_human_agreement_rate"] > 0.0

    charts = d["charts"]
    assert "cases_by_category" in charts
    assert sum(charts["cases_by_category"].values()) == 30
    assert charts["review_outcomes"]["Accepted"] >= 1
    assert charts["review_outcomes"]["Edited"] >= 5
    assert charts["verification_results"]["Passed"] >= 5
