import streamlit as st
import docker
import os
import json
import psutil
import time
import threading
from datetime import datetime

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="NANOBOT CORE",
    page_icon="🐈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600&family=Syne:wght@400;700;800&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background-color: #080b10;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #0c1018 !important;
    border-right: 1px solid #1a2332;
}
[data-testid="stSidebar"] * { color: #8899aa !important; }
[data-testid="stSidebar"] .stRadio label { 
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ── Scrub native chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
.stDeployButton { display: none; }

/* ── Typography ── */
h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    letter-spacing: -0.02em;
    color: #e2e8f0 !important;
}

/* ── Custom components ── */
.nano-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 800;
    color: #38bdf8;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.25rem;
}

.nano-label {
    font-size: 0.65rem;
    color: #4a5568;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.15rem;
}

.status-dot {
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 2s infinite;
}
.dot-online { background: #22c55e; box-shadow: 0 0 8px #22c55e; }
.dot-offline { background: #ef4444; }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* ── Log box ── */
.log-box {
    background: #050709;
    border: 1px solid #1a2332;
    border-left: 2px solid #22c55e;
    border-radius: 4px;
    padding: 12px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #4ade80;
    height: 460px;
    overflow-y: auto;
    white-space: pre-wrap;
    line-height: 1.6;
}

/* ── Chat ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border-bottom: 1px solid #0f1a24;
    padding: 8px 0;
}

/* ── Metrics ── */
.metric-card {
    background: #0c1018;
    border: 1px solid #1a2332;
    border-radius: 6px;
    padding: 16px;
    text-align: center;
}
.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    color: #38bdf8;
}
.metric-bar {
    height: 3px;
    background: #1a2332;
    border-radius: 2px;
    margin-top: 8px;
    overflow: hidden;
}
.metric-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.5s ease;
}

