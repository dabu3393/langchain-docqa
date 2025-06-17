from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import os
import shutil

VECTOR_STORE_DIR = "vector_store"
_vectordb = None  # Global singleton


def get_embeddings():
    return OpenAIEmbeddings()


def get_vectordb():
    """Initialize and return the Chroma vector store (singleton)."""
    global _vectordb
    if _vectordb is None:
        _vectordb = Chroma(
            persist_directory=VECTOR_STORE_DIR,
            embedding_function=get_embeddings()
        )
    return _vectordb


def reset_vectordb():
    """Deletes all vector store files and uploaded documents."""
    global _vectordb

    # Clear vector store
    if os.path.exists(VECTOR_STORE_DIR):
        shutil.rmtree(VECTOR_STORE_DIR)

    # Clear uploaded docs
    upload_dir = "uploaded_docs"
    if os.path.exists(upload_dir):
        for f in os.listdir(upload_dir):
            os.remove(os.path.join(upload_dir, f))

    _vectordb = None  # Clear reference so it's reinitialized on next use
