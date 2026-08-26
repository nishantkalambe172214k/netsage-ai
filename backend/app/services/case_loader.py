import csv
import json
import os
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.case import Case
from app.services.seed_data import export_cases_to_csv, CASES_DATA


def seed_cases(db: Session, csv_path: str = "data/cases.csv") -> int:
    """Seeds the SQLite database with cases from CSV or in-memory definitions."""
    # Ensure CSV exists
    if not os.path.exists(csv_path):
        export_cases_to_csv(csv_path)

    seeded_count = 0
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_id = row["case_id"]
            existing = db.query(Case).filter(Case.case_id == case_id).first()
            
            # Parse JSON fields safely
            try:
                topology = json.loads(row.get("network_topology", "{}"))
            except Exception:
                topology = {}
                
            try:
                configs = json.loads(row.get("raw_configs", "{}"))
            except Exception:
                configs = {}

            if existing:
                # Update existing case
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

    db.commit()
    return seeded_count
