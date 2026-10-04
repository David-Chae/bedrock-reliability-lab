from fastapi.testclient import TestClient

import app.main as main


class FakeBedrock:
    def ask(self, question: str) -> str:
        return f"mock answer: {question}"


def test_health():
    client = TestClient(main.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask(monkeypatch):
    monkeypatch.setattr(main, "bedrock", FakeBedrock())
    monkeypatch.setattr(main.settings, "model_id", "fake-model")
    client = TestClient(main.app)

    response = client.post("/ask", json={"question": "What is RAG?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "mock answer: What is RAG?"
    assert body["model_id"] == "fake-model"
    assert body["request_id"]
    assert body["latency_ms"] >= 0


def test_empty_question_rejected(monkeypatch):
    monkeypatch.setattr(main.settings, "model_id", "fake-model")
    client = TestClient(main.app)

    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 422
