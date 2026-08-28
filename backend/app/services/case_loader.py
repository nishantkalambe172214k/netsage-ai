import csv
import json
import os
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.case import Case
from app.services.seed_data import export_cases_to_csv, CASES_DATA


def seed_cases(db: Session, csv_path: str = "data/cases.csv") -> int:
    """Seeds the SQLite database with cases from CSV or in-memory definitions."""
    candidate_paths = [
        csv_path,
        os.path.join(os.path.dirname(__file__), "../../../data/cases.csv"),
        os.path.join(os.path.dirname(__file__), "../../data/cases.csv"),
        os.path.join(os.getcwd(), "data/cases.csv"),
        os.path.join(os.getcwd(), "../data/cases.csv"),
    ]
    
    found_path = None
    for p in candidate_paths:
        if os.path.exists(p):
            found_path = p
            break

    # If no existing file found, try creating it
    if not found_path:
        try:
            found_path = export_cases_to_csv(csv_path)
        except Exception:
            found_path = None

    seeded_count = 0

    if found_path and os.path.exists(found_path):
        with open(found_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                case_id = row["case_id"]
                existing = db.query(Case).filter(Case.case_id == case_id).first()
                
                try:
                    topology = json.loads(row.get("network_topology", "{}"))
                except Exception:
                    topology = {}
                    
                try:
                    configs = json.loads(row.get("raw_configs", "{}"))
                except Exception:
                    configs = {}

                if existing:
                    existing.title = row["title"]
                    existing.description = f"{row.get('description', '')}\nSymptoms: {row.get('symptoms', '')}\nCategory: {row.get('category', '')}"
                    existing.network_topology = topology
                    existing.raw_configs = configs
                else:
                    new_case = Case(
                        case_id=case_id,
                        title=row["title"],
                        description=f"{row.get('description', '')}\nSymptoms: {row.get('symptoms', '')}\nCategory: {row.get('category', '')}",
                        network_topology=topology,
                        raw_configs=configs,
                        status="OPEN"
                    )
                    db.add(new_case)
                    seeded_count += 1
    else:
        # Fallback directly to in-memory CASES_DATA
        for case in CASES_DATA:
            case_id = case["case_id"]
            existing = db.query(Case).filter(Case.case_id == case_id).first()
            if existing:
                existing.title = case["title"]
                existing.description = f"{case.get('description', '')}\nSymptoms: {case.get('symptoms', '')}\nCategory: {case.get('category', '')}"
                existing.network_topology = case.get("network_topology", {})
                existing.raw_configs = case.get("raw_configs", {})
            else:
                new_case = Case(
                    case_id=case_id,
                    title=case["title"],
                    description=f"{case.get('description', '')}\nSymptoms: {case.get('symptoms', '')}\nCategory: {case.get('category', '')}",
                    network_topology=case.get("network_topology", {}),
                    raw_configs=case.get("raw_configs", {}),
                    status="OPEN"
                )
                db.add(new_case)
                seeded_count += 1

    db.commit()
    return seeded_count
