import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PROJECT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.database import init_db
from app.tools import tool_registry, get_current_datetime
from app.main import app, request_ollama_chat


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db_path = tmp_path / "hugo_chat_tools_test.sqlite3"

    monkeypatch.setattr(
        "app.database.DB_PATH",
        test_db_path,
    )

    init_db()

    with TestClient(app) as test_client:
        yield test_client


def test_datetime_tool_is_registered():
    tool = tool_registry.get("get_current_datetime")

    assert tool is not None
    assert tool.name == "get_current_datetime"
    assert tool.requires_confirmation is False


def test_datetime_tool_returns_valid_data():
    result = get_current_datetime()

    assert isinstance(result, dict)
    assert result["timezone"] == "America/Sao_Paulo"
    assert result["datetime"]


def test_chat_endpoint_rejects_empty_message(client):
    response = client.post(
        "/api/chat",
        json={"message": "   "},
    )

    assert response.status_code == 422


def test_chat_endpoint_rejects_message_without_content(client, monkeypatch):
    async def fake_post(*args, **kwargs):
        raise AssertionError(
            "O Ollama não deveria ser chamado para uma mensagem vazia."
        )

    monkeypatch.setattr(
        "httpx.AsyncClient.post",
        fake_post,
    )

    response = client.post(
        "/api/chat",
        json={"message": "   "},
    )

    assert response.status_code == 422


def test_tool_registry_rejects_unknown_tool():
    tool = tool_registry.get("ferramenta_inexistente")

    assert tool is None


def test_describe_tools_includes_confirmation_requirement():
    descriptions = tool_registry.describe_tools()

    datetime_tool = next(
        (
            item
            for item in descriptions
            if item["name"] == "get_current_datetime"
        ),
        None,
    )

    assert datetime_tool is not None
    assert datetime_tool["requires_confirmation"] is False
    assert isinstance(datetime_tool["parameters"], dict)


def test_datetime_tool_has_no_required_arguments():
    tool = tool_registry.get("get_current_datetime")

    assert tool is not None
    assert tool.parameters["type"] == "object"
    assert tool.parameters["required"] == []
    assert tool.parameters["additionalProperties"] is False


@pytest.mark.anyio
async def test_request_ollama_chat_sends_registered_tools(monkeypatch):
    from types import SimpleNamespace

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "message": {
                    "role": "assistant",
                    "content": "Olá!",
                }
            }

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json):
            captured["url"] = url
            captured["payload"] = json
            return FakeResponse()

    monkeypatch.setattr(
        "app.main.httpx.AsyncClient",
        FakeAsyncClient,
    )

    messages = [{"role": "user", "content": "Que horas são?"}]

    result = await request_ollama_chat(messages)

    assert result["message"]["content"] == "Olá!"
    assert captured["payload"]["messages"] == messages
    assert captured["payload"]["stream"] is False
    assert "tools" in captured["payload"]

    tool_names = [
        item["function"]["name"]
        for item in captured["payload"]["tools"]
    ]

    assert "get_current_datetime" in tool_names


@pytest.mark.anyio
async def test_request_ollama_chat_can_disable_tools(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "message": {
                    "role": "assistant",
                    "content": "Resposta sem ferramentas.",
                }
            }

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, json):
            assert "tools" not in json
            return FakeResponse()

    monkeypatch.setattr(
        "app.main.httpx.AsyncClient",
        FakeAsyncClient,
    )

    result = await request_ollama_chat(
        [{"role": "user", "content": "Olá"}],
        include_tools=False,
    )

    assert result["message"]["content"] == "Resposta sem ferramentas."


def test_chat_executes_tool_and_returns_final_answer(client, monkeypatch):
    calls = []

    async def fake_request_ollama_chat(messages, include_tools=True):
        calls.append({
            "messages": [dict(message) for message in messages],
            "include_tools": include_tools,
        })

        if len(calls) == 1:
            return {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "get_current_datetime",
                                "arguments": {},
                            }
                        }
                    ],
                }
            }

        return {
            "message": {
                "role": "assistant",
                "content": "Consultei a ferramenta e obtive a data e hora atuais.",
            }
        }

    monkeypatch.setattr(
        "app.main.request_ollama_chat",
        fake_request_ollama_chat,
    )

    response = client.post(
        "/api/chat",
        json={"message": "Que horas são?"},
    )

    assert response.status_code == 200
    assert "data e hora atuais" in response.json()["reply"]
    assert len(calls) == 2

    messages_after_tool_call = calls[1]["messages"]

    tool_messages = [
        message
        for message in messages_after_tool_call
        if message.get("role") == "tool"
    ]

    assert len(tool_messages) == 1
    assert tool_messages[0]["tool_name"] == "get_current_datetime"
    assert '"success": true' in tool_messages[0]["content"]


def test_chat_stops_tool_loop_after_max_rounds(client, monkeypatch):
    from app.main import MAX_TOOL_CALL_ROUNDS

    calls = []

    async def fake_request_ollama_chat(messages, include_tools=True):
        calls.append(include_tools)

        if include_tools:
            return {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "get_current_datetime",
                                "arguments": {},
                            }
                        }
                    ],
                }
            }

        return {
            "message": {
                "role": "assistant",
                "content": "Concluí o processamento.",
            }
        }

    monkeypatch.setattr(
        "app.main.request_ollama_chat",
        fake_request_ollama_chat,
    )

    response = client.post(
        "/api/chat",
        json={"message": "Que horas são?"},
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "Concluí o processamento."
    assert len(calls) == MAX_TOOL_CALL_ROUNDS + 1
    assert calls[-1] is False


@pytest.mark.parametrize(
    ("tool_name", "arguments"),
    [
        ("ferramenta_inexistente", {}),
        ("get_current_datetime", {"argumento_invalido": "teste"}),
    ],
)
def test_chat_handles_invalid_tool_calls(
    client,
    monkeypatch,
    tool_name,
    arguments,
):
    calls = []

    async def fake_request_ollama_chat(messages, include_tools=True):
        calls.append(include_tools)

        if len(calls) == 1:
            return {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": tool_name,
                                "arguments": arguments,
                            }
                        }
                    ],
                }
            }

        return {
            "message": {
                "role": "assistant",
                "content": "A solicitação foi processada com segurança.",
            }
        }

    monkeypatch.setattr(
        "app.main.request_ollama_chat",
        fake_request_ollama_chat,
    )

    response = client.post(
        "/api/chat",
        json={"message": "Execute uma ferramenta."},
    )

    assert response.status_code == 200
    assert response.json()["reply"] == (
        "A solicitação foi processada com segurança."
    )
    assert len(calls) == 2
