from app.utils.load_env import load_env
from app.vector_store import get_vectordb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from app.utils.file_loader import load_document
from langsmith import traceable
import os
import argparse
from pathlib import Path

load_env()

@traceable(name="Document Ingestion")
def ingest_single_file(file_path):
    filename = Path(file_path).name

    vectordb = get_vectordb()

    existing_docs = vectordb.similarity_search(" ", k=100)
    already_ingested = any(doc.metadata.get("source") == filename for doc in existing_docs)
    
    if already_ingested:
        print(f"File '{filename}' already exists in the vector store. Skipping ingestion.")
        return "duplicate"
    
    try:
        document = load_document(file_path)
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(document)
        for chunk in chunks:
            chunk.metadata["source"] = filename

        vectordb.add_documents(chunks)

        return {
            "filename": os.path.basename(file_path),
            "chunks_added": len(chunks)
        }
    except Exception as e:
        print(f"Failed to process {file_path}: {str(e)}")
        return 0

def ingest_documents_from_directory(directory_path):
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
    chunks = ingest_documents_from_directory(directory)

    if not chunks:
        print("No chunks ingested. Exiting.")
        return

    vectordb = get_vectordb()
    
    print(f"Vector store updated with {len(chunks)} total chunks.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest multiple documents into a vector store.")
    parser.add_argument("--dir", type=str, default="test_files", help="Directory containing documents to ingest.")
    args = parser.parse_args()
    main(args.dir)
