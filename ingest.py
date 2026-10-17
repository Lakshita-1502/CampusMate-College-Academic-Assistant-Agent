"""Project-root convenience entry point for document ingestion."""
from rag.ingest import ingest
from utils.config import settings


if __name__ == "__main__":
    try:
        count = ingest()
        print(f"Indexed {count} chunks in {settings.vectorstore_dir}")
    except Exception as exc:
        raise SystemExit(f"Ingestion failed: {exc}")
