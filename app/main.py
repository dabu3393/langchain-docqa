from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import request_validation_exception_handler
from pydantic import BaseModel
from app.qa_chain import answer_question
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

vectordb = Chroma(persist_directory="vector_store", embedding_function=OpenAIEmbeddings())

class QuestionRequest(BaseModel):
    question: str
    k: int = 4

@app.on_event("startup")
async def on_startup():
    logger.info("🚀 FastAPI app has started and is ready to receive requests.")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid input", "details": exc.errors()},
    )

@app.post("/ask")
def ask_question(payload: QuestionRequest):
    logger.info(f"Received question: '{payload.question}' with k={payload.k}")
    try:
        response = answer_question(payload.question, payload.k)
        logger.info("Answer generated successfully.")
        return response
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Something went wrong while processing the question."}
        )

@app.get("/health")
def health_check():
    logger.info("Health check passed.")
    return {"status": "ok"}

@app.get("/status")
def status_check():
    try:
        count = vectordb._collection.count()
        logger.info(f"Vector store contains {count} documents.")
        return {
            "status": "ready",
            "documents_indexed": count
        }
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Something went wrong while checking the status."}
        )