/* ── Skill cards ── */
.skill-card {
    background: #0c1018;
    border: 1px solid #1a2332;
    border-radius: 6px;
    padding: 12px 14px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: border-color 0.2s;
}
.skill-card:hover { border-color: #38bdf8; }
.skill-name {
    font-family: 'Syne', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    color: #e2e8f0;
}
.skill-desc {
    font-size: 0.68rem;
    color: #4a5568;
    margin-top: 4px;
    line-height: 1.5;
}

/* ── Buttons ── */
.stButton > button {
    background: transparent !important;
    border: 1px solid #1a2332 !important;
    color: #8899aa !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    border-color: #38bdf8 !important;
    color: #38bdf8 !important;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea, .stSelectbox select {
    background: #0c1018 !important;
    border: 1px solid #1a2332 !important;
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    border-radius: 4px !important;
}
.stChatInput textarea {
    background: #0c1018 !important;
    border: 1px solid #1a2332 !important;
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ── Divider ── */
hr { border-color: #1a2332 !important; }

/* ── Toggle ── */
.stToggle label { font-size: 0.72rem !important; color: #4a5568 !important; }

/* ── Login ── */
.login-wrap {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; min-height: 80vh; gap: 8px;
}
.login-logo {
    font-family: 'Syne', sans-serif;
    font-size: 3rem; font-weight: 800;
    color: #38bdf8;
    letter-spacing: -0.04em;
    margin-bottom: 1rem;
}
.login-sub {
    font-size: 0.65rem; color: #2a3a4a;
    letter-spacing: 0.2em; text-transform: uppercase;
    margin-top: -1.2rem; margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
HISTORY_PATH = "workspace/chat_history.json"
WORKSPACE    = "workspace"
SKILLS_DIR   = "skills"

def save_history():
    os.makedirs(WORKSPACE, exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(st.session_state.messages, f, ensure_ascii=False, indent=2)

def load_history():
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def ts():
    return datetime.now().strftime("%H:%M:%S")

def color_for(pct):
    if pct < 60:  return "#22c55e"
    if pct < 85:  return "#f59e0b"
    return "#ef4444"

def get_skills():
    """Lista skills disponíveis (arquivos .md na pasta skills)"""
    skills = []
    for d in [SKILLS_DIR, f"nanobot/{SKILLS_DIR}", "."]:
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".md") and f not in ["README.md", "COMMUNICATION.md"]:
                    skills.append({"name": f.replace(".md","").replace("_"," ").title(), "file": os.path.join(d, f)})
    return skills

def get_tool_files():
    """Lista tools Python disponíveis"""
    tools = []
    for d in ["nanobot/agent/tools", "agent/tools"]:
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".py") and not f.startswith("_"):
                    tools.append({"name": f.replace(".py",""), "file": os.path.join(d, f)})
    return tools


# ─────────────────────────────────────────
# DOCKER
# ─────────────────────────────────────────
@st.cache_resource(ttl=30)
def get_docker_client():
    try:
        return docker.from_env()
    except Exception:
        return None

def get_container(client):
    if not client:
        return None
    try:
        c = client.containers.get("nanobot")
        return c if c.status == "running" else None
    except Exception:
        return None

def run_agent(container, prompt: str) -> str:
    if not container:
        return "⚠️  Container offline — inicie com `docker compose up -d`"
    try:
        # Escapa aspas simples no prompt
        safe = prompt.replace("'", "'\\''")
        result = container.exec_run(f"nanobot agent -m '{safe}'", demux=False)
        return result.output.decode("utf-8", errors="replace").strip()
    except Exception as e:
        return f"Erro ao executar: {e}"

def get_logs(container, lines=60) -> str:
    if not container:
        return "[container offline]"
    try:
        return container.logs(tail=lines).decode("utf-8", errors="replace")
    except Exception:
        return "[erro ao ler logs]"


# ─────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────
def check_password():
    if st.session_state.get("authenticated"):
        return True

    st.markdown("""
    <div class='login-wrap'>
        <div class='login-logo'>🐈 NANOBOT</div>
        <div class='login-sub'>Core Command Interface</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        u = st.text_input("Username", placeholder="admin", label_visibility="collapsed")
        p = st.text_input("Token", type="password", placeholder="security token", label_visibility="collapsed")
        if st.button("AUTHENTICATE →", use_container_width=True):
            eu = os.getenv("DASHBOARD_USER", "admin").strip()
            ep = os.getenv("DASHBOARD_PASS", "admin123").strip()
            if u.strip() == eu and p.strip() == ep:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Access denied.")
    return False

if not check_password():
    st.stop()


# ─────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = load_history()
if "live_logs" not in st.session_state:
    st.session_state.live_logs = False


# ─────────────────────────────────────────
# DOCKER INIT
# ─────────────────────────────────────────
docker_client = get_docker_client()
container     = get_container(docker_client)
is_online     = container is not None


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 8px 0 16px'>
        <div style='font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;color:#38bdf8;letter-spacing:-0.02em'>
            🐈 NANOBOT
        </div>
        <div style='font-size:0.6rem;color:#2a3a4a;letter-spacing:0.2em;text-transform:uppercase;margin-top:2px'>
            Core Command Interface
        </div>
    </div>
    """, unsafe_allow_html=True)

    dot_cls = "dot-online" if is_online else "dot-offline"
    status_txt = "ONLINE" if is_online else "OFFLINE"
    st.markdown(f"""
    <div style='margin-bottom:16px;font-size:0.72rem;letter-spacing:0.1em'>
        <span class='status-dot {dot_cls}'></span>{status_txt}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    menu = st.radio(
        "nav",
        ["Terminal", "Skills & Tools", "Identidade", "Telemetria"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    msg_count = len(st.session_state.messages)
    st.markdown(f"<div class='nano-label'>Mensagens</div><div style='color:#38bdf8;font-size:1.1rem;font-weight:700'>{msg_count}</div>", unsafe_allow_html=True)

    st.markdown("")
    if st.button("🗑  Limpar histórico"):
        st.session_state.messages = []
        save_history()
        st.rerun()

    if st.button("🔒 Logout"):
        st.session_state["authenticated"] = False
        st.rerun()


# ─────────────────────────────────────────
# ── TERMINAL
# ─────────────────────────────────────────
if menu == "Terminal":
    col_chat, col_logs = st.columns([0.55, 0.45], gap="large")

    with col_chat:
        st.markdown("<div class='nano-header'>Terminal Tático</div>", unsafe_allow_html=True)
        st.markdown("<div class='nano-label'>conversa com o agente</div>", unsafe_allow_html=True)

        chat_box = st.container(height=460, border=False)
        with chat_box:
            for msg in st.session_state.messages:
                icon = "🐈" if msg["role"] == "assistant" else "👤"
                with st.chat_message(msg["role"], avatar=icon):
                    st.markdown(msg["content"])

        if prompt := st.chat_input("Digite o comando..."):
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Mostra mensagem do usuário imediatamente
            with chat_box:
                with st.chat_message("user", avatar="👤"):
                    st.markdown(prompt)

            # Chama o agente
            with chat_box:
                with st.chat_message("assistant", avatar="🐈"):
                    with st.spinner("processando..."):
                        response = run_agent(container, prompt)
                    st.markdown(response)

            st.session_state.messages.append({"role": "assistant", "content": response})
            save_history()
            st.rerun()

    with col_logs:
        st.markdown("<div class='nano-header'>Thought Stream</div>", unsafe_allow_html=True)

        col_a, col_b = st.columns([1, 1])
        with col_a:
            live = st.toggle("Live", value=st.session_state.live_logs, help="Atualiza logs a cada 5s")
            st.session_state.live_logs = live
        with col_b:
            lines = st.selectbox("linhas", [30, 60, 100], index=1, label_visibility="collapsed")

        log_content = get_logs(container, lines)
        st.markdown(f'<div class="log-box">{log_content}</div>', unsafe_allow_html=True)

        if live and is_online:
            time.sleep(5)
            st.rerun()


# ─────────────────────────────────────────
# ── SKILLS & TOOLS
# ─────────────────────────────────────────
elif menu == "Skills & Tools":
    st.markdown("<div class='nano-header'>Skills & Tools</div>", unsafe_allow_html=True)
    st.markdown("<div class='nano-label'>arquitetura do agente</div>", unsafe_allow_html=True)
    st.markdown("")

    tab_skills, tab_tools, tab_editor = st.tabs(["📋 Skills (.md)", "🔧 Tools (.py)", "✏️ Editor"])

    with tab_skills:
        skills = get_skills()
        if not skills:
            st.info("Nenhuma skill encontrada. Verifique se a pasta `skills/` existe.")
        else:
            st.markdown(f"<div class='nano-label'>{len(skills)} skill(s) carregada(s)</div>", unsafe_allow_html=True)
            st.markdown("")
            for s in skills:
                with st.expander(f"📄 {s['name']}"):
                    try:
                        with open(s["file"], "r") as f:
                            content = f.read()
                        st.code(content, language="markdown")
                        st.caption(f"Arquivo: `{s['file']}`")
                    except:
                        st.warning("Não foi possível ler o arquivo.")

        # Criar nova skill
        st.markdown("---")
        st.markdown("<div class='nano-label'>criar nova skill</div>", unsafe_allow_html=True)
        new_skill_name = st.text_input("Nome da skill (ex: meta_ads)", placeholder="meta_ads")
        new_skill_content = st.text_area(
            "Conteúdo (.md)",
            height=200,
            placeholder="# Meta Ads Skill\n\nQuando o usuário perguntar sobre campanhas...",
        )
        if st.button("💾 Criar Skill"):
            if new_skill_name and new_skill_content:
                path = f"skills/{new_skill_name}.md"
                os.makedirs("skills", exist_ok=True)
                with open(path, "w") as f:
                    f.write(new_skill_content)
                st.success(f"Skill criada em `{path}`")
                st.rerun()

    with tab_tools:
        tools = get_tool_files()
        if not tools:
            st.info("Nenhuma tool encontrada. Verifique `nanobot/agent/tools/`.")
        else:
            st.markdown(f"<div class='nano-label'>{len(tools)} tool(s) disponível(is)</div>", unsafe_allow_html=True)
            st.markdown("")
            for t in tools:
                with st.expander(f"🔧 {t['name']}"):
                    try:
                        with open(t["file"], "r") as f:
                            code = f.read()
                        st.code(code, language="python")
                        st.caption(f"Arquivo: `{t['file']}`")
                    except:
                        st.warning("Não foi possível ler o arquivo.")

        # Criar nova tool
        st.markdown("---")
        st.markdown("<div class='nano-label'>criar nova tool</div>", unsafe_allow_html=True)
        new_tool_name = st.text_input("Nome da tool (ex: meta_api)", placeholder="meta_api")
        new_tool_content = st.text_area(
            "Código Python",
            height=250,
            placeholder='def meta_api(endpoint: str, params: dict) -> dict:\n    """Chama a API do Meta Ads"""\n    import requests\n    ...',
        )
        if st.button("💾 Criar Tool"):
            if new_tool_name and new_tool_content:
                os.makedirs("nanobot/agent/tools", exist_ok=True)
                path = f"nanobot/agent/tools/{new_tool_name}.py"
                with open(path, "w") as f:
                    f.write(new_tool_content)
                st.success(f"Tool criada em `{path}`")
                st.rerun()

    with tab_editor:
        st.markdown("<div class='nano-label'>editar arquivo de configuração</div>", unsafe_allow_html=True)
        config_path = os.path.expanduser("~/.nanobot/config.json")
        config_content = ""
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config_content = f.read()
        else:
            config_content = json.dumps({
                "providers": {"openrouter": {"apiKey": "sk-or-v1-xxx"}},
                "agents": {"defaults": {"model": "anthropic/claude-opus-4-5"}},
                "channels": {"telegram": {"enabled": False, "token": "", "allowFrom": []}},
                "meta": {"token": "", "account_id": ""}
            }, indent=2)

        edited = st.text_area("config.json", value=config_content, height=400)
        if st.button("💾 Salvar config.json"):
            try:
                json.loads(edited)  # valida JSON antes de salvar
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, "w") as f:
                    f.write(edited)
                st.success("Salvo com sucesso!")
            except json.JSONDecodeError as e:
                st.error(f"JSON inválido: {e}")


# ─────────────────────────────────────────
# ── IDENTIDADE
# ─────────────────────────────────────────
elif menu == "Identidade":
    st.markdown("<div class='nano-header'>Alma & Identidade</div>", unsafe_allow_html=True)
    st.markdown("<div class='nano-label'>define o comportamento do agente</div>", unsafe_allow_html=True)
    st.markdown("")

    IDENTITY_FILES = {
        "IDENTITY.md": "Personalidade e tom do agente",
        "SOUL.md":     "Valores e princípios base",
        "USER.md":     "Preferências e contexto do usuário",
        "AGENTS.md":   "Configuração de sub-agentes",
    }

    tabs = st.tabs(list(IDENTITY_FILES.keys()))
    for tab, (fname, desc) in zip(tabs, IDENTITY_FILES.items()):
        with tab:
            path = f"{WORKSPACE}/{fname}"
            st.caption(desc)
            content = ""
            if os.path.exists(path):
                with open(path, "r") as f:
                    content = f.read()
            else:
                content = f"# {fname.replace('.md','')}\n\n"

            new_content = st.text_area("", value=content, height=420, label_visibility="collapsed")
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💾 Salvar", key=f"save_{fname}"):
                    os.makedirs(WORKSPACE, exist_ok=True)
                    with open(path, "w") as f:
                        f.write(new_content)
                    st.success(f"{fname} salvo!")


# ─────────────────────────────────────────
# ── TELEMETRIA
# ─────────────────────────────────────────
elif menu == "Telemetria":
    st.markdown("<div class='nano-header'>Telemetria do Sistema</div>", unsafe_allow_html=True)
    st.markdown("<div class='nano-label'>status da VPS em tempo real</div>", unsafe_allow_html=True)
    st.markdown("")

    auto_refresh = st.toggle("Auto-refresh (10s)", value=False)

    cpu  = psutil.cpu_percent(interval=0.5)
    ram  = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net  = psutil.net_io_counters()

    # Métricas principais
    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        (c1, "CPU", f"{cpu:.1f}%", cpu),
        (c2, "RAM", f"{ram.percent:.1f}%", ram.percent),
        (c3, "Disco", f"{disk.percent:.1f}%", disk.percent),
        (c4, "Agente", "ONLINE" if is_online else "OFFLINE", 100 if is_online else 0),
    ]
    for col, label, value, pct in metrics:
        with col:
            fill_color = color_for(pct) if label != "Agente" else ("#22c55e" if is_online else "#ef4444")
            st.markdown(f"""
            <div class='metric-card'>
                <div class='nano-label'>{label}</div>
                <div class='metric-value' style='color:{fill_color}'>{value}</div>
                <div class='metric-bar'>
                    <div class='metric-fill' style='width:{pct}%;background:{fill_color}'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")

    # Detalhes
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("<div class='nano-label'>memória detalhada</div>", unsafe_allow_html=True)
        ram_used_gb  = ram.used  / 1e9
        ram_total_gb = ram.total / 1e9
        st.markdown(f"""
        <div class='metric-card' style='text-align:left'>
            <div style='display:flex;justify-content:space-between;margin-bottom:6px'>
                <span style='color:#4a5568;font-size:0.7rem'>Usado</span>
                <span style='color:#e2e8f0;font-size:0.8rem'>{ram_used_gb:.2f} GB</span>
            </div>
            <div style='display:flex;justify-content:space-between;margin-bottom:6px'>
                <span style='color:#4a5568;font-size:0.7rem'>Disponível</span>
                <span style='color:#e2e8f0;font-size:0.8rem'>{ram.available/1e9:.2f} GB</span>
            </div>
            <div style='display:flex;justify-content:space-between'>
                <span style='color:#4a5568;font-size:0.7rem'>Total</span>
                <span style='color:#e2e8f0;font-size:0.8rem'>{ram_total_gb:.2f} GB</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("<div class='nano-label'>rede i/o</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='metric-card' style='text-align:left'>
            <div style='display:flex;justify-content:space-between;margin-bottom:6px'>
                <span style='color:#4a5568;font-size:0.7rem'>Enviado</span>
                <span style='color:#e2e8f0;font-size:0.8rem'>{net.bytes_sent/1e6:.1f} MB</span>
            </div>
            <div style='display:flex;justify-content:space-between;margin-bottom:6px'>
                <span style='color:#4a5568;font-size:0.7rem'>Recebido</span>
                <span style='color:#e2e8f0;font-size:0.8rem'>{net.bytes_recv/1e6:.1f} MB</span>
            </div>
            <div style='display:flex;justify-content:space-between'>
                <span style='color:#4a5568;font-size:0.7rem'>Pacotes out</span>
                <span style='color:#e2e8f0;font-size:0.8rem'>{net.packets_sent:,}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Container info
    if container:
        st.markdown("")
        st.markdown("<div class='nano-label'>container nanobot</div>", unsafe_allow_html=True)
        try:
            stats = container.stats(stream=False)
            cpu_delta  = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            sys_delta  = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
            num_cpus   = stats["cpu_stats"].get("online_cpus", 1)
            c_cpu      = (cpu_delta / sys_delta) * num_cpus * 100 if sys_delta > 0 else 0
            c_mem      = stats["memory_stats"].get("usage", 0) / 1e6
            st.markdown(f"""
            <div class='metric-card' style='text-align:left'>
                <div style='display:flex;justify-content:space-between;margin-bottom:6px'>
                    <span style='color:#4a5568;font-size:0.7rem'>Container CPU</span>
                    <span style='color:#38bdf8;font-size:0.8rem'>{c_cpu:.2f}%</span>
                </div>
                <div style='display:flex;justify-content:space-between'>
                    <span style='color:#4a5568;font-size:0.7rem'>Container RAM</span>
                    <span style='color:#38bdf8;font-size:0.8rem'>{c_mem:.1f} MB</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.caption("Stats do container indisponíveis.")

    if auto_refresh:
        time.sleep(10)
        st.rerun()
