# H.U.G.O. — Plano Mestre

## Estado atual

Fase: 1 a 3 — Preparação, núcleo de inteligência e memória persistente
Status: em andamento
## Etapa 1 — Ambiente e organização

- [x] Inicializar repositório Git
- [x] Criar estrutura inicial de pastas
- [x] Criar `.gitignore`
- [ ] Configurar Git no PATH permanentemente
- [x] Instalar Python 3.13
- [x] Criar ambiente virtual Python
- [ ] Configurar VS Code para depuração
- [x] Registrar primeiro commit
- [x] Publicar repositório no GitHub

## Etapa 2 — Núcleo de inteligência

- [x] Configurar FastAPI
- [x] Conectar ao Ollama
- [x] Configurar o modelo `qwen2.5:3b`
- [x] Implementar endpoint de conversa
- [x] Tratar erros de conexão e respostas vazias
- [x] Configurar variáveis de ambiente
- [x] Validar o limite de contexto do Ollama
- [ ] Validar a conversa natural com o modelo real
- [ ] Testar indisponibilidade do Ollama em execução real

## Etapa 3 — Memória persistente
- [x] Criar banco SQLite
- [x] Persistir conversas e mensagens
- [x] Implementar operações de memórias de longo prazo
- [x] Implementar sugestões de memória com aprovação ou rejeição
- [ ] Implementar e validar busca contextual
- [ ] Testar persistência entre reinicializações
## Etapa 4 — Ferramentas

- [ ] Criar registro de ferramentas
- [ ] Implementar seleção de ferramentas pela IA
- [ ] Validar parâmetros e permissões
- [ ] Implementar confirmações e logs

## Etapa 5 — Interface desktop

- [ ] Criar aplicação React + Tauri
- [ ] Criar tela principal e navegação
- [ ] Criar esfera animada
- [ ] Integrar conversa e cartões dinâmicos

## Etapa 6 — Execução diária

- [ ] Gerenciar o núcleo pelo aplicativo
- [ ] Implementar inicialização e encerramento seguros
- [ ] Criar instalador Windows
- [ ] Testar sem terminal manual

## Etapa 7 — Voz

- [ ] Reconhecimento em português brasileiro
- [ ] Síntese de voz
- [ ] Ativação pelo botão
- [ ] Palavra de ativação Hugo

## Etapa 8 — Agenda e tarefas

- [ ] Calendário mensal, semanal e diário
- [ ] Criar, editar e concluir tarefas
- [ ] Recorrências e notificações
- [ ] Interpretar linguagem natural

## Etapa 9 — Gmail

- [ ] Autorização Google
- [ ] Leitura e resumos
- [ ] Rascunhos e respostas
- [ ] Envio com confirmação

## Etapa 10 — Pesquisa e briefing

- [ ] Pesquisa web com fontes
- [ ] Clima com autorização
- [ ] Briefing matinal

## Etapa 11 — Módulos pessoais

- [ ] Treinos
- [ ] Importação de investimentos
- [ ] Música

## Etapa 12 — Segurança e lançamento

- [ ] Credenciais protegidas
- [ ] Backup e restauração testados
- [ ] Testes automatizados
- [ ] Avaliar consumo de memória
- [ ] Gerar instalador e documentar atualizações

## Validação automatizada

- [x] Criar testes automatizados para o backend
- [x] Validar os fluxos de conversas, memórias e sugestões
- [x] Validar o envio do parâmetro de contexto ao Ollama
- [x] Validar configurações inválidas do limite de contexto
- [x] Obter 31 testes aprovados

## Regra de conclusão

Uma etapa só será marcada como concluída depois da implementação, dos testes e da verificação do resultado.