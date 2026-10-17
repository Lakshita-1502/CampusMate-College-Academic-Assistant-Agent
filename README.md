# CampusMate — College Academic Assistant Agent

CampusMate is a local-first academic assistant built with Python, LangGraph, RAG, ChromaDB, Sentence Transformers, Ollama, and Streamlit. It helps students retrieve information from college documents, calculate attendance, create study plans, and look up assignment deadlines.

> Note: The included academic policies and deadlines are fictional sample data. Replace them with verified college information before relying on the app.

## Features

- Routes user requests to the appropriate action using LangGraph.
- Retrieves relevant content from PDF, TXT, and Markdown files using RAG.
- Shows source filenames for document-based answers.
- Calculates attendance using Python.
- Generates study plans.
- Looks up deadlines from a sample academic dataset.
- Runs a local language model through Ollama.
- Provides a Streamlit chat interface.

## Technologies

- Python 3.11+
- LangGraph
- Ollama with Llama 3.2
- ChromaDB
- Sentence Transformers
- Streamlit

## Project Structure

```
CampusMate/
├── app.py              # Streamlit interface
├── ingest.py           # Indexes documents in ChromaDB
├── requirements.txt
├── .env.example
├── data/               # Documents and sample academic data
├── agent/              # Agent workflow and routing
├── rag/                # Document ingestion and retrieval
├── tools/              # Attendance, study plan, and deadline tools
├── utils/              # Configuration
└── vectorstore/        # Generated local ChromaDB index
```

## Setup and Run

### 1. Clone the Repository

Install Git, then run:

```
git clone <repository-url>
cd CampusMate
```

Replace `<repository-url>` with the URL of your GitHub repository. If the cloned folder has a different name, use that folder name in the `cd` command.

### 2. Install Python and Ollama

Install Python 3.11 or newer from [python.org](https://www.python.org/downloads/?utm_source=chatgpt.com) and Ollama from [ollama.com](https://ollama.com/download?utm_source=chatgpt.com).

Download the model:

```
ollama pull llama3.2
```

Make sure Ollama is running before launching the app.

### 3. Create a Virtual Environment

```
python -m venv .venv
```

Activate it using the appropriate command.

Windows PowerShell

```
.venv\Scripts\Activate.ps1
```

Windows Command Prompt

```
.venv\Scripts\activate.bat
```

macOS/Linux

```
source .venv/bin/activate
```

### 4. Install Dependencies and Configure

Install the required packages:

```
pip install -r requirements.txt
```

Create the local configuration file.

Windows PowerShell

```
Copy-Item .env.example .env
```

macOS/Linux

```
cp .env.example .env
```

Edit `.env` only if you need to change the model or configuration settings.

### 5. Index Documents and Start the App

```
python ingest.py
streamlit run app.py
```

Open the local URL shown in the terminal.

The first indexing run may download the Sentence Transformers embedding model.

## Add College Documents

Place PDF, TXT, or Markdown files in the `data/` directory, then rebuild the index:

```
python ingest.py
```

Run ingestion again whenever documents are added, replaced, or removed.

## Limitations

- The included academic documents and deadlines are sample data, not official college information.
- Answers depend on the quality and completeness of the available documents.
- Live information, such as current weather or scores, is outside the app's supported scope.
- The app requires Ollama and the configured model to be available locally.