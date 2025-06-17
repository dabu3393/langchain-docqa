"""Document ingestion and processing."""

import argparse
import os
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langsmith import traceable

from app.utils.file_loader import load_document
from app.utils.load_env import load_env
from app.vector_store import get_vectordb

load_env()


@traceable(name="File Ingestion")
def ingest_single_file(file_path: str) -> dict:
    """Process and ingest a single document file.

    Args:
        file_path: Path to the file to ingest

    Returns:
        A dictionary containing the filename and number of chunks added
    """
    filename = Path(file_path).name

    vectordb = get_vectordb()

    existing_docs = vectordb.similarity_search(" ", k=100)
    already_ingested = any(
        doc.metadata.get("source") == filename for doc in existing_docs
    )

    if already_ingested:
        print(
            f"File '{filename}' already exists in the vector store. Skipping ingestion."
        )
        return "duplicate"

    try:
        document = load_document(file_path)
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(document)
        for chunk in chunks:
            chunk.metadata["source"] = filename

        vectordb.add_documents(chunks)

        return {"filename": os.path.basename(file_path), "chunks_added": len(chunks)}
    except Exception as e:
        print(f"Failed to process {file_path}: {str(e)}")
        return 0


@traceable(name="Batch Ingestion")
def ingest_files(file_paths: list) -> list:
    """Process and ingest multiple document files.

    Args:
        file_paths: List of file paths to ingest

    Returns:
        List of ingestion results for each file
    """
    results = []
    for file_path in file_paths:
        result = ingest_single_file(file_path)
        results.append(result)
    return results


@traceable(name="Directory Ingestion")
def ingest_directory(directory_path: str) -> list:
    """Process and ingest all documents from a directory.

    Args:
        directory_path: Path to the directory containing files to ingest

    Returns:
        List of ingestion results for all files
    """
    file_paths = [os.path.join(directory_path, f) for f in os.listdir(directory_path)]
    return ingest_files(file_paths)


def ingest_documents_from_directory(directory_path):
    """Process and ingest all documents from a directory.

    Args:
        directory_path: Path to the directory containing files to ingest

    Returns:
        List of chunks for all files
    """
    all_chunks = []

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        if not os.path.isfile(file_path):
            continue

        try:
            document = load_document(file_path)
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = splitter.split_documents(document)
            filename = Path(file_path).name
            for chunk in chunks:
                chunk.metadata["source"] = filename
            all_chunks.extend(chunks)
            print(f"Ingested {len(chunks)} chunks from {filename}")
        except Exception as e:
            print(f"Failed to process {filename}: {str(e)}")

    return all_chunks


def main(directory):
    """Main entry point for the script.

    Args:
        directory: Path to the directory containing files to ingest
    """
    chunks = ingest_documents_from_directory(directory)

    if not chunks:
        print("No chunks ingested. Exiting.")
        return

    print(f"Vector store updated with {len(chunks)} total chunks.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest multiple documents into a vector store."
    )
    parser.add_argument(
        "--dir",
        type=str,
        default="test_files",
        help="Directory containing documents to ingest.",
    )
    args = parser.parse_args()
    main(args.dir)
