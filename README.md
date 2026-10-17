# CampusMate — College Academic Assistant Agent

CampusMate is a small, local-first academic assistant for demonstrating agentic AI, LangGraph routing, retrieval-augmented generation (RAG), ChromaDB, Sentence Transformers, Ollama, Python tools, and Streamlit. It requires no paid API or OpenAI key.

> **Sample data warning:** the included policies, calendar, timetable, placement guidance, and deadlines are fictional demonstration data. Replace them with college-approved documents before relying on answers as official information.

## Features

- LangGraph routes each query to the action that fits its intent.
- RAG retrieves relevant PDF, TXT, and Markdown document chunks from a local ChromaDB index and cites source filenames.
- Sentence Transformers creates local document embeddings.
- Ollama provides local generation for grounded document answers and general academic tutoring.
- Python tools calculate attendance, build study plans, and look up sample assignment deadlines.
- Streamlit provides chat history, suggested questions, source citations, and a short Agent Details trace.

## Project structure

```text
CampusMate/
├── app.py                     # Streamlit chat UI
├── ingest.py                  # Ingest documents into ChromaDB
├── requirements.txt
├── .env.example
├── data/                      # Fictional sample documents and deadlines
├── agent/                     # LangGraph state, intent routing, prompts, workflow
├── rag/                       # Embeddings, ingestion, retrieval
├── tools/                     # Attendance, deadlines, study plan
├── utils/                     # Configuration
└── vectorstore/               # Generated local Chroma index
```

## Architecture

```text
Student
   ↓
Streamlit UI
   ↓
LangGraph Agent
   ↓
 ┌──────────────┬───────────────┬────────────────┐
 ↓              ↓               ↓
RAG          Academic Tools   Ollama
 ↓              ↓               ↓
College       Attendance      General Academic
Documents     Study Plan      Q&A
              Deadline
 └──────────────┴───────────────┘
                 ↓
            Final Answer
```

The router normalizes common informal forms (such as `hrs`, `subj`, `whats`, and `min`) and applies readable intent rules to the user's goal and the information provided. Attendance only goes to the calculator for a calculation, personal class counts, or a numeric estimate; attendance policies go to RAG. Study requests are recognized from subjects, available time, exam timing, preparation, or scheduling language, even when the user does not say “study plan.” If planner details are missing, CampusMate asks for those details and keeps what the user already provided. Unclear personal attendance statements receive a short clarification question instead of an unsupported response.

## Setup

