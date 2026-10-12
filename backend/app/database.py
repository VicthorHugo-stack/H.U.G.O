
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ============================================================

# Estrutura:
# H.U.G.O/
#   .env
#   data/
#   backend/
#     app/
#       database.py

PROJECT_DIR = Path(__file__).resolve().parents[2]

# Carrega as variáveis do arquivo .env na raiz do projeto.
load_dotenv(PROJECT_DIR / ".env")

DB_PATH_CONFIG = os.getenv(
    "HUGO_DB_PATH",
    "data/hugo.sqlite3",
)

_configured_db_path = Path(DB_PATH_CONFIG)

if not _configured_db_path.is_absolute():
    DB_PATH = PROJECT_DIR / _configured_db_path
else:
    DB_PATH = _configured_db_path


# ============================================================
# CONEXÃO COM O SQLITE
# ============================================================

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ============================================================
# INICIALIZAÇÃO DAS TABELAS E ÍNDICES
# ============================================================

def init_db():
    with get_connection() as connection:

        # ----------------------------------------------------
        # CONVERSAS
        # ----------------------------------------------------

        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL DEFAULT
                    (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                updated_at TEXT NOT NULL DEFAULT
                    (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
        """)

        # ----------------------------------------------------
        # MENSAGENS
        # ----------------------------------------------------

        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL
                    CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT
                    (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages (conversation_id, id)
        """)

        # ----------------------------------------------------
        # MEMÓRIAS
        # ----------------------------------------------------

        connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL DEFAULT 'general',
                content TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL DEFAULT
                    (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                updated_at TEXT NOT NULL DEFAULT
                    (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_category
            ON memories (category)
        """)

        # ----------------------------------------------------
        # SUGESTÕES DE MEMÓRIA
        # ----------------------------------------------------

        connection.execute("""
            CREATE TABLE IF NOT EXISTS memory_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL DEFAULT 'general',
                content TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'accepted', 'rejected')),
                created_at TEXT NOT NULL DEFAULT
                    (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                resolved_at TEXT
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_suggestions_status
            ON memory_suggestions (status, id)
        """)

        # ----------------------------------------------------
        # REMOÇÃO DE DUPLICATAS EXISTENTES
        # ----------------------------------------------------

        # Preserva o registro mais antigo de cada combinação
        # de categoria e conteúdo, ignorando espaços externos
        # e diferenças entre maiúsculas e minúsculas no conteúdo.
        connection.execute("""
            DELETE FROM memories
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM memories
                GROUP BY category, LOWER(TRIM(content))
            )
        """)

        # ----------------------------------------------------
        # ÍNDICE ÚNICO DE MEMÓRIAS
        # ----------------------------------------------------

        connection.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_memories_unique_content
            ON memories (category, LOWER(TRIM(content)))
        """)