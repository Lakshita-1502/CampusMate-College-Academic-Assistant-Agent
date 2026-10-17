"""Demo assignment deadlines. Replace these clearly marked sample records locally."""
from datetime import date
import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "sample_academic_data.json"


def _assignments() -> list[dict]:
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data.get("assignments", [])
    except (OSError, json.JSONDecodeError):
        return []


def get_assignment_deadline(subject: str) -> dict:
    query = subject.strip().casefold()
    if not query:
        return {"found": False, "message": "Enter an assignment or subject name."}
    matches = [item for item in _assignments() if query in item["subject"].casefold() or item["subject"].casefold() in query or query in item["title"].casefold()]
    if not matches:
        return {"found": False, "message": f"No sample deadline matched '{subject}'."}
    return {"found": True, "deadlines": matches, "demo_data": True}


def days_until(iso_date: str) -> int:
    return (date.fromisoformat(iso_date) - date.today()).days
