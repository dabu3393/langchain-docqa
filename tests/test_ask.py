"""Unit tests for the ask functionality."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_ask_question_success(monkeypatch):
    """Test question answering with success."""

    # Patch where the function is used, not defined
    def mock_answer_question(_query: str, _k: int = 4):
        return {
            "answer": "This is a mock answer.",
            "sources": [
                {"source": "sample.txt", "snippet": "Mock snippet...", "score": 0.91}
            ],
        }

    monkeypatch.setattr("app.main.answer_question", mock_answer_question)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/ask", json={"question": "What is LangChain?", "k": 4}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "This is a mock answer."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["source"] == "sample.txt"


@pytest.mark.asyncio
async def test_ask_question_no_documents(monkeypatch):
    """Test question answering with no documents."""

    def mock_answer_question(_query: str, _k: int = 4):
        return {"answer": "I don't know based on the document.", "sources": []}

    monkeypatch.setattr("app.main.answer_question", mock_answer_question)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/ask", json={"question": "Unanswerable question", "k": 4}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "I don't know based on the document."
    assert data["sources"] == []


@pytest.mark.asyncio
async def test_ask_invalid_payload(client):
    """Test question answering with invalid payload."""
    # Send an empty JSON body, which lacks both 'question' and 'k'
    response = await client.post("/ask", json={})

    assert response.status_code == 422
    assert "details" in response.json()


@pytest.mark.asyncio
async def test_ask_internal_error(monkeypatch, client):
    """Test question answering with internal error."""

    # Monkeypatch the answer_question function to raise an exception
    def mock_answer_question(*args, **kwargs):
        """Mock answer_question function."""
        raise Exception("Simulated failure")

    monkeypatch.setattr("app.main.answer_question", mock_answer_question)

    payload = {"question": "What is Python?", "k": 3}
    response = await client.post("/ask", json=payload)

    assert response.status_code == 500
    assert (
        response.json()["detail"]
        == "Something went wrong while processing the question."
    )
