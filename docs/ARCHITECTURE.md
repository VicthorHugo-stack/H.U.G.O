# Arquitetura do H.U.G.O.

## Objetivo
Assistente pessoal para Windows, com conversa natural, memória persistente
e ferramentas, priorizando processamento local.

## Componentes

### Aplicação desktop
Tecnologias previstas: Tauri + React.
Responsabilidades: interface, conversa, voz, animações e configurações.

### Backend
Tecnologia: Python + FastAPI.
Responsabilidades: orquestração da IA, contexto, ferramentas, validações e API local.

### Modelo de linguagem
Tecnologia: Ollama.
Modelo inicial disponível: qwen2.5:3b.
A escolha definitiva dependerá dos testes de qualidade e desempenho.

### Persistência
Tecnologia: SQLite.
Responsabilidades: conversas, mensagens, memórias, tarefas e configurações.

### Ferramentas
Módulos independentes, com parâmetros validados, permissões e registro de resultados.

## Princípios
- Interface separada do backend.
- Modelo substituível sem perder os dados.
- Nenhuma execução arbitrária de comandos sugeridos pela IA.
- Confirmação de ações sensíveis.
- Segredos fora do Git.
- Funcionamento local sempre que possível.
- Não declarar sucesso sem verificar a operação.
