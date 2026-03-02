# 🤖 Nanobot AI Framework: Elite Command Center v2.5

<p align="center">
  <img src="nanobot_logo.png" alt="Logo Oficial do Nanobot AI Agent Framework - Agente de IA Autônomo" width="300">
</p>

![Arquitetura do Nanobot AI Agent Framework](nanobot_arch.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)
![Docker Ready](https://img.shields.io/badge/docker-ready-cyan.svg)
![UI](https://img.shields.io/badge/UI-Elite%20Dashboard-red.svg)
![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)

O **Nanobot AI Framework** é um runtime de agentes de Inteligência Artificial de alto desempenho, focado em minimalismo, proatividade e segurança. Esta versão customizada eleva o projeto original ao nível de **Central de Comando**, integrando uma interface visual avançada para gestão de operações táticas.

---

## 📑 Índice
1. [Introdução](#-introdução)
2. [Elite Command Center (Exclusivo)](#-elite-command-center-exclusivo)
3. [Funcionalidades Principais](#-funcionalidades-principais)
4. [Estrutura do Projeto](#-estrutura-do-projeto)
5. [Guia de Instalação e Configuração](#-guia-de-instalação-e-configuração)
6. [Personalização do Agente (AIEOS)](#-personalização-do-agente-aieos)
7. [Segurança e Privacidade](#-segurança-e-privacidade)
8. [Créditos e Licença](#-créditos-e-licença)

---

## 🌟 Introdução

O Nanobot não é apenas um chatbot; é um **Agente Autônomo** capaz de executar tarefas agendadas, gerenciar arquivos no servidor e realizar buscas proativas. Esta implementação foi desenhada para rodar de forma privada em VPS, garantindo total controle sobre seus dados e o comportamento da IA.

---

## 🖥️ Elite Command Center (Exclusivo)

Esta versão inclui uma interface administrativa desenvolvida em **Streamlit**, oferecendo controle total sem a necessidade de terminal constante:

- **💬 Chat Master Persistente:** Histórico de conversas salvo localmente (JSON) no volume `workspace`, permitindo continuidade entre sessões.
- **🧠 Thought Stream (Live):** Monitoramento em tempo real do "fluxo de consciência" do robô. Observe o raciocínio interno (Chain of Thought) enquanto o agente processa.
- **⚙️ Editor de Alma Visual:** Interface amigável para modificar diretrizes de comportamento (`IDENTITY.md`, `SOUL.md`).
- **📊 Telemetria em Tempo Real:** Gráficos de monitoramento de uso de CPU e RAM da VPS integrados ao painel.
- **🛡️ Login Blindado:** Acesso protegido por autenticação via variáveis de ambiente no Docker.

---

## 🚀 Funcionalidades Principais

- **Navegação Web Real-Time:** Integração nativa com a **Brave Search API**.
- **Autonomia Proativa:** Suporte a tarefas agendadas (`cron`) e monitoramento contínuo (`heartbeat`).
- **Arquitetura Sandboxed:** Execução segura de comandos e scripts isolados no diretório `/workspace`.
- **Conectividade Multicanal:** Suporte para Telegram, Discord, WhatsApp e Slack via Gateway API.
- **Protocolo MCP:** Conectividade plug-and-play com ferramentas externas via Model Context Protocol.

---

## 🏗️ Estrutura do Projeto

| Pasta/Arquivo | Descrição |
| :--- | :--- |
| `nanobot/` | Core do agente desenvolvido em Python. |
| `dashboard.py` | Código-fonte do Elite Command Center. |
| `workspace/` | Área de trabalho segura, memórias e histórico de chat. |
| `data/` | Configurações de canais (Telegram) e tokens de API. |
| `docker-compose.yml` | Orquestração do ecossistema via Docker. |

---

## 🛠️ Guia de Instalação e Configuração

### 1. Pré-requisitos
- Docker & Docker Compose instalados.
- Chave de API de um provedor LLM (OpenAI, Anthropic, ou Local via Ollama).
- Chave de API da Brave (Opcional, para busca web).

### 2. Configuração do Ambiente
Crie as credenciais de segurança no seu arquivo `docker-compose.yml` local (Este arquivo está protegido no `.gitignore`):

```yaml
environment:
  - DASHBOARD_USER=seu_usuario
  - DASHBOARD_PASS=sua_senha_secreta
  - BRAVE_API_KEY=seu_token_aqui
```

### 3. Deploy
```bash
docker compose up -d
```
O painel administrativo estará disponível em: `http://seu-ip-vps:8501`

---

## 🧠 Personalização do Agente (AIEOS)

A personalidade do Nanobot é definida por arquivos Markdown na pasta `workspace/`:
- **`IDENTITY.md`**: Define quem o robô é (ex: "Você é um Engenheiro de Elite").
- **`SOUL.md`**: Define o tom de voz e regras éticas.
- **`USER.md`**: Memória persistente sobre o usuário para personalização profunda.

---

## 🔒 Segurança e Privacidade

Este projeto prioriza a proteção de dados:
1. **Histórico Privado:** As conversas são armazenadas localmente no servidor e nunca são enviadas para nuvens de terceiros para log.
2. **Docker Isolation:** O agente tem acesso restrito apenas aos volumes montados, protegendo o sistema host.
3. **Proteção de Segredos:** O arquivo `docker-compose.yml` real e a pasta `data/` estão no `.gitignore` para evitar vazamentos acidentais em repositórios públicos.

---

## ⚖️ Créditos e Licença

Este repositório é uma implementação customizada, focada em segurança e interface tática, baseada no projeto original **Nanobot**.

- **Projeto Original:** [HKUDS/nanobot](https://github.com/HKUDS/nanobot)
- **Melhorias e Interface:** [Eberton M. Álvares](https://github.com/eberton-m-alvares)
- **Licença:** [MIT](LICENSE)

---
*Transformando Inteligência Artificial em uma ferramenta tática de alta performance.*
