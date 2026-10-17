"""Application settings loaded from environment variables or a local .env."""
from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    model: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    data_dir: Path = ROOT / os.getenv("DATA_DIR", "data")
    vectorstore_dir: Path = ROOT / os.getenv("VECTORSTORE_DIR", "vectorstore/chroma")
    attendance_target: float = float(os.getenv("ATTENDANCE_TARGET", "75"))


settings = Settings()
