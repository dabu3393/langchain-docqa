from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredMarkdownLoader
from pathlib import Path

def load_document(file_path):
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".md":
        loader = UnstructuredMarkdownLoader(file_path)
    elif ext == ".txt":
        loader = TextLoader(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    documents = loader.load()

    # Add metadata
    source = Path(file_path).name
    for doc in documents:
        doc.metadata["source"] = source
    
    return documents