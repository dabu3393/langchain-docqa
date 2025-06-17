import pytest
from pathlib import Path

@pytest.mark.asyncio
async def test_full_flow_file_upload_and_ask_question_success(client):
    # Setup: Create a small test file
    test_file_path = Path("tests/test_files/full_flow.txt")
    test_file_path.parent.mkdir(parents=True, exist_ok=True)
    test_file_path.write_text("LangChain enables building apps powered by LLMs.")

    try:
        # Step 1: Upload the file
        with test_file_path.open("rb") as f:
            upload_response = await client.post("/upload", files={"file": (test_file_path.name, f, "text/plain")})

        assert upload_response.status_code == 200
        assert "chunks" in upload_response.json()["message"]

        # Step 2: Ask a question related to the content
        question_payload = {
            "question": "What does LangChain help with?",
            "k": 2
        }
        ask_response = await client.post("/ask", json=question_payload)

        assert ask_response.status_code == 200
        data = ask_response.json()
        assert "answer" in data
        assert "sources" in data
        assert any(source["source"].endswith("full_flow.txt") for source in data["sources"])

    finally:
        test_file_path.unlink()
