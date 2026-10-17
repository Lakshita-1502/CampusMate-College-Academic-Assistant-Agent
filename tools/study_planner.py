"""Simple weighted study plan generator with deterministic output."""
from datetime import date, timedelta


def generate_study_plan(subjects: list[str], days: int, hours_per_day: float, priorities: dict[str, float] | None = None, completed_topics: dict[str, list[str]] | None = None) -> list[dict]:
    subjects = [s.strip() for s in subjects if s and s.strip()]
    if not subjects or len(subjects) > 12:
        raise ValueError("Provide between 1 and 12 subjects.")
    if not isinstance(days, int) or not 1 <= days <= 60:
        raise ValueError("Days remaining must be a whole number from 1 to 60.")
    if not 0.5 <= float(hours_per_day) <= 16:
        raise ValueError("Study hours per day must be between 0.5 and 16.")
    weights = {s: max(0.1, float((priorities or {}).get(s, 1))) for s in subjects}
    slots = max(1, round(hours_per_day * 2))  # half-hour blocks
    schedule = []
    start = date.today()
    for day_index in range(days):
        sessions = []
        for slot in range(slots):
            subject = max(subjects, key=lambda s: (weights[s] / (1 + sum(x["subject"] == s for x in sessions)), -subjects.index(s)))
            topics = (completed_topics or {}).get(subject, [])
            topic_hint = "Review and practice" if not topics else f"Continue after: {topics[-1]}"
            begin_minutes = 9 * 60 + slot * 30
            end_minutes = begin_minutes + 30
            sessions.append({"time": f"{begin_minutes//60:02d}:{begin_minutes%60:02d}–{end_minutes//60:02d}:{end_minutes%60:02d}", "subject": subject, "task": topic_hint})
        schedule.append({"day": day_index + 1, "date": (start + timedelta(days=day_index)).isoformat(), "sessions": sessions})
    return schedule
