"""Small parsers that extract tool inputs from normalized natural language."""
import re


def attendance_counts(query: str) -> tuple[int | None, int | None]:
    """Return attended/total counts without mistaking percentages for counts."""
    missed_out_of = re.search(r"\bmiss(?:ed)?\s+(\d+)\s+(?:classes?\s+)?out of\s+(\d+)\b", query)
    if missed_out_of:
        missed, total = map(int, missed_out_of.groups())
        return total - missed, total

    attended_and_missed = re.search(r"\b(?:attended|went to|attend)\s+(\d+)\s+classes?\b.*?\bmiss(?:ed)?\s+(\d+)\b", query)
    if attended_and_missed:
        attended, missed = map(int, attended_and_missed.groups())
        return attended, attended + missed

    attended_out_of = re.search(r"\b(?:attended|attend|went to|have)\s+(\d+)\s+(?:classes?\s+)?(?:out of|/)\s*(\d+)\b", query)
    if attended_out_of:
        return tuple(map(int, attended_out_of.groups()))

    fraction = re.search(r"\b(\d+)\s*/\s*(\d+)\b", query)
    if fraction:
        return tuple(map(int, fraction.groups()))
    count_phrase = re.search(r"\b(\d+)\s+classes?\s+out of\s+(\d+)\b", query)
    if count_phrase:
        return tuple(map(int, count_phrase.groups()))
    return None, None


def study_subjects(query: str) -> list[str]:
    count = re.search(r"(\d+)\s+subjects?\b", query, re.I)
    if count:
        return [f"Subject {i}" for i in range(1, min(int(count.group(1)), 12) + 1)]
    match = re.search(r"\bsubjects?\s*(?:are|include|:)?\s+(.+?)(?:\.|$)", query, re.I)
    if match:
        names = [item.strip(" ,.") for item in re.split(r",|\band\b|\&", match.group(1))]
        names = [item for item in names if item and not re.search(r"\d+\s*(?:days?|weeks?|hours?)", item)]
        if names:
            return names[:12]
    match = re.search(
        r"\bfor\s+([A-Za-z][A-Za-z0-9 +,&-]*?)(?=\s+\d+\s*(?:days?|weeks?|hours?)|"
        r"\s+and\s+\d+\s*(?:days?|weeks?|hours?)|[.!?]|$)",
        query,
        re.I,
    )
    if match and not re.match(r"\d", match.group(1).strip()):
        names = [item.strip(" ,.") for item in re.split(r",|\band\b|\&", match.group(1))]
        names = [item for item in names if item and item.casefold() not in {"the next", "study"}]
        if names:
            return names[:12]
    return []


def study_days(query: str) -> int | None:
    match = re.search(r"\b(\d+)\s+days?\b", query)
    if match:
        return int(match.group(1))
    match = re.search(r"\b(\d+)\s+weeks?\b", query)
    if match:
        return int(match.group(1)) * 7
    match = re.search(r"\b(\d+)\s+months?\b", query)
    if match:
        return int(match.group(1)) * 30
    if re.search(r"\bnext month|in a month|one month\b", query):
        return 30
    return None


def study_hours(query: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*hours?\b", query, re.I)
    return float(match.group(1)) if match else None


def study_inputs(query: str) -> dict:
    """Extract the planner's available inputs from an already normalized query."""
    return {"subjects": study_subjects(query), "days": study_days(query), "hours_per_day": study_hours(query)}
