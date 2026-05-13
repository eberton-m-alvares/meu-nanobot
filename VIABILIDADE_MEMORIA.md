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

## 3. Unificação de Identidade (Múltiplos Canais)
**Viabilidade: Média/Alta (Exige lógica de vinculação)**

Atualmente, o sistema diferencia sessões usando o formato `canal:id_do_chat` (ex: `telegram:12345` e `whatsapp:551199999999`). Para o bot, são duas pessoas diferentes. Para unificar identidades e rotear as sessões do Telegram e WhatsApp para o mesmo "cérebro", precisamos de um **Gerenciador de Identidades**.

### Solução Recomendada: Tabela de Roteamento de Identidade
Criar um roteador transparente:
- Quando uma mensagem chega do `telegram:12345`, o `IdentityManager` verifica um arquivo de mapeamento.
- Se não existir, ele cria um UUID (ex: `usr_abc123`) e atrela o `telegram:12345` a esse UUID.
- Se o usuário vincular sua conta do WhatsApp (através de um comando como `/link_conta`), o `whatsapp:9876` passará a apontar para o mesmo `usr_abc123`, carregando instantaneamente todas as memórias do Telegram.

---

## 4. Escalabilidade: Lidando com Milhares de Usuários de Forma Simples e Efetiva

Lidar com **milhares de usuários** muda a perspectiva de armazenamento. Embora os sistemas operacionais modernos consigam lidar com milhares de arquivos `.md` em uma pasta (`workspace/memory/users/`), isso se tornará lento para gerenciar e fazer backups.

### Soluções Simples e Efetivas para Escala:

#### Nível 1 (Custo zero, fácil implementação): SQLite
A forma mais simples, rápida e nativa do Python de resolver isso é abandonar os arquivos `.md` por usuário e usar um único arquivo de banco de dados **SQLite** (`memory.db`).
* **Vantagem:** Não requer instalar servidores (MySQL, Postgres). É apenas um arquivo que aguenta gigabytes de dados de forma extremamente rápida.
* **Tabelas simples:**
  * Tabela `Users` (id, uuid)
  * Tabela `Identities` (user_id, channel, chat_id) -> *Resolve a unificação de canais.*
  * Tabela `Memories` (user_id, content_long_term, history_log)
* O `MemoryStore` passaria a fazer um `SELECT` rápido ao invés de abrir arquivos `.md`. A memória global pode continuar sendo um `.md` para fácil edição manual.

#### Nível 2 (Foco em IA): Banco de Dados Vetorial Local (ChromaDB / LanceDB)
Se os históricos ficarem gigantescos, você não vai querer ler textos brutos. Um banco de dados vetorial como ChromaDB (que também roda local e não precisa de servidor externo) permite armazenar as memórias.
* **Como funciona:** Em vez de dar ao bot todo o `HISTORY.md` do usuário, o bot recebe *apenas* os pedaços de memória que são relevantes para a pergunta atual do usuário (isso se chama RAG - Retrieval-Augmented Generation).

#### Eles devem ser implementados juntos?
**Não necessariamente.** A melhor abordagem é iterativa:
- **Passo 1 (Apenas Nível 1 - SQLite):** Implemente primeiro apenas o SQLite. Use-o para gerenciar as identidades (unificar Telegram/WhatsApp) e salvar o `MEMORY.md` global e o `user_MEMORY.md` de cada usuário. Como as memórias de longo prazo (fatos importantes) devem ser enxutas (ex: bullet points curtos), o SQLite é perfeito para puxar esse texto e jogar no prompt inteiro.
- **Passo 2 (Nível 1 + Nível 2):** Se no futuro você quiser que o bot lembre de conversas passadas complexas (o `HISTORY.md` que ficou muito grande para o SQLite/Prompt), aí sim você adiciona o banco vetorial **ao lado** do SQLite. O SQLite continua gerenciando quem é o usuário e suas permissões/identidades, e o Banco Vetorial passa a ser o motor de busca para resgatar os trechos antigos do histórico de chat daquele usuário.

---

## 5. Consumo de Tokens (O grande gargalo financeiro)

Sempre que o usuário envia um "Oi", o bot envia o "Oi" + todo o Histórico recente + a Memória Global + a Memória do Usuário para o LLM (OpenAI, Anthropic, etc). As APIs cobram por **quantidade de texto enviado** (Tokens).

### O Problema
Se você injetar a Memória Global (`MEMORY.md` = 500 tokens) + a Memória do Usuário (`user_MEMORY.md` = 1000 tokens) em **todas** as mensagens, e você tiver milhares de usuários enviando milhares de mensagens por dia, **o custo da API vai disparar**.

### Como mitigar o Consumo de Tokens de forma efetiva:

1. **Agressividade na Consolidação (Foco em Fatos, não Histórias):**
   * A Memória de Longo Prazo do usuário (`user_MEMORY.md`) deve ser um "Bullet Point" de fatos estritos.
   * *Ruim (muitos tokens):* "O usuário me contou ontem que estava indo para a padaria comprar pão francês porque ele prefere o pão francês ao pão de forma, e depois foi trabalhar no seu projeto Python."
   * *Bom (poucos tokens):* "- Gosta de pão francês.\n- Programa em Python."
   * O prompt que faz a "consolidação de memória" em background deve ser instruído a ser **extremamente sucinto** ao atualizar a memória de longo prazo do usuário.

2. **Limite Rígido de Tamanho de Memória:**
   * O `ContextBuilder` deve cortar a memória injetada se ela passar de um certo tamanho (ex: limitar a `user_MEMORY` a no máximo 800 tokens). O que for mais antigo ou menos importante deve ser sobreposto pelo agente consolidador.

3. **Injeção de Memória Dinâmica (O futuro do seu projeto):**
   * Para escalar economicamente com milhares de usuários, a melhor solução é não enviar a memória de longo prazo toda vez.
   * Quando o usuário manda uma mensagem, um sistema rápido (como Embeddings/Vector DB) busca na memória se há algo relevante.
   * Exemplo: Se o usuário diz "Qual o clima?", não precisamos injetar a memória de que ele "Tem um cachorro chamado Rex". O bot injeta a memória apenas quando a pergunta for relacionada.

### Conclusão e Próximo Passo
A transição para **SQLite** é o caminho mais óbvio, simples e profissional para você lidar com os múltiplos canais, as identidades cruzadas e armazenar a memória individual de milhares de usuários. Para gerenciar os tokens, o segredo será criar uma consolidação de memória que gere resumos muito curtos e diretos.
