"""Local sentence-transformer embeddings."""
from langchain_huggingface import HuggingFaceEmbeddings
from utils.config import settings


def get_embeddings():
    return HuggingFaceEmbeddings(model_name=settings.embedding_model, model_kwargs={"device": "cpu"})
