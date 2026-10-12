# Decisões técnicas

## D-001 — Sistema operacional
Windows 10.

## D-002 — Ambiente de desenvolvimento
Visual Studio Code.

## D-003 — Controle de versão
Git, com branch principal main.

## D-004 — Backend
Python + FastAPI.

## D-005 — Modelo local
Ollama, usando qwen2.5:3b como candidato inicial já instalado.
A decisão final dependerá dos testes.

## D-006 — Versão Python
Python 3.13 para o ambiente virtual do projeto, evitando depender
da compatibilidade ainda não verificada do Python 3.15.

## D-007 — Banco de dados
SQLite para persistência local.

## D-008 — Interface
React + Tauri, planejados para o aplicativo desktop.

## D-009 — Memória
Histórico de conversa separado das memórias de longo prazo.
A memória deverá permitir consulta, correção e exclusão.

## D-010 — Segurança
Credenciais fora do Git; ações sensíveis exigem confirmação;
nenhum comando arbitrário do sistema será executado por sugestão da IA.

## D-011 — Execução diária
O aplicativo deverá gerenciar o backend sem exigir que o usuário
abra manualmente um terminal a cada utilização.

## D-012 — Hardware
RAM disponível: 8 GB. CPU e GPU ainda precisam ser identificadas.
