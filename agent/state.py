from typing import TypedDict, Any


class AgentState(TypedDict, total=False):
    query: str
    intent: str
    route_label: str
    action: str
    answer: str
    sources: list[str]
    details: dict[str, Any]
    error: str
