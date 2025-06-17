"""Vector store management for document embeddings."""

import os
import shutil

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

VECTOR_STORE_DIR = "vector_store"
_VECTORDB = None  # Global singleton


def get_embeddings():
    """Initialize OpenAI embeddings."""
    return OpenAIEmbeddings()


def get_vectordb():
    """Get or create the vector store instance."""
    global _VECTORDB
    if _VECTORDB is None:
        _VECTORDB = Chroma(
            persist_directory=VECTOR_STORE_DIR, embedding_function=get_embeddings()
        )
    return _VECTORDB


def reset_vectordb():
    """Clean up the vector store and uploaded documents."""
    global _VECTORDB

    # Clear vector store
    if os.path.exists(VECTOR_STORE_DIR):
        shutil.rmtree(VECTOR_STORE_DIR)

    # Clear uploaded docs
    upload_dir = "uploaded_docs"
    if os.path.exists(upload_dir):
        for f in os.listdir(upload_dir):
            os.remove(os.path.join(upload_dir, f))

    _VECTORDB = None  # Clear reference so it's reinitialized on next use


def cleanup():
    """Remove the vector store directory."""
    if os.path.exists(VECTOR_STORE_DIR):
        shutil.rmtree(VECTOR_STORE_DIR)


def exists():
    """Check if vector store directory exists."""
    return os.path.exists(VECTOR_STORE_DIR)
