# 🤖 Nanobot AI Framework: Agente de IA Proativo e Ultra-Leve
<p align="center">
  <img src="nanobot_logo.png" alt="Logo Oficial do Nanobot AI Agent Framework" width="300">
</p>

![Diagrama de Arquitetura do Nanobot AI Agent Framework](nanobot_arch.png)

O **Nanobot** (ou `nanobot-ai`) é um framework de agentes de Inteligência Artificial de alto desempenho, projetado para ser minimalista, rápido e altamente autônomo. Ao contrário de chatbots convencionais, o Nanobot opera como um **runtime proativo**, capaz de executar tarefas agendadas, gerenciar arquivos no servidor e interagir através de múltiplos canais de comunicação.

Este repositório documenta a implementação segura, a estrutura de diretórios e as melhores práticas de operação do Nanobot via Docker.
## ⚖️ Créditos e Licença

Este repositório é uma implementação customizada, traduzida e focada em deploy via Docker do projeto original **Nanobot**.

- **Projeto Original:** [HKUDS/nanobot](https://github.com/HKUDS/nanobot)
- **Licença:** Este projeto opera sob a licença [MIT](LICENSE), preservando todos os direitos dos autores originais da arquitetura.
---

## 🚀 Principais Funcionalidades

- **Navegação Web em Tempo Real:** Integração nativa com a **Brave Search API** para fornecer respostas baseadas em dados atuais da internet.
- **Autonomia Proativa:** Possui sistemas de `heartbeat` e tarefas agendadas (`cron`) que permitem ao agente agir sem necessidade de um comando imediato do usuário.
- **Arquitetura Sandboxed:** Execução de comandos, scripts e manipulação de arquivos isolada dentro do diretório `/workspace`.
- **Protocolo MCP (Model Context Protocol):** Suporte total ao protocolo da Anthropic para conexão plug-and-play com ferramentas externas.
- **Multicanal:** Capaz de se conectar ao Telegram, Discord, WhatsApp e Slack através de sua Gateway API interna.

---

## 🏗️ Estrutura do Projeto

| Pasta/Arquivo | Descrição |
| :--- | :--- |
| `nanobot/` | Core do agente desenvolvido em Python (lógica principal). |
| `workspace/` | Área de trabalho segura onde o robô executa comandos e armazena arquivos temporários. |
| `data/` | Onde reside a memória de longo prazo, histórico de sessões e banco de dados vetorial. |
| `bridge/` | Conectores de tradução para APIs de mensageria externas. |
| `docker-compose.yml` | Orquestração do container e definição de volumes/portas. |

---

## 🛠️ Guia de Instalação e Configuração

### 1. Pré-requisitos
- Docker e Docker Compose instalados.
- Chave de API da Brave (Opcional, para navegação web).
- Acesso a um modelo LLM (OpenAI, Anthropic, ou local via Ollama).

### 2. Configuração de Variáveis de Ambiente
Para garantir a segurança, nunca exponha suas chaves no código. Utilize um arquivo `.env` na raiz do projeto:

```bash
# Exemplo de conteúdo do .env
BRAVE_API_KEY=seu_token_aqui
TIMEZONE=America/Sao_Paulo
PORTA_GATEWAY=18790
```

### 3. Deploy via Docker Compose
Certifique-se de que o seu `docker-compose.yml` está configurado para ler as variáveis de ambiente:

```yaml
version: '3.8'

services:
  nanobot:
    container_name: nanobot
    build: .
    restart: unless-stopped
    volumes:
      - ./data:/root/.nanobot
      - ./workspace:/root/workspace
    ports:
      - "127.0.0.1:18790:18790" # Acesso restrito apenas ao host local
    environment:
      - TZ=${TIMEZONE}
      - BRAVE_API_KEY=${BRAVE_API_KEY}
    command: ["gateway"]
```

---

## 🔒 Segurança e Privacidade

Este setup foi planejado com foco em segurança cibernética:
1. **Localhost Binding:** A porta do gateway (`18790`) está vinculada apenas ao endereço `127.0.0.1`, impedindo que a API fique exposta à internet pública sem um proxy reverso.
2. **Proteção de Dados:** O arquivo `.gitignore` impede o versionamento acidental do diretório `data/` (memória privada e banco de dados) e do arquivo `.env` (chaves de API).
3. **Isolamento de Processos:** O agente tem permissões de escrita limitadas apenas ao volume montado em `workspace`, protegendo o servidor host.

---

## 🧠 Personalização de Identidade (AIEOS)

A "personalidade" e o comportamento do Nanobot são moldados por arquivos Markdown localizados na pasta `data/`:
- **IDENTITY.md**: Define quem o robô é e sua função principal.
- **SOUL.md**: Define os valores éticos, o tom de voz e as restrições comportamentais.
- **USER.md**: Armazena informações que o bot aprende sobre o usuário para personalização contínua.

---

## 🔧 Comandos Úteis de Manutenção

**Acompanhar o processamento do bot em tempo real (Logs):**
```bash
docker logs -f nanobot
```

**Reiniciar o serviço após alterações de configuração (.env ou docker-compose):**
```bash
docker-compose up -d --force-recreate
```

**Executar um comando direto via CLI do agente (Terminal):**
```bash
docker exec -it nanobot nanobot agent -m "Olá, descreva seu status atual."
```

---
*Este repositório é uma documentação independente e segura para uso do framework [HKUDS/nanobot](https://github.com/HKUDS/nanobot).*
