"""Lightweight intent routing for natural, informal academic requests.

The router uses task intent and context instead of requiring canned phrases.
It intentionally stays local and readable so its decisions are easy to explain.
"""
import re


_NUMBER_WORDS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12", "fourteen": "14", "twenty": "20",
    "thirty": "30",
}


def normalize_query(query: str) -> str:
    """Normalize common chat spelling and abbreviations before routing/parsing."""
    q = query.casefold().replace("’", "'")
    q = re.sub(r"\bwhat's\b", "what is", q)
    q = re.sub(r"\bwhats\b", "what is", q)
    q = re.sub(r"\bi've\b", "i have", q)
    q = re.sub(r"\bcan\s+u\b", "can you", q)
    q = re.sub(r"\bsubj\b", "subjects", q)
    q = re.sub(r"(?<=\d)\s*hrs?\b|\bhrs?\b", " hours", q)
    q = re.sub(r"(?<=\d)h\b", " hours", q)
    q = re.sub(r"(?<=\d)[- ]?(days?|weeks?|months?)\b", r" \1", q)
    q = re.sub(r"\battendence\b|\batendance\b", "attendance", q)
    q = re.sub(r"\bpreperation\b", "preparation", q)
    q = re.sub(r"\bmin\b", "minimum", q)
    q = re.sub(r"\bn\b", "and", q)
    for word, digit in _NUMBER_WORDS.items():
        q = re.sub(rf"\b{word}(?=\s*(?:subjects?|days?|weeks?|hours?))", digit, q)
    return " ".join(q.split())


def _is_unsupported_live_query(q: str) -> bool:
    """Identify live or external requests this local academic app cannot answer."""
    external = re.search(
        r"\b(weather|stock|share price|bitcoin|crypto|news|cricket|match|score|traffic|forecast)\b",
        q,
    )
    live = re.search(r"\b(today|tonight|right now|currently|latest|live|current|tomorrow)\b", q)
    return bool(external and (live or re.search(r"\b(weather|bitcoin|crypto|stock price|share price)\b", q)))


def _is_attendance_calculation(q: str) -> bool:
    """Separate actual personal calculations from policy/eligibility questions."""
    attendance_context = bool(re.search(r"\b(attendance|attended|attend|classes?|missed|miss)\b", q))
    if not attendance_context:
        return False

    explicit_calculation = bool(re.search(r"\b(calculate|calculation|compute|work out|estimate)\b", q))
    numeric_record = bool(
        re.search(r"\b\d+\s*/\s*\d+\b", q)
        or re.search(r"\b(?:attended|attend|went to|missed|miss)\s+\d+\b", q)
        or re.search(r"\b\d+\s+(?:classes?\s+)?out of\s+\d+\b", q)
    )
    asks_class_estimate = bool(
        re.search(r"\bhow many\s+(?:(?:more|additional|extra)\s+)?classes?\b", q)
        and (re.search(r"\d+(?:\.\d+)?\s*%", q) or re.search(r"\bmiss\b", q))
    )
    personal_percent_goal = bool(
        re.search(r"\bmy attendance\b", q)
        and len(re.findall(r"\d+(?:\.\d+)?\s*%", q)) >= 2
    )
    return explicit_calculation or numeric_record or asks_class_estimate or personal_percent_goal


