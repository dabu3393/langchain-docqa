"""FastAPI application for LangChain document Q&A system."""

import argparse
import logging
import os
import shutil
from contextlib import asynccontextmanager
from typing import Set

from fastapi import (FastAPI, File, HTTPException, Request, UploadFile,
                     WebSocket, WebSocketDisconnect)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain.globals import set_llm_cache
from pydantic import BaseModel

from app.ingest import ingest_single_file
from app.qa_chain import answer_question
from app.vector_store import get_vectordb

set_llm_cache(None)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Parse CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "--fresh-start", action="store_true", help="Delete vector store on startup"
)
args, _ = parser.parse_known_args()

if args.fresh_start:
    VECTOR_STORE_DIR = "vector_store"
    if os.path.exists(VECTOR_STORE_DIR):
        shutil.rmtree(VECTOR_STORE_DIR)
        logger.info("🧹 Fresh start: Deleted vector store directory.")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize the FastAPI application."""
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
    """Request model for question answering."""

    question: str
    k: int = 4


# Store active WebSocket connections
active_connections: Set[WebSocket] = set()


@app.websocket("/ws/files")
async def websocket_endpoint(websocket: WebSocket):
    """Establish a WebSocket connection for file updates."""
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            # Wait for any message (we don't actually need to process it)
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning("Validation error: %s", exc)
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid input", "details": exc.errors()},
    )


@app.post("/ask")
async def ask_question(payload: QuestionRequest):
    """Answer a question based on ingested documents."""
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    logger.info("Received question: %s with k=%s", payload.question, payload.k)
    try:
        response = answer_question(payload.question, payload.k)
        logger.info("Answer generated successfully.")
        return response
    except Exception as e:
        logger.error("Error processing question: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while processing the question.",
        ) from e


@app.get("/health")
async def health_check():
    """Check application health status."""
    logger.info("Health check passed.")
    return {"status": "ok"}


@app.get("/status")
async def status_check():
    """Check the status of the vector store."""
    try:
        vectordb = get_vectordb()
        count = vectordb._collection.count()
        files = os.listdir("uploaded_docs") if os.path.exists("uploaded_docs") else []
        logger.info("Vector store contains %s documents.", count)
        return {"status": "ready", "documents_indexed": count, "uploaded_files": files}
    except Exception as e:
        logger.error("Error checking status: %s", str(e))
        raise HTTPException(
            status_code=500, detail="Something went wrong while checking the status."
        ) from e


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a document file."""
    try:
        # ✅ Allow .pdf, .txt, .md only
        allowed_extensions = [".pdf", ".txt", ".md"]
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail="Only PDF, TXT, and Markdown files are supported.",
            )

        upload_dir = "uploaded_docs"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info("File '%s' uploaded successfully.", file.filename)

        # Ingest the uploaded file
        result = ingest_single_file(file_path)

        if result == "duplicate":
            return {
                "message": (
                    f"File '{file.filename}' already exists in the vector store."
                    "Skipping ingestion."
                )
            }

        if isinstance(result, dict):
            logger.info(
                "%s chunks ingested from '%s'.", result["chunks_added"], file.filename
            )
            # Notify WebSocket clients
            for connection in active_connections:
                try:
                    await connection.send_json(
                        {"type": "file_updated", "files": os.listdir(upload_dir)}
                    )
                except Exception as e:
                    logger.error("Error sending update to WebSocket client: %s", str(e))

            return {
                "message": (
                    f"Successfully uploaded '{file.filename}' with {result['chunks_added']} chunks."
                )
            }

        logger.error("Error uploading file: ingestion failed for '%s'", file.filename)
        raise HTTPException(status_code=500, detail="Failed to process file.")

    except HTTPException as http_exc:
        raise http_exc  # Let FastAPI handle this cleanly

    except Exception as e:
        logger.error("Error uploading file: %s", str(e))
        raise HTTPException(
            status_code=500, detail="Something went wrong while uploading the file."
        ) from e


@app.post("/fresh-start")
async def fresh_start():
    """Reset the vector store to a fresh state."""
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
                logger.error("Error sending update to WebSocket client: %s", str(e))

        return {
            "message": (
                "All files have been deleted."
                "Please manually restart both the backend and frontend servers."
            ),
            "instructions": (
                "1. Stop the backend server (Ctrl+C)\n"
                "2. Stop the frontend server (Ctrl+C)\n"
                "3. Restart both servers"
            ),
        }
    except Exception as e:
        logger.error("Error during fresh start: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to perform fresh start.",
        ) from e


@app.get("/files")
async def list_uploaded_files():
    """List all files currently in the vector store."""
    try:
        upload_dir = "uploaded_docs"
        os.makedirs(upload_dir, exist_ok=True)
        files = os.listdir(upload_dir)
        return {"files": files}
    except Exception as e:
        logger.error("Error listing files: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while listing files.",
        ) from e
