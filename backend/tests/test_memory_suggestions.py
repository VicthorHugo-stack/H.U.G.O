
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.database import init_db


# ============================================================
# FIXTURE: BANCO DE DADOS TEMPORÁRIO
# ============================================================

@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db_path = tmp_path / "hugo_test.sqlite3"

    monkeypatch.setattr(
        "app.database.DB_PATH",
        test_db_path,
    )

    init_db()

    with TestClient(app) as test_client:
        yield test_client


# ============================================================
# TESTE 1: SAÚDE DA API
# ============================================================

def test_health_endpoint(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "online"


# ============================================================
# TESTE 2: CRIAR SUGESTÃO
# ============================================================

def test_create_memory_suggestion(client):
    response = client.post(
        "/api/memory-suggestions",
        json={
            "category": " Preference ",
            "content": "  Prefere respostas práticas.  ",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["category"] == "preference"
    assert data["content"] == "Prefere respostas práticas."
    assert data["status"] == "pending"
    assert data["duplicate"] is False


# ============================================================
# TESTE 3: DETECTAR SUGESTÃO DUPLICADA
# ============================================================

def test_duplicate_pending_suggestion(client):
    payload = {
        "category": "preference",
        "content": "Prefere respostas práticas.",
    }

    first_response = client.post(
        "/api/memory-suggestions",
        json=payload,
    )

    second_response = client.post(
        "/api/memory-suggestions",
        json={
            "category": " PREFERENCE ",
            "content": "  Prefere respostas práticas.  ",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first = first_response.json()
    second = second_response.json()

    assert first["duplicate"] is False
    assert second["duplicate"] is True
    assert second["id"] == first["id"]


# ============================================================
# TESTE 4: LISTAR SUGESTÕES PENDENTES
# ============================================================

def test_list_pending_suggestions(client):
    client.post(
        "/api/memory-suggestions",
        json={
            "category": "preference",
            "content": "Prefere exemplos práticos.",
        },
    )

    response = client.get(
        "/api/memory-suggestions",
        params={"status": "pending"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["suggestions"]) == 1
    assert data["suggestions"][0]["status"] == "pending"


# ============================================================
# TESTE 5: ACEITAR SUGESTÃO E CRIAR MEMÓRIA
# ============================================================

def test_accept_suggestion_creates_memory(client):
    suggestion_response = client.post(
        "/api/memory-suggestions",
        json={
            "category": "preference",
            "content": "Prefere exemplos detalhados.",
        },
    )

    suggestion_id = suggestion_response.json()["id"]

    decision_response = client.post(
        f"/api/memory-suggestions/{suggestion_id}/decision",
        json={"decision": "accept"},
    )

    assert decision_response.status_code == 200

    decision_data = decision_response.json()

    assert decision_data["status"] == "accepted"
    assert decision_data["memory_id"] is not None

    memories_response = client.get(
        "/api/memories",
        params={"category": "preference"},
    )

    assert memories_response.status_code == 200

    memories_data = memories_response.json()

    assert any(
        memory["content"] == "Prefere exemplos detalhados."
        for memory in memories_data["memories"]
    )


# ============================================================
# TESTE 6: REJEITAR SUGESTÃO SEM CRIAR MEMÓRIA
# ============================================================

def test_reject_suggestion_does_not_create_memory(client):
    suggestion_response = client.post(
        "/api/memory-suggestions",
        json={
            "category": "test",
            "content": "Esta memória deve ser rejeitada.",
        },
    )

    suggestion_id = suggestion_response.json()["id"]

    decision_response = client.post(
        f"/api/memory-suggestions/{suggestion_id}/decision",
        json={"decision": "reject"},
    )

    assert decision_response.status_code == 200
    assert decision_response.json()["status"] == "rejected"

    memories_response = client.get(
        "/api/memories",
        params={"category": "test"},
    )

    assert memories_response.status_code == 200
    assert memories_response.json()["total"] == 0
    assert memories_response.json()["memories"] == []


# ============================================================
# TESTE 7: IMPEDIR SEGUNDA DECISÃO
# ============================================================

def test_cannot_decide_suggestion_twice(client):
    suggestion_response = client.post(
        "/api/memory-suggestions",
        json={
            "category": "preference",
            "content": "Sugestão avaliada uma única vez.",
        },
    )

    suggestion_id = suggestion_response.json()["id"]

    first_decision = client.post(
        f"/api/memory-suggestions/{suggestion_id}/decision",
        json={"decision": "reject"},
    )

    second_decision = client.post(
        f"/api/memory-suggestions/{suggestion_id}/decision",
        json={"decision": "accept"},
    )

    assert first_decision.status_code == 200
    assert second_decision.status_code == 409
    assert second_decision.json()["detail"] == (
        "Esta sugestão já foi avaliada."
    )


# ============================================================
# TESTE 8: SUGESTÃO INEXISTENTE
# ============================================================

def test_decision_for_nonexistent_suggestion(client):
    response = client.post(
        "/api/memory-suggestions/999999/decision",
        json={"decision": "accept"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Sugestão não encontrada."


# ============================================================
# TESTE 9: FILTRO DE STATUS INVÁLIDO
# ============================================================

def test_invalid_suggestion_status_filter(client):
    response = client.get(
        "/api/memory-suggestions",
        params={"status": "invalid"},
    )

    assert response.status_code == 422


# ============================================================
# TESTE 10: LISTAR TODAS AS SUGESTÕES
# ============================================================

def test_list_all_suggestions(client):
    for content in [
        "Sugestão aceita.",
        "Sugestão rejeitada.",
    ]:
        client.post(
            "/api/memory-suggestions",
            json={
                "category": "test",
                "content": content,
            },
        )

    client.post(
        "/api/memory-suggestions/1/decision",
        json={"decision": "accept"},
    )

    client.post(
        "/api/memory-suggestions/2/decision",
        json={"decision": "reject"},
    )

    response = client.get(
        "/api/memory-suggestions",
        params={"status": "all"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2

    statuses = {
        suggestion["status"]
        for suggestion in data["suggestions"]
    }

    assert statuses == {"accepted", "rejected"}

# ============================================================
# TESTE 11: LISTAR MEMÓRIAS
# ============================================================

def test_list_memories(client):
    response = client.get("/api/memories")

    assert response.status_code == 200

    data = response.json()

    assert "total" in data
    assert "memories" in data
    assert isinstance(data["memories"], list)
    assert data["total"] == len(data["memories"])


# ============================================================
# TESTE 12: FILTRAR MEMÓRIAS POR CATEGORIA
# ============================================================

def test_list_memories_by_category(client):
    client.post(
        "/api/memories",
        json={
            "category": "preference",
            "content": "Prefere respostas objetivas.",
        },
    )

    client.post(
        "/api/memories",
        json={
            "category": "work",
            "content": "Trabalha com desenvolvimento de software.",
        },
    )

    response = client.get(
        "/api/memories",
        params={"category": "preference"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1
    assert all(
        memory["category"].strip().lower() == "preference"
        for memory in data["memories"]
    )


# ============================================================
# TESTE 13: FILTRO IGNORA MAIÚSCULAS E ESPAÇOS
# ============================================================

def test_list_memories_category_normalization(client):
    client.post(
        "/api/memories",
        json={
            "category": "preference",
            "content": "Prefere exemplos claros.",
        },
    )

    response = client.get(
        "/api/memories",
        params={"category": "  PREFERENCE  "},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1
    assert all(
        memory["category"].strip().lower() == "preference"
        for memory in data["memories"]
    )


# ============================================================
# TESTE 14: CATEGORIA SEM RESULTADOS
# ============================================================

def test_list_memories_empty_category(client):
    response = client.get(
        "/api/memories",
        params={"category": "categoria_inexistente"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["memories"] == []


# ============================================================
# TESTE 15: ATUALIZAR MEMÓRIA
# ============================================================

def test_update_memory(client):
    create_response = client.post(
        "/api/memories",
        json={
            "category": "preference",
            "content": "Conteúdo original da memória.",
        },
    )

    assert create_response.status_code in (200, 201)

    memory_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/memories/{memory_id}",
        json={
            "category": "preference",
            "content": "Conteúdo atualizado da memória.",
        },
    )

    assert update_response.status_code == 200

    data = update_response.json()

    assert data["id"] == memory_id
    assert data["category"] == "preference"
    assert data["content"] == "Conteúdo atualizado da memória."
    assert data["message"] == "Memória atualizada com sucesso."


# ============================================================
# TESTE 16: ATUALIZAR MEMÓRIA INEXISTENTE
# ============================================================

def test_update_nonexistent_memory(client):
    response = client.put(
        "/api/memories/999999",
        json={
            "category": "preference",
            "content": "Memória inexistente.",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Memória não encontrada."


# ============================================================
# TESTE 17: IMPEDIR ATUALIZAÇÃO COM MEMÓRIA DUPLICADA
# ============================================================

def test_update_memory_with_duplicate_content(client):
    first_response = client.post(
        "/api/memories",
        json={
            "category": "preference",
            "content": "Memória original A.",
        },
    )

    second_response = client.post(
        "/api/memories",
        json={
            "category": "preference",
            "content": "Memória original B.",
        },
    )

    assert first_response.status_code in (200, 201)
    assert second_response.status_code in (200, 201)

    first_id = first_response.json()["id"]
    second_id = second_response.json()["id"]

    response = client.put(
        f"/api/memories/{second_id}",
        json={
            "category": "preference",
            "content": "Memória original A.",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Já existe outra memória com essa categoria e conteúdo."
    )

    # Confirma que a memória original não foi alterada.
    memories_response = client.get("/api/memories")

    memories = memories_response.json()["memories"]

    original = next(
        memory for memory in memories
        if memory["id"] == second_id
    )

    assert original["content"] == "Memória original B."


# ============================================================
# TESTE 18: EXCLUIR MEMÓRIA
# ============================================================

def test_delete_memory(client):
    create_response = client.post(
        "/api/memories",
        json={
            "category": "test",
            "content": "Memória que será excluída.",
        },
    )

    assert create_response.status_code in (200, 201)

    memory_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/api/memories/{memory_id}"
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["id"] == memory_id
    assert delete_response.json()["message"] == (
        "Memória excluída com sucesso."
    )

    list_response = client.get(
        "/api/memories",
        params={"category": "test"},
    )

    assert list_response.status_code == 200

    assert all(
        memory["id"] != memory_id
        for memory in list_response.json()["memories"]
    )


# ============================================================
# TESTE 19: EXCLUIR MEMÓRIA INEXISTENTE
# ============================================================

def test_delete_nonexistent_memory(client):
    response = client.delete("/api/memories/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Memória não encontrada."



# ============================================================
# TESTE 20: CONSULTAR CONVERSA INEXISTENTE
# ============================================================

def test_get_messages_for_nonexistent_conversation(client):
    response = client.get(
        "/api/conversations/conversa-inexistente/messages"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversa não encontrada."


# ============================================================
# TESTE 21: CONSULTAR CONVERSA EXISTENTE SEM MENSAGENS
# ============================================================

def test_get_messages_for_empty_conversation(client):
    from app.database import get_connection
    import uuid

    conversation_id = str(uuid.uuid4())

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO conversations (id)
            VALUES (?)
            """,
            (conversation_id,),
        )

    response = client.get(
        f"/api/conversations/{conversation_id}/messages"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["conversation"]["id"] == conversation_id
    assert data["messages"] == []


# ============================================================
# TESTE 22: CONSULTAR MENSAGENS DE UMA CONVERSA
# ============================================================

def test_get_messages_for_existing_conversation(client):
    from app.database import get_connection
    import uuid

    conversation_id = str(uuid.uuid4())

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO conversations (id)
            VALUES (?)
            """,
            (conversation_id,),
        )

        connection.execute(
            """
            INSERT INTO messages (
                conversation_id,
                role,
                content
            )
            VALUES (?, ?, ?)
            """,
            (
                conversation_id,
                "user",
                "Olá, Hugo!",
            ),
        )

        connection.execute(
            """
            INSERT INTO messages (
                conversation_id,
                role,
                content
            )
            VALUES (?, ?, ?)
            """,
            (
                conversation_id,
                "assistant",
                "Olá! Como posso ajudar?",
            ),
        )

    response = client.get(
        f"/api/conversations/{conversation_id}/messages"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["conversation"]["id"] == conversation_id
    assert len(data["messages"]) == 2

    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "Olá, Hugo!"

    assert data["messages"][1]["role"] == "assistant"
    assert data["messages"][1]["content"] == (
        "Olá! Como posso ajudar?"
    )


# ============================================================
# TESTE 23: NÃO MISTURAR MENSAGENS DE CONVERSAS DIFERENTES
# ============================================================

def test_conversation_messages_are_isolated(client):
    from app.database import get_connection
    import uuid

    conversation_a = str(uuid.uuid4())
    conversation_b = str(uuid.uuid4())

    with get_connection() as connection:
        connection.execute(
            "INSERT INTO conversations (id) VALUES (?)",
            (conversation_a,),
        )

        connection.execute(
            "INSERT INTO conversations (id) VALUES (?)",
            (conversation_b,),
        )

        connection.execute(
            """
            INSERT INTO messages (
                conversation_id,
                role,
                content
            )
            VALUES (?, ?, ?)
            """,
            (conversation_a, "user", "Mensagem da conversa A"),
        )

        connection.execute(
            """
            INSERT INTO messages (
                conversation_id,
                role,
                content
            )
            VALUES (?, ?, ?)
            """,
            (conversation_b, "user", "Mensagem da conversa B"),
        )

    response = client.get(
        f"/api/conversations/{conversation_a}/messages"
    )

    assert response.status_code == 200

    messages = response.json()["messages"]

    assert len(messages) == 1
    assert messages[0]["content"] == "Mensagem da conversa A"
    assert all(
        message["conversation_id"] == conversation_a
        for message in messages
    )


# ============================================================
# TESTE 24: CHAT COM NOVA CONVERSA
# ============================================================

def test_chat_creates_conversation_and_saves_messages(
    client,
    monkeypatch,
):
    from unittest.mock import AsyncMock, MagicMock
    import app.main as main_module

    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {
        "message": {
            "content": "Olá! Como posso ajudar?"
        }
    }

    fake_client = MagicMock()
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=None)
    fake_client.post = AsyncMock(return_value=fake_response)

    monkeypatch.setattr(
        main_module.httpx,
        "AsyncClient",
        lambda **kwargs: fake_client,
    )

    response = client.post(
        "/api/chat",
        json={"message": "Olá, Hugo!"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["reply"] == "Olá! Como posso ajudar?"
    assert data["model"] == main_module.OLLAMA_MODEL
    assert data["conversation_id"]

    history_response = client.get(
        f"/api/conversations/{data['conversation_id']}/messages"
    )

    assert history_response.status_code == 200

    messages = history_response.json()["messages"]

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Olá, Hugo!"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Olá! Como posso ajudar?"


# ============================================================
# TESTE 25: CONTINUAR CONVERSA EXISTENTE
# ============================================================

def test_chat_continues_existing_conversation(
    client,
    monkeypatch,
):
    from unittest.mock import AsyncMock, MagicMock
    import app.main as main_module
    import uuid

    conversation_id = str(uuid.uuid4())

    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {
        "message": {"content": "Essa é a segunda resposta."}
    }

    fake_client = MagicMock()
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=None)
    fake_client.post = AsyncMock(return_value=fake_response)

    monkeypatch.setattr(
        main_module.httpx,
        "AsyncClient",
        lambda **kwargs: fake_client,
    )

    first_response = client.post(
        "/api/chat",
        json={
            "message": "Minha primeira mensagem.",
            "conversation_id": conversation_id,
        },
    )

    second_response = client.post(
        "/api/chat",
        json={
            "message": "Minha segunda mensagem.",
            "conversation_id": conversation_id,
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["conversation_id"] == conversation_id

    sent_messages = fake_client.post.call_args.kwargs["json"]["messages"]

    assert any(
        message["role"] == "user"
        and message["content"] == "Minha primeira mensagem."
        for message in sent_messages
    )

    assert sent_messages[-1]["role"] == "user"
    assert sent_messages[-1]["content"] == "Minha segunda mensagem."


# ============================================================
# TESTE 26: REJEITAR MENSAGEM VAZIA
# ============================================================

def test_chat_rejects_empty_message(client):
    response = client.post(
        "/api/chat",
        json={"message": "   "},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "A mensagem não pode estar vazia."


# ============================================================
# TESTE 27: RESPOSTA VAZIA DO OLLAMA
# ============================================================

def test_chat_rejects_empty_ollama_reply(
    client,
    monkeypatch,
):
    from unittest.mock import AsyncMock, MagicMock
    import app.main as main_module

    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {
        "message": {"content": "   "}
    }

    fake_client = MagicMock()
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=None)
    fake_client.post = AsyncMock(return_value=fake_response)

    monkeypatch.setattr(
        main_module.httpx,
        "AsyncClient",
        lambda **kwargs: fake_client,
    )

    response = client.post(
        "/api/chat",
        json={"message": "Olá"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "O Ollama retornou uma resposta vazia."
    )

    # A mensagem não deve ser gravada se a resposta for vazia.
    from app.database import get_connection

    with get_connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM messages"
        ).fetchone()[0]

    assert count == 0


# ============================================================
# TESTE 28: FALHA DE CONEXÃO COM O OLLAMA
# ============================================================

def test_chat_handles_ollama_connection_error(
    client,
    monkeypatch,
):
    from unittest.mock import AsyncMock, MagicMock
    import app.main as main_module

    fake_client = MagicMock()
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=None)
    fake_client.post = AsyncMock(
        side_effect=main_module.httpx.ConnectError(
            "Conexão recusada"
        )
    )

    monkeypatch.setattr(
        main_module.httpx,
        "AsyncClient",
        lambda **kwargs: fake_client,
    )

    response = client.post(
        "/api/chat",
        json={"message": "Teste de conexão"},
    )

    assert response.status_code == 503
    assert "Não foi possível conectar ao Ollama" in (
        response.json()["detail"]
    )

    # Nenhuma mensagem deve ser salva após falha de conexão.
    from app.database import get_connection

    with get_connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM messages"
        ).fetchone()[0]

    assert count == 0


def test_chat_sends_configured_context_to_ollama(client):
    from unittest.mock import AsyncMock, MagicMock

    import app.main as main_module

    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {
        "message": {
            "content": "Resposta de teste."
        }
    }

    fake_client = MagicMock()
    fake_client.__aenter__ = AsyncMock(
        return_value=fake_client
    )
    fake_client.__aexit__ = AsyncMock(
        return_value=None
    )
    fake_client.post = AsyncMock(
        return_value=fake_response
    )

    original_client = main_module.httpx.AsyncClient
    main_module.httpx.AsyncClient = lambda **kwargs: fake_client

    try:
        response = client.post(
            "/api/chat",
            json={"message": "Teste de contexto"},
        )
    finally:
        main_module.httpx.AsyncClient = original_client

    assert response.status_code == 200

    payload = fake_client.post.call_args.kwargs["json"]

    assert "options" in payload
    assert payload["options"]["num_ctx"] == main_module.HUGO_NUM_CTX
    assert main_module.HUGO_NUM_CTX == 2048


def test_load_num_ctx_rejects_non_integer(monkeypatch):
    import pytest
    import app.main as main_module

    monkeypatch.setenv("HUGO_NUM_CTX", "abc")

    with pytest.raises(
        ValueError,
        match="deve ser um número inteiro",
    ):
        main_module.load_num_ctx()


def test_load_num_ctx_rejects_value_out_of_range(monkeypatch):
    import pytest
    import app.main as main_module

    monkeypatch.setenv("HUGO_NUM_CTX", "100")

    with pytest.raises(
        ValueError,
        match="deve estar entre 512 e 32768",
    ):
        main_module.load_num_ctx()
