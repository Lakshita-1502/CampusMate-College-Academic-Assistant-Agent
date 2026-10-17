"""Read PDF/TXT/Markdown files, split them, and persist a Chroma index."""
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import fitz

from rag.embeddings import get_embeddings
from utils.config import settings


def load_documents(folder: Path | None = None) -> list[Document]:
    folder = folder or settings.data_dir
    documents = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            with fitz.open(path) as pdf:
                for page_no, page in enumerate(pdf, start=1):
                    text = page.get_text().strip()
                    if text:
                        documents.append(Document(page_content=text, metadata={"source": path.name, "page": page_no, "section": path.stem.replace("_", " ").title()}))
        elif suffix in {".txt", ".md"}:
            text = path.read_text(encoding="utf-8").strip()
            if text:
                documents.append(Document(page_content=text, metadata={"source": path.name, "page": 1, "section": path.stem.replace("_", " ").title()}))
    return documents


def ingest(folder: Path | None = None) -> int:
    docs = load_documents(folder)
    if not docs:
        raise FileNotFoundError(f"No PDF, TXT, or Markdown documents found in {folder or settings.data_dir}.")
    chunks = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100).split_documents(docs)
    settings.vectorstore_dir.mkdir(parents=True, exist_ok=True)
    embeddings = get_embeddings()
    # Rebuild the named collection instead of appending duplicate chunks on each run.
    existing = Chroma(persist_directory=str(settings.vectorstore_dir), embedding_function=embeddings, collection_name="campusmate")
    existing.delete_collection()
    Chroma.from_documents(chunks, embeddings, persist_directory=str(settings.vectorstore_dir), collection_name="campusmate")
    return len(chunks)


if __name__ == "__main__":
    try:
        count = ingest()
        print(f"Indexed {count} chunks in {settings.vectorstore_dir}")
    except Exception as exc:
        raise SystemExit(f"Ingestion failed: {exc}")
