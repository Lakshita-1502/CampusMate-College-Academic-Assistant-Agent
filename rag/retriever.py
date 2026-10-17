"""Search the persisted local Chroma document index."""
from pathlib import Path
from langchain_chroma import Chroma
from rag.embeddings import get_embeddings
from utils.config import settings


def retrieve(query: str, k: int = 4) -> list:
    if not (settings.vectorstore_dir / "chroma.sqlite3").exists():
        raise FileNotFoundError("Document index is missing. Run `python ingest.py` first.")
    store = Chroma(persist_directory=str(settings.vectorstore_dir), embedding_function=get_embeddings(), collection_name="campusmate")
    return store.similarity_search(query, k=k)
