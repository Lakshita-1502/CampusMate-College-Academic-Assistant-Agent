"""LangGraph workflow: route to RAG, an academic tool, or Ollama."""
import re

from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph

from agent.prompts import GENERAL_SYSTEM, RAG_SYSTEM
from agent.parsing import attendance_counts, study_inputs
from agent.router import classify, normalize_query
from agent.state import AgentState
from rag.retriever import retrieve
from tools.attendance import calculate_attendance
from tools.deadlines import get_assignment_deadline
from tools.study_planner import generate_study_plan
from utils.config import settings


def _llm():
    return ChatOllama(model=settings.model, base_url=settings.ollama_base_url, temperature=0.1)


def understand(state: AgentState) -> AgentState:
    return {"intent": classify(state["query"]), "details": {"query": state["query"]}}


def attendance_node(state: AgentState) -> AgentState:
    q = normalize_query(state["query"])
    try:
        percentages = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*%", q)]
        if len(percentages) >= 2:
            target = percentages[-1]
        elif percentages and re.search(r"\b(reach|target|maintain|need)\b", q):
            target = percentages[0]
        else:
            target = settings.attendance_target

        attended, total = attendance_counts(q)
        if attended is None or total is None:
            raise ValueError("Please include attended and total classes, such as 36 out of 50. A percentage-only estimate also needs the total class count.")

        result = calculate_attendance(attended, total, target)
        wants_miss_estimate = bool(re.search(r"\bhow many\s+(?:more\s+)?classes? can i miss\b", q))
        if wants_miss_estimate:
            allowed = max(0, int(attended / (target / 100) - total)) if target < 100 else 0
            answer = f"Current attendance: {result['percentage']:.1f}%. You can miss approximately {allowed} upcoming classes and remain at or above {target:g}%."
        else:
            answer = f"Current attendance: {result['percentage']:.1f}%."
            if result["classes_needed"] is None:
                answer += " A 100% target cannot be reached after an absence by attending a finite number of additional classes."
            elif result["classes_needed"]:
                answer += f" Attend {result['classes_needed']} consecutive classes to reach {target:g}% (approximately)."
            else:
                answer += f" You have reached the {target:g}% target."
        return {"answer": answer, "details": {"tool": "calculate_attendance", "result": result}}
    except (ValueError, OverflowError) as exc:
        return {"answer": f"I couldn't calculate that: {exc}", "details": {"tool": "calculate_attendance", "error": str(exc)}}


def study_node(state: AgentState) -> AgentState:
    q = normalize_query(state["query"])
    inputs = study_inputs(q)
    subjects = inputs["subjects"]
    days = inputs["days"]
    hours = inputs["hours_per_day"]
    try:
        missing = []
        if not subjects:
            missing.append("the number or names of your subjects")
        if not days:
            missing.append("how many days you have")
        if not hours:
            missing.append("your available study hours per day")
        if missing:
            understood = []
            if subjects:
                understood.append(f"{len(subjects)} subject(s)")
            if days:
                understood.append(f"{days} days")
            if hours:
                understood.append(f"{hours:g} hours per day")
            context = " I understood " + ", ".join(understood) + "." if understood else ""
            answer = "I can help build your study plan." + context + " Please tell me " + ", ".join(missing) + "."
            return {"answer": answer, "details": {"tool": "generate_study_plan", "missing": missing, "understood": understood}}

        plan = generate_study_plan(subjects, days, hours)
        lines = [f"Available study time: {days * hours:g} hours across {days} days."]
        for item in plan:
            lines.append(f"**Day {item['day']} — {item['date']}**")
            lines.extend(f"- {session['time']} · {session['subject']} — {session['task']}" for session in item["sessions"])
        return {"answer": "\n".join(lines), "details": {"tool": "generate_study_plan", "days": len(plan), "subjects": subjects}}
    except ValueError as exc:
        return {"answer": f"I couldn't create the plan: {exc}", "details": {"tool": "generate_study_plan", "error": str(exc)}}


def deadline_node(state: AgentState) -> AgentState:
    q = normalize_query(state["query"])
    subject = re.sub(r"\b(when|what is|the|my|last|date|assignment|deadline|due|for|submission|do i have to)\b", " ", q, flags=re.I).strip(" ?.! ")
    result = get_assignment_deadline(subject)
    if result["found"]:
        lines = [f"{item['title']} ({item['subject']}): {item['due_date']}" for item in result["deadlines"]]
        return {"answer": "DEMO/SAMPLE academic data: " + "; ".join(lines), "details": {"tool": "get_assignment_deadline", "result": result}}
    return {"answer": result["message"] + " These dates are demo data, so check your official course notices.", "details": {"tool": "get_assignment_deadline", "result": result}}