1. Install **Python 3.11 or newer**.
2. Install [Ollama](https://ollama.com/download), start it, and pull the default model:

   ```bash
   ollama pull llama3.2
   ```

3. Create and activate a virtual environment from the project directory:

   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   # Windows Command Prompt
   .venv\Scripts\activate.bat
   ```

4. Install packages and create the local configuration file:

   ```bash
   pip install -r requirements.txt
   Copy-Item .env.example .env   # PowerShell (use `cp .env.example .env` on macOS/Linux)
   ```

5. Index the sample documents and run the app:

   ```bash
   python ingest.py
   streamlit run app.py
   ```

The first embedding run may download the Sentence Transformers model. Configure `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `EMBEDDING_MODEL`, and data/index directories in `.env`. No online language model API is used.

### Add college documents

Place PDF, `.txt`, or `.md` files under `data/` and run `python ingest.py`. The loader records the document name and page number (for PDFs); the UI displays retrieved source filenames. Ingestion rebuilds the `campusmate` collection so rerunning it does not append duplicate chunks. If you remove or replace documents, rerun ingestion to refresh the index.

## Example questions

- What is the minimum attendance requirement?
- What are the examination rules?
- I attended 36 out of 50 classes. Calculate my attendance.
- I have exams in 10 days and 4 subjects. I can study 3 hours per day. Create a study plan.
- When is the NLP assignment due?
- What documents are required for placement registration?
- What is the weather today? (This should be declined as unsupported live information.)

## How RAG works

1. `ingest.py` reads document text and PDF pages.
2. A text splitter creates overlapping chunks and keeps source metadata.
3. Sentence Transformers embeds each chunk and ChromaDB stores the vectors locally.
4. The agent embeds a college-information question and retrieves relevant chunks.
5. Ollama answers using only the retrieved excerpts. If the information is missing, CampusMate says: “I couldn't find this information in the available college documents.”
6. The UI shows the source filenames from retrieval metadata.

## How LangGraph routing works

The graph begins with an `understand` node that records the query intent. Conditional edges route to `attendance`, `study_plan`, `deadline`, `rag`, `general`, `unsupported`, or `clarify`. Each route node returns an answer and a short high-level trace. The Streamlit “Agent Details” panel shows the chosen route and action without exposing hidden reasoning.

Routing priority:

1. Clear attendance calculation
2. Study planning request
3. Deadline lookup
4. College policy/document question
5. General academic tutoring
6. Unsupported live/current information

The live-information guard prevents requests such as current weather, stock prices, or today's cricket score from being treated as ordinary academic questions. Vague personal attendance input can use the `clarify` route.

## Why this demonstrates agentic AI

```text
Traditional chatbot:  Question → LLM → Answer

CampusMate:           Question
                         ↓
                    LangGraph route
                 ↙       ↓        ↘
               RAG     Python tool   Ollama
                 ↘       ↓        ↙
                     Final answer
```

CampusMate selects a route before answering. Policy questions are grounded in documents, attendance is calculated in Python, study plans are generated by a planner, deadlines are looked up in structured sample data, and general academic explanations are generated locally with Ollama.

## Error handling and limitations

- The sidebar checks that Ollama is reachable and that the configured model is installed.
- If Ollama is unavailable, the UI shows startup and model-pull guidance.
- A missing Chroma index tells the user to run `python ingest.py`.
- Empty questions, invalid attendance inputs, incomplete study-plan details, and unknown deadlines produce readable messages.
- Sample academic policies and deadlines are fictional; verify official college rules and dates separately.
- Live web information is outside the supported scope.

## Course concepts

| Concept | Where it appears | What to demonstrate |
| --- | --- | --- |
| Agentic AI | `agent/graph.py`, `agent/router.py` | The query is routed to a task-specific action |
| LangGraph | `agent/graph.py`, `agent/state.py` | StateGraph nodes and conditional edges |
| RAG | `rag/`, `data/` | Relevant college document chunks and source citations |
| ChromaDB | `rag/ingest.py`, `rag/retriever.py` | Persistent local vector index |
| Sentence Transformers | `rag/embeddings.py` | Local document/query embeddings |
| Ollama | `agent/graph.py`, `utils/config.py` | Local, grounded answer generation and tutoring |
| Tool calling | `tools/` | Attendance math, study schedule, deadline lookup |
| Streamlit | `app.py` | Chat UI, history, examples, route trace |

## Manual test cases

After setup and ingestion, test these in the chat. The route can be checked in the Agent Details expander.

| Input | Expected route / result |
| --- | --- |
| What is the minimum attendance requirement? | RAG; answer from `attendance_policy.md` and cite the source. |
| I attended 36 out of 50 classes. Calculate my attendance. | Attendance Calculator; 72%, with 6 classes needed for 75%. |
| What is the attendance policy? | RAG. |
| How many classes do I need to attend to reach 75%? | Attendance Calculator; asks for current attended/total counts if they were not supplied. |
| What percentage attendance is required? | RAG. |
| I attended 40 out of 50 classes. What is my attendance percentage? | Attendance Calculator; 80%. |
| I have exams in 10 days and 4 subjects. Create a study plan. | Study Plan Tool; structured 10-day schedule. |
| When is the NLP assignment due? | Deadline Tool; sample date `2026-10-05`. |
| Explain what NLP is. | General / Ollama. |
| What is the weather today? | Unsupported; no live-data claim. |

The routing and deterministic tool regression tests can also be run with the standard library:

```bash
python -m unittest discover -v
```

## Faculty Demonstration Guide (5 minutes)

1. **0:00–0:40 — Start the app.** Show Ollama ready with `llama3.2`, then open Streamlit. Explain that the model and embeddings run locally.
2. **0:40–1:30 — Demonstrate RAG.** Ask “What is the minimum attendance requirement?” Show the 75% answer, `attendance_policy.md` citation, and Agent Route: RAG.
3. **1:30–2:15 — Contrast routing.** Ask “What is the attendance policy?” and show it also uses RAG. Then ask “I attended 36 out of 50 classes. Calculate my attendance.” Show the Attendance Calculator route and 72% result.
4. **2:15–3:10 — Demonstrate the study planner.** Ask for a 10-day plan with four subjects and three hours per day. Show the schedule and Study Plan Tool action.
5. **3:10–3:50 — Demonstrate deadlines.** Ask “When is the NLP assignment due?” Show the sample date and explain the data is fictional.
6. **3:50–4:30 — Demonstrate local Ollama.** Ask “Explain what NLP is.” Show the General / Ollama route and describe local generation.
7. **4:30–5:00 — Summarize LangGraph.** Point to the `understand` node and conditional edges in `agent/graph.py`. Explain that the Agent Details trace reveals the selected action without showing private reasoning.
