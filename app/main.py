from fastapi import FastAPI
from pydantic import BaseModel
from app.qa_chain import answer_question

app = FastAPI()

class QuestionRequest(BaseModel):
    question: str
    k: int = 4

@app.post("/ask")
def ask_question(payload: QuestionRequest):
    return answer_question(payload.question, payload.k)