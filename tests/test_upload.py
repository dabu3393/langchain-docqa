import pytest
from pathlib import Path
from fpdf import FPDF
from app.main import active_connections
from datetime import datetime

@pytest.mark.asyncio
async def test_file_upload_success(client):
    test_file_path = Path("tests/test_files/sample.pdf")
    test_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a valid simple PDF using fpdf
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Test PDF content", ln=True)
    pdf.output(str(test_file_path))

    with test_file_path.open("rb") as f:
        response = await client.post("/upload", files={"file": ("sample.pdf", f, "application/pdf")})

    assert response.status_code == 200

@pytest.mark.asyncio
async def test_file_upload_invalid_type(client):
    test_file_path = Path("tests/test_files/invalid.exe")
    test_file_path.parent.mkdir(parents=True, exist_ok=True)
    test_file_path.write_text("This should not be allowed.")

    with test_file_path.open("rb") as f:
        response = await client.post("/upload", files={"file": ("invalid.exe", f, "application/octet-stream")})

    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF, TXT, and Markdown files are supported."

@pytest.mark.asyncio
async def test_file_upload_duplicate(client):
    test_file_path = Path("tests/test_files/sample.txt")
    test_file_path.parent.mkdir(parents=True, exist_ok=True)
    test_file_path.write_text("This is a duplicate test file.")

    # Upload once to ensure it's in the store
    with test_file_path.open("rb") as f:
        await client.post("/upload", files={"file": ("sample.txt", f, "text/plain")})

    # Upload again to trigger "duplicate"
    with test_file_path.open("rb") as f:
        response = await client.post("/upload", files={"file": ("sample.txt", f, "text/plain")})

    assert response.status_code == 200
    assert "already exists" in response.json().get("message", "")

@pytest.mark.asyncio
async def test_websocket_notification_on_upload(monkeypatch, client):
    class FakeConnection:
        def __init__(self):
            self.called = False
            self.sent_data = None

        async def send_json(self, data):
            self.called = True
            self.sent_data = data

    fake_connection = FakeConnection()
    active_connections.add(fake_connection)

    try:
        # Make file name unique to avoid 'duplicate' skips
        filename = f"ws_test_{datetime.utcnow().timestamp()}.txt"
        test_file_path = Path(f"tests/test_files/{filename}")
        test_file_path.parent.mkdir(parents=True, exist_ok=True)
        test_file_path.write_text("WebSocket test content.")

        with test_file_path.open("rb") as f:
            response = await client.post("/upload", files={"file": (filename, f, "text/plain")})

        assert response.status_code == 200
        assert fake_connection.called, "WebSocket was not notified"
        assert isinstance(fake_connection.sent_data, dict)
        assert fake_connection.sent_data["type"] == "file_updated"
        assert "files" in fake_connection.sent_data

    finally:
        active_connections.discard(fake_connection)
        if test_file_path.exists():
            test_file_path.unlink()
