"""Attendance calculations using plain Python arithmetic."""
from math import ceil


def calculate_attendance(attended: int, total: int, target: float = 75.0) -> dict:
    if isinstance(attended, bool) or isinstance(total, bool):
        raise ValueError("Class counts must be whole numbers.")
    if attended < 0 or total <= 0 or attended > total:
        raise ValueError("Enter class counts where 0 <= attended <= total and total is above zero.")
    if not 0 < target <= 100:
        raise ValueError("Target percentage must be above 0 and at most 100.")
    percentage = attended / total * 100
    if percentage >= target:
        needed = 0
    elif target == 100:
        # If classes have already been missed, attending finite future classes
        # can approach but never reach exactly 100%.
        needed = None
    else:
        needed = max(0, ceil((target * total - 100 * attended) / (100 - target) - 1e-12))
    return {"attended": attended, "total": total, "target": target, "percentage": percentage, "classes_needed": needed}
