"""File loading utilities for document processing."""

from pathlib import Path

from langchain_community.document_loaders import (PyPDFLoader, TextLoader,
                                                  UnstructuredMarkdownLoader)


def load_document(file_path: str) -> list:
    """Load and process a document file.

    Args:
        file_path: Path to the file to load

    Returns:
        List of document chunks
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext in [".txt", ".md"]:
        if ext == ".md":
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            loader = TextLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    documents = loader.load()

    # Add metadata
    source = Path(file_path).name
    for doc in documents:
        doc.metadata["source"] = source

    return documents
