from app.ingest import ingest_single_file
from app.vector_store import get_vectordb
from fastapi import FastAPI, Request, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.qa_chain import answer_question
from langchain_core.caches import InMemoryCache
from langchain.globals import set_llm_cache
import logging
import shutil
import os
import sys
import argparse
from typing import Set
from contextlib import asynccontextmanager

set_llm_cache(None)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Parse CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument("--fresh-start", action="store_true", help="Delete vector store on startup")
args, _ = parser.parse_known_args()

if args.fresh_start:
    vector_store_dir = "vector_store"
    if os.path.exists(vector_store_dir):
        shutil.rmtree(vector_store_dir)
        logger.info("🧹 Fresh start: Deleted vector store directory.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 FastAPI app has started and is ready to receive requests.")
    
    # Clean up reload trigger if it exists
    reload_trigger = ".reload"
    if os.path.exists(reload_trigger):
        os.remove(reload_trigger)
    
    get_vectordb()
    yield

app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str
    k: int = 4

# Store active WebSocket connections
active_connections: Set[WebSocket] = set()

@app.websocket("/ws/files")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            # Wait for any message (we don't actually need to process it)
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid input", "details": exc.errors()},
    )

@app.post("/ask")
def ask_question(payload: QuestionRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    logger.info(f"Received question: '{payload.question}' with k={payload.k}")
    try:
        response = answer_question(payload.question, payload.k)
        logger.info("Answer generated successfully.")
        return response
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Something went wrong while processing the question.")

@app.get("/health")
def health_check():
    logger.info("Health check passed.")
    return {"status": "ok"}

@app.get("/status")
def status_check():
    try:
        vectordb = get_vectordb()
        count = vectordb._collection.count()
        files = os.listdir("uploaded_docs") if os.path.exists("uploaded_docs") else []
        logger.info(f"Vector store contains {count} documents.")
        return {
            "status": "ready",
            "documents_indexed": count,
            "uploaded_files": files
        }
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Something went wrong while checking the status.")

from fastapi import UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
import logging

logger = logging.getLogger(__name__)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # ✅ Allow .pdf, .txt, .md only
        allowed_extensions = [".pdf", ".txt", ".md"]
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Only PDF, TXT, and Markdown files are supported.")

        upload_dir = "uploaded_docs"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File '{file.filename}' uploaded successfully.")

        # Ingest the uploaded file
        result = ingest_single_file(file_path)

        if result == "duplicate":
            return {"message": f"File '{file.filename}' already exists in the vector store. Skipping ingestion."}

        if isinstance(result, dict):
            logger.info(f"{result['chunks_added']} chunks ingested from '{file.filename}'.")
            # Notify WebSocket clients
            for connection in active_connections:
                try:
                    await connection.send_json({"type": "file_updated", "files": os.listdir(upload_dir)})
                except Exception as e:
                    logger.error(f"Error sending update to WebSocket client: {str(e)}")

            return {
                "message": f"Successfully uploaded '{file.filename}' with {result['chunks_added']} chunks."
            }
        else:
            logger.error(f"Error uploading file: ingestion failed for '{file.filename}'")
            raise HTTPException(status_code=500, detail="Failed to process file.")

    except HTTPException as http_exc:
        raise http_exc  # Let FastAPI handle this cleanly

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Something went wrong while uploading the file.")

@app.post("/fresh-start")
async def fresh_start():
    try:
        # Delete vector store and uploaded files
        vector_store_dir = "vector_store"
        if os.path.exists(vector_store_dir):
            shutil.rmtree(vector_store_dir)
            logger.info("🧹 Deleted vector store directory.")

        upload_dir = "uploaded_docs"
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)
            logger.info("🗑️ Deleted uploaded files directory.")

        # Notify all connected clients about the change
        for connection in active_connections:
            try:
                await connection.send_json({"type": "files_cleared"})
            except Exception as e:
                logger.error(f"Error sending update to WebSocket client: {str(e)}")

        return {
            "message": "All files have been deleted. Please manually restart both the backend and frontend servers.",
            "instructions": "1. Stop the backend server (Ctrl+C)\n2. Stop the frontend server (Ctrl+C)\n3. Restart both servers"
        }
    except Exception as e:
        logger.error(f"Error during fresh start: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to perform fresh start.")

@app.get("/files")
def list_uploaded_files():
    try:
        upload_dir = "uploaded_docs"
        os.makedirs(upload_dir, exist_ok=True)
        files = os.listdir(upload_dir)
        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Something went wrong while listing files.")
