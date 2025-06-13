from utils.load_env import load_env
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from utils.file_loader import load_document

load_env()

def ingest_file(file_path):
    # Load document
    document = load_document(file_path)
    
    # Split document
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(document)

    # Create embeddings
    embeddings = OpenAIEmbeddings()
    vectordb = Chroma.from_documents(chunks, embedding=embeddings, persist_directory="vector_store")
    vectordb.persist()
    
    print(f"Ingested {len(chunks)} chunks from {file_path}")


if __name__ == "__main__":
    test_file = "/Users/davisburrill/Documents/langchain-docqa/test_files/Avalanche.pdf" # Use a real file path
    ingest_file(test_file)
    
