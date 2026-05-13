# Análise de Viabilidade: Memória Individual por Usuário (e Global)

## 1. Visão Geral da Arquitetura Atual
Atualmente, o Nanobot possui uma memória dividida em duas camadas (curto e longo prazo):
- **Curto prazo:** `SessionManager` armazena mensagens por `channel:chat_id` em arquivos JSONL no diretório `~/.nanobot/sessions/`.
- **Longo prazo:** `MemoryStore` utiliza arquivos globais em `workspace/memory/` (`MEMORY.md` e `HISTORY.md`). A consolidação de memória processa o histórico de curto prazo quando fica muito grande, resumindo-o e atualizando os arquivos globais.

Esta arquitetura funciona bem para um uso onde o bot atende uma única pessoa (ou pequeno grupo) e todos compartilham o mesmo contexto.

## 2. Viabilidade da Memória Dupla (Global + Por Usuário)
**Viabilidade: Alta.**

É plenamente possível e recomendável implementar um modelo híbrido onde o agente possui:
1. **Memória Global:** Fatos sobre o próprio agente, diretrizes do sistema e aprendizados gerais (`MEMORY.md` global).
2. **Memória Específica do Usuário:** Preferências do usuário, histórico do usuário, contexto de conversas passadas (`user_MEMORY.md` e `user_HISTORY.md`).

### Como seria implementado tecnicamente:
- O `MemoryStore` seria alterado para receber um identificador de usuário (`user_id`).
- A estrutura de arquivos seria algo como:
  - `workspace/memory/global_MEMORY.md`
  - `workspace/memory/global_HISTORY.md`
  - `workspace/memory/users/<user_id>/MEMORY.md`
  - `workspace/memory/users/<user_id>/HISTORY.md`
- No `ContextBuilder` (`nanobot/agent/context.py`), durante a montagem do prompt (`build_system_prompt`), o sistema injetaria tanto a memória global quanto a memória lida do diretório específico daquele usuário.
- Durante a *consolidação de memória* (`_consolidate_memory` em `nanobot/agent/loop.py`), o prompt do LLM precisaria ser ajustado para que o modelo pudesse atualizar arquivos diferentes (ex: retornar JSON com atualizações para fatos globais X fatos do usuário).

## 3. Unificação de Identidade (Múltiplos Canais)
**Viabilidade: Média/Alta (Exige lógica de vinculação)**

Atualmente, o sistema diferencia sessões usando o formato `canal:id_do_chat` (ex: `telegram:12345` e `whatsapp:551199999999`). Para o bot, são duas pessoas diferentes.

Para unificar essas identidades e fazer o bot reconhecer que o usuário do Telegram é a mesma pessoa no WhatsApp, precisamos criar um "Sistema de Vinculação de Identidades" (Identity Linking).

### Opção A: Vinculação Ativa (Comando)
O usuário pode associar suas contas através de um token ou comando.
- **Fluxo:** O usuário fala com o bot no Telegram e pede para unificar contas (ex: `/link`). O bot gera um token temporário (ex: `ABC-123`). O usuário vai no WhatsApp, envia o comando `/link ABC-123`, e o bot funde os perfis.
- **Implementação:** Precisaríamos de um pequeno banco de dados ou arquivo JSON (`users.json`) mapeando um UUID interno (`user_123`) para múltiplos endpoints (`["telegram:12345", "whatsapp:551199999999"]`).

### Opção B: Vinculação Passiva (Por número de telefone)
- O WhatsApp e o Telegram possuem números de telefone (embora o do Telegram nem sempre seja público na API, dependendo das configurações de privacidade do usuário). Se for possível extrair o número de ambos, eles poderiam ser vinculados automaticamente.
- **Problema:** Nem sempre temos o número de telefone em todos os canais (ex: Discord, Slack).

### Solução Recomendada: Tabela de Roteamento de Identidade
Recomendo criar um "Gerenciador de Identidades" que faz o roteamento transparente.
- Quando uma mensagem chega do `telegram:12345`, o `IdentityManager` verifica em um arquivo `identities.json`.
- Se não existir, ele cria um UUID (ex: `usr_abc123`) e atrela o `telegram:12345` a esse UUID.
- Todas as operações de *Memory* utilizarão o `usr_abc123`.
- Se o usuário futuramente fizer o processo de *link* com o WhatsApp, o `whatsapp:9876` passará a apontar para o mesmo `usr_abc123`, carregando instantaneamente todas as memórias.

## 4. Impacto e Riscos
- **Consumo de Tokens:** Injetar a memória global + memória do usuário consumirá mais contexto na janela do LLM. É importante que a consolidação seja agressiva para manter o `MEMORY.md` de cada usuário enxuto.
- **Escalabilidade:** Se o bot tiver milhares de usuários, criar milhares de pastas e arquivos no disco (`workspace/memory/users/`) é factível, mas pode exigir a migração futura para um banco de dados (como SQLite) no lugar de arquivos de texto puro. No entanto, para escala de dezenas/centenas de usuários, o disco (`.md`) lidará sem problemas.
- **Prompt de Consolidação:** Atualmente, a consolidação é simples. Com duas memórias (Global e Usuário), o LLM que faz a consolidação precisará ser mais inteligente para decidir se uma nova informação ("A capital da França é Paris") deve ir para a Global ou se ("Meu nome é João e tenho 3 cachorros") deve ir para a do Usuário.

## Conclusão
A implementação é totalmente viável na arquitetura atual do Nanobot.
Os passos necessários seriam:
1. Criar um mapeamento (JSON simples) de `canal:id` -> `UUID_Usuario`.
2. Refatorar `MemoryStore` para aceitar `UUID_Usuario` e gerenciar as pastas de usuários.
3. Atualizar `ContextBuilder` para ler os dois níveis de memória.
4. Ajustar `AgentLoop._consolidate_memory` para processar e salvar a memória do usuário de forma inteligente.