def rag_node(state: AgentState) -> AgentState:
    try:
        docs = retrieve(state["query"])
        query_terms = {word.casefold() for word in re.findall(r"[a-zA-Z]{4,}", state["query"])}
        relevant = [doc for doc in docs if len(query_terms & set(re.findall(r"[a-zA-Z]{4,}", doc.page_content.casefold()))) >= 1]
        if not relevant:
            return {"answer": "I couldn't find this information in the available college documents.", "sources": [], "details": {"retrieval": "No relevant excerpts found"}}
        context = "\n\n".join(f"[{doc.metadata.get('source')} page {doc.metadata.get('page', '?')}]\n{doc.page_content}" for doc in relevant)
        response = _llm().invoke([("system", RAG_SYSTEM), ("human", f"Question: {state['query']}\n\nCollege document excerpts:\n{context}")])
        sources = list(dict.fromkeys(doc.metadata.get("source", "Unknown document") for doc in relevant))
        return {"answer": str(response.content), "sources": sources, "details": {"retrieval": f"Retrieved {len(relevant)} excerpts"}}
    except FileNotFoundError as exc:
        return {"answer": str(exc), "error": str(exc), "details": {"retrieval": "Index unavailable"}}
    except Exception as exc:
        message = str(exc)
        if any(term in message.casefold() for term in ("ollama", "connection refused", "not found", "404")):
            answer = f"Ollama could not generate the document answer. Start Ollama and run `ollama pull {settings.model}`. Details: {message}"
        else:
            answer = f"Document search failed: {message}"
        return {"answer": answer, "error": message, "details": {"retrieval": "Search or generation error"}}


def general_node(state: AgentState) -> AgentState:
    try:
        answer = _llm().invoke([("system", GENERAL_SYSTEM), ("human", state["query"])])
        return {"answer": str(answer.content), "details": {"response": "Local Ollama academic response"}}
    except Exception as exc:
        return {"answer": f"Ollama is unavailable. Start Ollama and run `ollama pull {settings.model}`. Details: {exc}", "error": str(exc), "details": {"response": "Ollama unavailable"}}


def unsupported_node(state: AgentState) -> AgentState:
    return {"answer": "I can help with college documents, attendance, study planning, and assignment deadlines. I don't have current or general live information for this question.", "details": {"response": "Outside supported academic tasks"}}


def clarify_node(state: AgentState) -> AgentState:
    return {"answer": "Do you want me to calculate your attendance or look up the college attendance policy? For a calculation, share how many classes you attended and the total number of classes.", "details": {"response": "Clarification requested for ambiguous attendance intent"}}


def build_graph():
    graph = StateGraph(AgentState)
    nodes = {
        "understand": understand,
        "attendance": attendance_node,
        "study_plan": study_node,
        "deadline": deadline_node,
        "rag": rag_node,
        "general": general_node,
        "unsupported": unsupported_node,
        "clarify": clarify_node,
    }
    for name, function in nodes.items():
        graph.add_node(name, function)
    graph.add_edge(START, "understand")
    destinations = tuple(name for name in nodes if name != "understand")
    graph.add_conditional_edges("understand", lambda state: state["intent"], {name: name for name in destinations})
    for name in destinations:
        graph.add_edge(name, END)
    return graph.compile()


agent = build_graph()


def ask(query: str) -> AgentState:
    if not query.strip():
        return {"query": query, "answer": "Please enter a question.", "details": {"response": "Empty query"}}
    result = agent.invoke({"query": query.strip()})
    route_labels = {
        "rag": "RAG",
        "attendance": "Attendance Calculator",
        "study_plan": "Study Plan Tool",
        "deadline": "Deadline Tool",
        "general": "General / Ollama",
        "unsupported": "Unsupported",
        "clarify": "Clarification",
    }
    actions = {
        "rag": "Retrieved college documents",
        "attendance": "Calculated attendance",
        "study_plan": "Generated a study plan",
        "deadline": "Looked up academic deadlines",
        "general": "Answered with the local Ollama model",
        "unsupported": "Kept the response within the supported academic scope",
        "clarify": "Asked for the missing attendance intent and class counts",
    }
    result["route_label"] = route_labels[result["intent"]]
    result["action"] = actions[result["intent"]]
    return result
