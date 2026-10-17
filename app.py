"""CampusMate Streamlit chat interface."""
from urllib.parse import urlparse
from urllib.request import urlopen
import json

import streamlit as st

from agent.graph import ask
from utils.config import settings

st.set_page_config(page_title="CampusMate", page_icon="🎓", layout="centered")


@st.cache_data(ttl=10)
def ollama_status() -> tuple[bool, str]:
    parsed = urlparse(settings.ollama_base_url)
    try:
        with urlopen(settings.ollama_base_url.rstrip("/") + "/api/tags", timeout=1.5) as response:
            models = json.loads(response.read().decode("utf-8")).get("models", [])
        installed = {model.get("name", "") for model in models}
        base_model = settings.model.split(":", 1)[0]
        if not any(name == settings.model or name.split(":", 1)[0] == base_model for name in installed):
            return False, f"Ollama is running, but `{settings.model}` is not installed. Run `ollama pull {settings.model}`."
        return True, f"Ollama is ready · {settings.model}"
    except OSError:
        return False, f"Ollama is not running at {settings.ollama_base_url}. Start Ollama, then run `ollama pull {settings.model}`."
    except (ValueError, json.JSONDecodeError):
        return False, "Ollama responded with an unexpected status. Check the configured OLLAMA_BASE_URL."


EXAMPLES = [
    "What is the minimum attendance requirement?",
    "What are the examination rules?",
    "I attended 36 out of 50 classes. Calculate my attendance.",
    "I have exams in 10 days and 4 subjects. I can study 3 hours per day. Create a study plan.",
    "When is the NLP assignment due?",
    "What documents are required for placement registration?",
]

with st.sidebar:
    st.title("🎓 CampusMate")
    st.caption("AI Academic Assistant")
    st.markdown("**Features**\n\n- College document Q&A\n- RAG retrieval\n- Attendance calculator\n- Study planner\n- Deadline lookup\n- Local LLM using Ollama")
    st.divider()
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.caption(f"Model: `{settings.model}` · Local Ollama")
    ok, status = ollama_status()
    (st.success if ok else st.warning)(status)

st.title("🎓 CampusMate")
st.subheader("College Academic Assistant Agent")
st.caption("Ask about sample college documents, calculate attendance, plan study time, or look up demo deadlines.")
st.info("The included college policies and dates are fictional sample data. Replace them with approved college documents before relying on them.", icon="ℹ️")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "suggested_query" not in st.session_state:
    st.session_state.suggested_query = ""

with st.expander("Try these examples", expanded=not st.session_state.messages):
    cols = st.columns(2)
    for i, example in enumerate(EXAMPLES):
        if cols[i % 2].button(example, key=f"example_{i}", use_container_width=True):
            st.session_state.suggested_query = example
            st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            st.markdown("**📚 Sources**")
            for source in message["sources"]:
                st.markdown(f"- `{source}`")
        if message.get("details"):
            with st.expander("Agent Details · How the agent handled this"):
                st.markdown(f"**Agent Route:** {message.get('route_label', 'Unknown')}  \n**Action:** {message.get('action', 'Completed request')}")
                st.json(message["details"])

prompt = st.chat_input("Ask CampusMate a question…")
if not prompt and st.session_state.suggested_query:
    prompt = st.session_state.suggested_query
    st.session_state.suggested_query = ""

if prompt is not None:
    if not prompt.strip():
        st.warning("Please enter a question.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("CampusMate is working…"):
                result = ask(prompt)
            st.markdown(result.get("answer", "I couldn't produce an answer. Please try again."))
            if result.get("sources"):
                st.markdown("**📚 Sources**")
                for source in result["sources"]:
                    st.markdown(f"- `{source}`")
            if result.get("details"):
                with st.expander("Agent Details · How the agent handled this"):
                    st.markdown(f"**Agent Route:** {result.get('route_label', 'Unknown')}  \n**Action:** {result.get('action', 'Completed request')}")
                    st.json(result.get("details", {}))
        st.session_state.messages.append({"role": "assistant", "content": result.get("answer", ""), "sources": result.get("sources", []), "route_label": result.get("route_label"), "action": result.get("action"), "details": result.get("details", {})})