def _is_study_plan(q: str) -> bool:
    """Recognize planning intent from goals, timing, available time, or subjects."""
    has_subject_count = bool(re.search(r"\b\d+\s+subjects?\b", q))
    has_subjects = bool(re.search(r"\bsubjects?\b", q))
    has_duration = bool(re.search(r"\b\d+\s*(?:days?|weeks?|months?)\b|\bnext month\b", q))
    has_study_time = bool(re.search(r"\b\d+(?:\.\d+)?\s*hours?\b|\b(?:daily|every day|per day)\b", q))
    study_context = bool(re.search(r"\b(study|exam|exams|prepare|preparation|revision|revise|subjects?)\b", q))
    planning_action = bool(re.search(r"\b(plan|planning|prepare|preparation|organize|divide|distribute|schedule|timetable|revise|revision)\b", q))
    explicit_schedule = bool(re.search(r"\b(make|create|build|give|help|can you|could you)\b", q) and re.search(r"\b(schedule|timetable|study plan|revision plan)\b", q))

    # A subject count with a time horizon is an implicit preparation-planning request,
    # even when the message has no command or punctuation.
    if has_subject_count and has_duration:
        return True
    if explicit_schedule:
        return True
    if planning_action and (study_context or has_study_time):
        return True
    if has_study_time and study_context and (has_duration or planning_action or has_subjects):
        return True
    if has_duration and study_context and re.search(r"\bhow should i|how do i|help me|don't know|do not know\b", q):
        return True
    if has_duration and re.search(r"\bexam|exams|subjects?\b", q):
        return True
    if re.search(r"\bhow should i divide\b", q) and (has_study_time or has_subjects):
        return True
    return False


def _is_deadline_request(q: str) -> bool:
    explicit_date = bool(re.search(r"\b(deadline|due date|last date|submission)\b", q))
    due_with_task = bool(re.search(r"\bdue\b", q) and re.search(r"\b(when|assignment|project|homework|coursework|submit|submission)\b", q))
    has_submit_intent = bool(re.search(r"\b(submit|turn in|hand in)\b", q))
    asks_when = bool(re.search(r"\b(when|by when|what is the date|what's the date)\b", q))
    return explicit_date or due_with_task or (has_submit_intent and (asks_when or re.search(r"\bsoon|date|due\b", q)))


def _is_college_information(q: str) -> bool:
    """Recognize questions whose evidence should come from college documents."""
    college_context = bool(re.search(
        r"\b(college|campus|attendance|placement|internal assessment|exam|examination|"
        r"academic|student handbook|semester|assignment|coursework)\b", q
    ))
    policy_or_doc = bool(re.search(r"\b(policy|policies|regulation|rules?|requirements?|guidelines?|handbook)\b", q))
    needs_document = bool(
        re.search(r"\b(documents?|paperwork|guidelines?)\b", q)
        and re.search(r"\b(need|needs|required|require|what|which|tell me|mentioned|according to)\b", q)
    )
    academic_policy = policy_or_doc and bool(
        re.search(r"\b(college|campus|academic|student|attendance|exam|assessment)\b", q)
    )
    return college_context or academic_policy or needs_document


def classify(query: str) -> str:
    """Return the LangGraph node for the user's underlying task.

    Clear calculations and task-specific tools take priority. College policy
    questions remain in RAG even if they mention percentages or requirements.
    Unknown ordinary questions default to local academic tutoring; only clearly
    live/external requests are sent to the unsupported route.
    """
    q = normalize_query(query)
    if not q:
        return "unsupported"

    if re.search(r"\bmy attendance\b", q) and re.search(r"\b(low|bad|poor|not good)\b", q) and not _is_attendance_calculation(q):
        return "clarify"

    if _is_attendance_calculation(q):
        return "attendance"
    if _is_study_plan(q):
        return "study_plan"
    if _is_deadline_request(q):
        return "deadline"
    if _is_college_information(q):
        return "rag"
    if _is_unsupported_live_query(q):
        return "unsupported"

    # Treat unmatched educational questions and short concept prompts as general
    # tutoring rather than rejecting them for not resembling a sample question.
    if re.search(r"\b(what|who|why|how|which|explain|define|compare|difference|teach|help|tell me)\b", q):
        return "general"
    if re.search(r"\b(nlp|machine learning|artificial intelligence|\bai\b|tcp|udp|compiler|java|python|programming|math|science|biology|physics|history|economics)\b", q):
        return "general"
    return "unsupported"
