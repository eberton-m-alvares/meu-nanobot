import streamlit as st
import streamlit.components.v1 as components
import docker
import os
import json
import psutil
import time
import base64
import subprocess
from datetime import datetime

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="NANOBOT",
    page_icon="🐈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Remove ALL streamlit chrome
st.markdown("""
<style>
#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stSidebar"], .stDeployButton { display: none !important; }
.stApp { background: #07090f; margin: 0; padding: 0; }
.block-container { padding: 0 !important; max-width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
HISTORY_PATH = "workspace/chat_history.json"
WORKSPACE    = "workspace"

def save_history(msgs):
    os.makedirs(WORKSPACE, exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)

def load_history():
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return []

def get_docker_client():
    try: return docker.from_env()
    except: return None

def get_container(client):
    if not client: return None
    try:
        c = client.containers.get("nanobot")
        return c if c.status == "running" else None
    except: return None

def run_agent(container, prompt: str) -> str:
    if not container:
        return "⚠ Container offline. Inicie com `docker compose up -d`"
    try:
        safe = prompt.replace("'", "'\\''")
        result = container.exec_run(f"nanobot agent -m '{safe}'", demux=False)
        return result.output.decode("utf-8", errors="replace").strip()
    except Exception as e:
        return f"Erro: {e}"

def get_logs(container, lines=80) -> str:
    if not container: return "[container offline]"
    try:
        raw = container.logs(tail=lines).decode("utf-8", errors="replace")
        # Escape HTML
        return raw.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    except: return "[erro ao ler logs]"

def get_whatsapp_qr(container) -> str:
    """Tenta capturar QR code do log do container como base64 ou texto"""
    if not container: return None
    try:
        logs = container.logs(tail=200).decode("utf-8", errors="replace")
        # Procura por QR code no log (Evolution API imprime como texto)
        lines = logs.split('\n')
        qr_lines = []
        in_qr = False
        for line in lines:
            if '█' in line or '▄' in line or '▀' in line or '■' in line:
                in_qr = True
            if in_qr:
                qr_lines.append(line)
                if len(qr_lines) > 35:
                    break
        if qr_lines:
            return '\n'.join(qr_lines)
    except: pass
    return None

def get_sys_metrics():
    cpu  = psutil.cpu_percent(interval=0.3)
    ram  = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net  = psutil.net_io_counters()
    return {
        "cpu": round(cpu, 1),
        "ram": round(ram.percent, 1),
        "ram_used": round(ram.used / 1e9, 2),
        "ram_total": round(ram.total / 1e9, 2),
        "disk": round(disk.percent, 1),
        "disk_used": round(disk.used / 1e9, 1),
        "disk_total": round(disk.total / 1e9, 1),
        "net_sent": round(net.bytes_sent / 1e6, 1),
        "net_recv": round(net.bytes_recv / 1e6, 1),
    }

def get_identity_files():
    files = {}
    for fname in ["IDENTITY.md", "SOUL.md", "USER.md", "AGENTS.md"]:
        path = f"{WORKSPACE}/{fname}"
        try:
            with open(path, "r") as f: files[fname] = f.read()
        except: files[fname] = f"# {fname.replace('.md','')}\n\n"
    return files

def save_identity_file(fname, content):
    os.makedirs(WORKSPACE, exist_ok=True)
    with open(f"{WORKSPACE}/{fname}", "w") as f: f.write(content)

def get_config():
    path = os.path.expanduser("~/.nanobot/config.json")
    try:
        with open(path, "r") as f: return f.read()
    except:
        return json.dumps({
            "providers": {"openrouter": {"apiKey": ""}},
            "agents": {"defaults": {"model": "anthropic/claude-opus-4-5"}},
            "channels": {
                "telegram": {"enabled": False, "token": "", "allowFrom": []},
                "whatsapp": {"enabled": False}
            },
            "meta": {"token": "", "account_id": ""}
        }, indent=2)

# ─────────────────────────────────────────
# LOGIN CHECK
# ─────────────────────────────────────────
if not st.session_state.get("authenticated"):
    # Full page login via HTML
    login_html = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Unbounded:wght@300;700;900&display=swap');
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    background: #07090f;
    font-family: 'Space Mono', monospace;
    display: flex; align-items: center; justify-content: center;
    min-height: 100vh; overflow: hidden;
  }
  .bg {
    position: fixed; inset: 0; z-index: 0;
    background: radial-gradient(ellipse at 30% 20%, #0a1628 0%, transparent 60%),
                radial-gradient(ellipse at 70% 80%, #0d1f12 0%, transparent 60%);
  }
  .grid {
    position: fixed; inset: 0; z-index: 0;
    background-image: linear-gradient(#ffffff04 1px, transparent 1px),
                      linear-gradient(90deg, #ffffff04 1px, transparent 1px);
    background-size: 40px 40px;
  }
  .wrap { position: relative; z-index: 1; width: 360px; padding: 20px; }
  .logo {
    font-family: 'Unbounded', sans-serif;
    font-size: 2.8rem; font-weight: 900;
    color: #fff; letter-spacing: -0.04em;
    margin-bottom: 4px;
  }
  .logo span { color: #00ff87; }
  .sub {
    font-size: 0.6rem; color: #2a4a3a;
    letter-spacing: 0.25em; text-transform: uppercase;
    margin-bottom: 48px;
  }
  label { display: block; font-size: 0.6rem; color: #2a3a4a; letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 6px; }
  input {
    width: 100%; background: #0c1018; border: 1px solid #1a2d1e;
    color: #e2e8f0; font-family: 'Space Mono', monospace; font-size: 0.85rem;
    padding: 12px 14px; border-radius: 3px; outline: none;
    transition: border-color 0.2s; margin-bottom: 16px;
  }
  input:focus { border-color: #00ff87; }
  button {
    width: 100%; background: #00ff87; border: none; color: #07090f;
    font-family: 'Unbounded', sans-serif; font-size: 0.7rem; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    padding: 14px; border-radius: 3px; cursor: pointer;
    transition: all 0.2s; margin-top: 8px;
  }
  button:hover { background: #00e07a; transform: translateY(-1px); }
  .err { color: #ff4757; font-size: 0.7rem; margin-top: 12px; display: none; }
  .corner {
    position: fixed; font-size: 0.55rem; color: #1a2a1a;
    letter-spacing: 0.1em; text-transform: uppercase;
  }
  .corner.tl { top: 20px; left: 24px; }
  .corner.br { bottom: 20px; right: 24px; }
</style>
</head>
<body>
<div class="bg"></div>
<div class="grid"></div>
<div class="corner tl">NANOBOT CORE v2.0</div>
<div class="corner br">SECURE ACCESS ONLY</div>
<div class="wrap">
  <div class="logo">NANO<span>BOT</span></div>
  <div class="sub">Core Command Interface</div>
  <form id="f" onsubmit="auth(event)">
    <label>Username</label>
    <input id="u" type="text" autocomplete="off" placeholder="admin">
    <label>Security Token</label>
    <input id="p" type="password" placeholder="••••••••">
    <button type="submit">AUTHENTICATE →</button>
    <div class="err" id="err">Access denied.</div>
  </form>
</div>
<script>
function auth(e) {
  e.preventDefault();
  const u = document.getElementById('u').value;
  const p = document.getElementById('p').value;
  // Send to Streamlit via query param trick
  window.parent.postMessage({type:'streamlit:setComponentValue', value: JSON.stringify({u,p})}, '*');
}
</script>
</body>
</html>
    """
    # Fallback: use streamlit native login (mais confiável)
    st.markdown("""
    <style>
    .stApp { background: #07090f !important; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align:center;font-family:"Space Mono",monospace;margin-bottom:32px'>
            <div style='font-size:3rem;font-weight:900;color:#fff;letter-spacing:-0.04em'>
                NANO<span style='color:#00ff87'>BOT</span>
            </div>
            <div style='font-size:0.6rem;color:#2a4a3a;letter-spacing:0.25em;text-transform:uppercase;margin-top:4px'>
                Core Command Interface
            </div>
        </div>
        """, unsafe_allow_html=True)

        u = st.text_input("", placeholder="username", label_visibility="collapsed")
        p = st.text_input("", placeholder="security token", type="password", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("AUTHENTICATE →", use_container_width=True):
            eu = os.getenv("DASHBOARD_USER", "admin").strip()
            ep = os.getenv("DASHBOARD_PASS", "admin123").strip()
            if u.strip() == eu and p.strip() == ep:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Access denied.")
    st.stop()

# ─────────────────────────────────────────
# INIT STATE
# ─────────────────────────────────────────
if "messages"     not in st.session_state: st.session_state.messages     = load_history()
if "active_tab"   not in st.session_state: st.session_state.active_tab   = "terminal"
if "live_logs"    not in st.session_state: st.session_state.live_logs    = False
if "editing_file" not in st.session_state: st.session_state.editing_file = "IDENTITY.md"

# ─────────────────────────────────────────
# DOCKER
# ─────────────────────────────────────────
docker_client = get_docker_client()
container     = get_container(docker_client)
is_online     = container is not None
metrics       = get_sys_metrics()

# ─────────────────────────────────────────
# MAIN LAYOUT — Full custom HTML shell
# ─────────────────────────────────────────
tab = st.session_state.active_tab

# ── TOP NAV ──────────────────────────────
dot_color = "#00ff87" if is_online else "#ff4757"
status_label = "ONLINE" if is_online else "OFFLINE"

nav_html = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Unbounded:wght@300;700;900&display=swap');
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
  --bg:      #07090f;
  --surface: #0c1018;
  --border:  #141c28;
  --accent:  #00ff87;
  --text:    #c8d8e8;
  --muted:   #3a4a5a;
  --danger:  #ff4757;
  --warn:    #ffa502;
  --mono:    'Space Mono', monospace;
  --display: 'Unbounded', sans-serif;
}}
body {{ background: var(--bg); color: var(--text); font-family: var(--mono); }}

.topbar {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; height: 52px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 100;
}}
.topbar-logo {{
  font-family: var(--display); font-size: 1rem; font-weight: 900;
  color: #fff; letter-spacing: -0.03em;
}}
.topbar-logo span {{ color: var(--accent); }}
.topbar-nav {{ display: flex; gap: 4px; }}
.nav-btn {{
  font-family: var(--mono); font-size: 0.6rem; font-weight: 700;
  letter-spacing: 0.12em; text-transform: uppercase;
  padding: 6px 14px; border-radius: 2px; border: 1px solid transparent;
  cursor: pointer; transition: all 0.15s; background: transparent; color: var(--muted);
}}
.nav-btn:hover {{ color: var(--text); border-color: var(--border); }}
.nav-btn.active {{ color: var(--accent); border-color: var(--accent); background: #00ff8710; }}
.topbar-status {{ display: flex; align-items: center; gap: 8px; font-size: 0.6rem; color: var(--muted); letter-spacing: 0.1em; }}
.dot {{ width: 7px; height: 7px; border-radius: 50%; background: {dot_color}; box-shadow: 0 0 8px {dot_color}; animation: pulse 2s infinite; }}
@keyframes pulse {{ 0%,100% {{ opacity:1 }} 50% {{ opacity:0.4 }} }}
.logout-btn {{
  font-family: var(--mono); font-size: 0.55rem; letter-spacing: 0.1em;
  text-transform: uppercase; padding: 5px 10px; border: 1px solid var(--border);
  background: transparent; color: var(--muted); border-radius: 2px; cursor: pointer;
  transition: all 0.15s; margin-left: 12px;
}}
.logout-btn:hover {{ border-color: var(--danger); color: var(--danger); }}
</style>

<div class="topbar">
  <div class="topbar-logo">NANO<span>BOT</span></div>
  <div class="topbar-nav">
    <button class="nav-btn {'active' if tab=='terminal' else ''}"
      onclick="setTab('terminal')">⚡ Terminal</button>
    <button class="nav-btn {'active' if tab=='whatsapp' else ''}"
      onclick="setTab('whatsapp')">📱 WhatsApp</button>
    <button class="nav-btn {'active' if tab=='skills' else ''}"
      onclick="setTab('skills')">🧩 Skills</button>
    <button class="nav-btn {'active' if tab=='identity' else ''}"
      onclick="setTab('identity')">🧠 Identidade</button>
    <button class="nav-btn {'active' if tab=='telemetry' else ''}"
      onclick="setTab('telemetry')">📊 Telemetria</button>
  </div>
  <div class="topbar-status">
    <div class="dot"></div>{status_label}
    <span style="color:#1a2a3a">|</span>
    CPU {metrics['cpu']}%
    <span style="color:#1a2a3a">|</span>
    RAM {metrics['ram']}%
  </div>
</div>

<script>
function setTab(t) {{
  const form = document.createElement('form');
  form.method = 'GET';
  const input = document.createElement('input');
  input.name = 'tab'; input.value = t;
  form.appendChild(input); document.body.appendChild(form);
  // Use Streamlit's JS bridge instead
  window.parent.postMessage({{isStreamlitMessage: true, type: 'streamlit:setComponentValue', value: t}}, '*');
}}
</script>
"""

# Nav tab switcher via query params
params = st.query_params
if "tab" in params:
    st.session_state.active_tab = params["tab"]
    tab = params["tab"]

# Render nav as HTML
st.markdown(nav_html, unsafe_allow_html=True)

# Tab buttons via Streamlit (reliable switching)
col_t, col_w, col_s, col_i, col_m, col_spacer, col_logout = st.columns([1,1,1,1,1,4,1])
with col_t:
    if st.button("⚡ Terminal", use_container_width=True, key="nav_terminal"):
        st.session_state.active_tab = "terminal"; st.rerun()
with col_w:
    if st.button("📱 WhatsApp", use_container_width=True, key="nav_whatsapp"):
        st.session_state.active_tab = "whatsapp"; st.rerun()
with col_s:
    if st.button("🧩 Skills", use_container_width=True, key="nav_skills"):
        st.session_state.active_tab = "skills"; st.rerun()
with col_i:
    if st.button("🧠 Identidade", use_container_width=True, key="nav_identity"):
        st.session_state.active_tab = "identity"; st.rerun()
with col_m:
    if st.button("📊 Telemetria", use_container_width=True, key="nav_telemetry"):
        st.session_state.active_tab = "telemetry"; st.rerun()
with col_logout:
    if st.button("🔒", use_container_width=True, key="nav_logout"):
        st.session_state["authenticated"] = False; st.rerun()

# Active tab indicator
st.markdown(f"""
<style>
/* Style active nav button */
div[data-testid="stHorizontalBlock"] .stButton button {{
  background: transparent !important;
  border: 1px solid #141c28 !important;
  color: #3a4a5a !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 0.6rem !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
  padding: 6px !important;
  border-radius: 2px !important;
  transition: all 0.15s !important;
}}
div[data-testid="stHorizontalBlock"] .stButton button:hover {{
  border-color: #00ff87 !important;
  color: #00ff87 !important;
}}
</style>
""", unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

tab = st.session_state.active_tab

# ─────────────────────────────────────────
# SHARED CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Unbounded:wght@300;700;900&display=swap');
.stApp { background: #07090f; }
.block-container { padding: 0 24px 24px !important; max-width: 100% !important; }

/* Section headers */
.sec-title {
  font-family: 'Unbounded', sans-serif; font-size: 0.7rem; font-weight: 700;
  color: #fff; letter-spacing: 0.15em; text-transform: uppercase;
  margin-bottom: 4px;
}
.sec-sub {
  font-size: 0.6rem; color: #2a3a4a; letter-spacing: 0.1em;
  text-transform: uppercase; margin-bottom: 16px;
}

/* Cards */
.card {
  background: #0c1018; border: 1px solid #141c28; border-radius: 4px;
  padding: 16px;
}

/* Log box */
.logbox {
  background: #050709; border: 1px solid #141c28;
  border-left: 2px solid #00ff87; border-radius: 3px;
  padding: 14px; font-family: 'Space Mono', monospace;
  font-size: 0.68rem; color: #4ade80; line-height: 1.7;
  height: 420px; overflow-y: auto; white-space: pre-wrap;
}

/* Metric */
.mcard {
  background: #0c1018; border: 1px solid #141c28; border-radius: 4px;
  padding: 18px 16px; text-align: center;
}
.mval {
  font-family: 'Unbounded', sans-serif; font-size: 1.8rem; font-weight: 900;
  line-height: 1; margin: 6px 0;
}
.mlabel { font-size: 0.55rem; color: #2a3a4a; letter-spacing: 0.2em; text-transform: uppercase; }
.mbar { height: 2px; background: #141c28; border-radius: 1px; margin-top: 10px; overflow: hidden; }
.mfill { height: 100%; border-radius: 1px; transition: width 0.6s ease; }

/* Chat */
[data-testid="stChatMessage"] {
  background: transparent !important;
  border-bottom: 1px solid #0d1520 !important;
  padding: 10px 0 !important;
}
[data-testid="stChatMessageContent"] p {
  font-family: 'Space Mono', monospace !important;
  font-size: 0.8rem !important; line-height: 1.7 !important;
  color: #c8d8e8 !important;
}
.stChatInput textarea {
  background: #0c1018 !important; border: 1px solid #141c28 !important;
  color: #e2e8f0 !important; font-family: 'Space Mono', monospace !important;
  font-size: 0.8rem !important; border-radius: 3px !important;
}
.stChatInput textarea:focus { border-color: #00ff87 !important; }

/* Text areas and inputs */
.stTextArea textarea, .stTextInput input, .stSelectbox select {
  background: #0c1018 !important; border: 1px solid #141c28 !important;
  color: #e2e8f0 !important; font-family: 'Space Mono', monospace !important;
  font-size: 0.78rem !important; border-radius: 3px !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
  border-color: #00ff87 !important;
}

/* Buttons */
.stButton > button {
  background: transparent !important; border: 1px solid #141c28 !important;
  color: #3a4a5a !important; font-family: 'Space Mono', monospace !important;
  font-size: 0.65rem !important; letter-spacing: 0.08em !important;
  text-transform: uppercase !important; border-radius: 3px !important;
  transition: all 0.15s !important;
}
.stButton > button:hover {
  border-color: #00ff87 !important; color: #00ff87 !important;
}

/* QR code box */
.qrbox {
  background: #050709; border: 1px solid #141c28;
  border-left: 2px solid #00ff87; border-radius: 3px;
  padding: 14px; font-family: 'Space Mono', monospace;
  font-size: 0.55rem; color: #00ff87; line-height: 1.2;
  white-space: pre; overflow: auto; min-height: 200px;
}

/* Tabs */
[data-testid="stTabs"] button {
  font-family: 'Space Mono', monospace !important;
  font-size: 0.65rem !important; letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
}

/* Toggle */
.stToggle label { font-size: 0.65rem !important; color: #3a4a5a !important; font-family: 'Space Mono', monospace !important; }

/* Divider */
hr { border-color: #141c28 !important; }

/* Success/error */
.stSuccess, .stError, .stInfo { font-family: 'Space Mono', monospace !important; font-size: 0.75rem !important; }

/* Selectbox */
[data-testid="stSelectbox"] label { font-size: 0.6rem !important; color: #2a3a4a !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# ── TAB: TERMINAL
# ─────────────────────────────────────────
if tab == "terminal":
    col_chat, col_logs = st.columns([0.55, 0.45], gap="large")

    with col_chat:
        st.markdown("<div class='sec-title'>Terminal Tático</div>", unsafe_allow_html=True)
        st.markdown("<div class='sec-sub'>conversa direta com o agente</div>", unsafe_allow_html=True)

        # Chat container
        chat_area = st.container(height=440, border=False)
        with chat_area:
            for msg in st.session_state.messages:
                icon = "🐈" if msg["role"] == "assistant" else "👤"
                with st.chat_message(msg["role"], avatar=icon):
                    st.markdown(msg["content"])

        # Input
        if prompt := st.chat_input("insira o comando..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_area:
                with st.chat_message("user", avatar="👤"):
                    st.markdown(prompt)
                with st.chat_message("assistant", avatar="🐈"):
                    with st.spinner(""):
                        response = run_agent(container, prompt)
                    st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            save_history(st.session_state.messages)
            st.rerun()

        # Controls below chat
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("🗑 Limpar", use_container_width=True):
                st.session_state.messages = []
                save_history([])
                st.rerun()
        with c2:
            msg_count = len(st.session_state.messages)
            st.markdown(f"<div style='font-size:0.6rem;color:#2a3a4a;padding-top:8px;letter-spacing:0.1em'>{msg_count} MSGS</div>", unsafe_allow_html=True)

    with col_logs:
        st.markdown("<div class='sec-title'>Thought Stream</div>", unsafe_allow_html=True)

        lc1, lc2 = st.columns([1, 1])
        with lc1:
            live = st.toggle("Live (5s)", value=st.session_state.live_logs)
            st.session_state.live_logs = live
        with lc2:
            log_lines = st.selectbox("", [30, 60, 100, 200], index=1, label_visibility="collapsed")

        log_text = get_logs(container, log_lines)
        st.markdown(f'<div class="logbox">{log_text}</div>', unsafe_allow_html=True)

        if live and is_online:
            time.sleep(5)
            st.rerun()


# ─────────────────────────────────────────
# ── TAB: WHATSAPP
# ─────────────────────────────────────────
elif tab == "whatsapp":
    st.markdown("<div class='sec-title'>WhatsApp</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>conexão e status do canal</div>", unsafe_allow_html=True)

    col_status, col_qr = st.columns([0.4, 0.6], gap="large")

    with col_status:
        st.markdown("<div class='card'>", unsafe_allow_html=True)

        # Status do container WA
        wa_container = None
        if docker_client:
            try:
                wa_container = docker_client.containers.get("evolution_api")
            except:
                try:
                    wa_container = docker_client.containers.get("whatsapp")
                except: pass

        wa_online = wa_container and wa_container.status == "running"
        wa_dot = "#00ff87" if wa_online else "#ff4757"
        wa_status = "CONECTADO" if wa_online else "OFFLINE"

        st.markdown(f"""
        <div style='margin-bottom:20px'>
            <div style='font-size:0.55rem;color:#2a3a4a;letter-spacing:0.2em;text-transform:uppercase;margin-bottom:8px'>Status do Serviço</div>
            <div style='display:flex;align-items:center;gap:8px'>
                <div style='width:8px;height:8px;border-radius:50%;background:{wa_dot};box-shadow:0 0 8px {wa_dot}'></div>
                <span style='font-family:"Unbounded",sans-serif;font-size:0.85rem;font-weight:700;color:#fff'>{wa_status}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Config
        st.markdown("<div style='font-size:0.55rem;color:#2a3a4a;letter-spacing:0.2em;text-transform:uppercase;margin-bottom:8px'>Configuração</div>", unsafe_allow_html=True)

        config_str = get_config()
        try:
            config_data = json.loads(config_str)
            wa_config = config_data.get("channels", {}).get("whatsapp", {})
            wa_enabled = wa_config.get("enabled", False)
            allow_from = wa_config.get("allowFrom", [])
        except:
            wa_enabled = False
            allow_from = []

        new_enabled = st.toggle("WhatsApp Habilitado", value=wa_enabled)
        new_allow = st.text_input(
            "Números autorizados",
            value=", ".join(allow_from),
            placeholder="+5511999999999, +5511888888888",
            help="Separados por vírgula"
        )

        if st.button("💾 Salvar Config WhatsApp", use_container_width=True):
            try:
                cfg = json.loads(config_str)
                cfg.setdefault("channels", {}).setdefault("whatsapp", {})
                cfg["channels"]["whatsapp"]["enabled"] = new_enabled
                cfg["channels"]["whatsapp"]["allowFrom"] = [n.strip() for n in new_allow.split(",") if n.strip()]
                path = os.path.expanduser("~/.nanobot/config.json")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f: json.dump(cfg, f, indent=2)
                st.success("Salvo!")
            except Exception as e:
                st.error(f"Erro: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Comandos rápidos
        st.markdown("<div style='font-size:0.55rem;color:#2a3a4a;letter-spacing:0.2em;text-transform:uppercase;margin-bottom:8px'>Comandos Docker</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("▶ Start", use_container_width=True):
                try:
                    subprocess.run(["docker", "compose", "up", "-d", "whatsapp"], check=True)
                    st.success("Iniciado!")
                    time.sleep(2); st.rerun()
                except Exception as e: st.error(str(e))
        with c2:
            if st.button("⏹ Stop", use_container_width=True):
                try:
                    if wa_container: wa_container.stop()
                    st.success("Parado!")
                    time.sleep(1); st.rerun()
                except Exception as e: st.error(str(e))

        if st.button("🔄 Reiniciar", use_container_width=True):
            try:
                if wa_container: wa_container.restart()
                st.success("Reiniciado!")
                time.sleep(2); st.rerun()
            except Exception as e: st.error(str(e))

    with col_qr:
        st.markdown("<div class='sec-title' style='font-size:0.65rem'>QR Code</div>", unsafe_allow_html=True)
        st.markdown("<div class='sec-sub'>escaneie com o WhatsApp</div>", unsafe_allow_html=True)

        refresh_qr = st.button("🔄 Atualizar QR", use_container_width=False)

        # Tenta pegar QR do container WA
        qr_text = None
        if wa_container:
            qr_text = get_whatsapp_qr(wa_container)

        # Também tenta do container nanobot
        if not qr_text and container:
            qr_text = get_whatsapp_qr(container)

        if qr_text:
            st.markdown(f'<div class="qrbox">{qr_text}</div>', unsafe_allow_html=True)
            st.caption("QR capturado dos logs do container. Se não aparecer corretamente, use o terminal direto.")
        else:
            # Mostra instrução para copiar QR do terminal
            st.markdown("""
            <div class='qrbox' style='color:#2a4a3a;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:12px'>
<span style='font-size:2rem'>📱</span>
<span>QR Code não detectado nos logs.</span>
<span style='color:#1a3a2a'>Para conectar manualmente:</span>
<span style='color:#00ff87'>nanobot channels login</span>
<span style='color:#1a3a2a'>no terminal da VPS</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Log do container WA
        if wa_container:
            with st.expander("📋 Logs do container WhatsApp"):
                try:
                    wa_logs = wa_container.logs(tail=40).decode("utf-8", errors="replace")
                    wa_logs_safe = wa_logs.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                    st.markdown(f'<div class="logbox" style="height:250px">{wa_logs_safe}</div>', unsafe_allow_html=True)
                except:
                    st.error("Não foi possível ler logs do container WhatsApp.")

        if refresh_qr:
            st.rerun()


# ─────────────────────────────────────────
# ── TAB: SKILLS & TOOLS
# ─────────────────────────────────────────
elif tab == "skills":
    st.markdown("<div class='sec-title'>Skills & Tools</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>arquitetura do agente</div>", unsafe_allow_html=True)

    tab_sk, tab_tl, tab_cfg = st.tabs(["📋 Skills (.md)", "🔧 Tools (.py)", "⚙️ Config"])

    # ── Skills
    with tab_sk:
        skill_dirs = ["skills", "nanobot/skills", "."]
        skills = []
        for d in skill_dirs:
            if os.path.isdir(d):
                for f in os.listdir(d):
                    if f.endswith(".md") and f not in ["README.md","COMMUNICATION.md"]:
                        skills.append({"name": f.replace(".md","").replace("_"," ").upper(), "file": os.path.join(d,f)})

        if not skills:
            st.markdown("""
            <div class='card' style='text-align:center;color:#2a3a4a;padding:32px'>
                <div style='font-size:1.5rem;margin-bottom:8px'>🧩</div>
                <div style='font-size:0.7rem;letter-spacing:0.1em'>Nenhuma skill encontrada</div>
                <div style='font-size:0.6rem;margin-top:4px'>Crie uma abaixo ou verifique a pasta skills/</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='font-size:0.6rem;color:#2a3a4a;letter-spacing:0.1em;margin-bottom:12px'>{len(skills)} SKILL(S) CARREGADA(S)</div>", unsafe_allow_html=True)
            for s in skills:
                with st.expander(f"📄 {s['name']}"):
                    try:
                        with open(s["file"]) as f: content = f.read()
                        edited = st.text_area("", value=content, height=200, key=f"skill_{s['file']}", label_visibility="collapsed")
                        c1, c2 = st.columns([1,4])
                        with c1:
                            if st.button("💾 Salvar", key=f"save_skill_{s['file']}"):
                                with open(s["file"], "w") as f: f.write(edited)
                                st.success("Salvo!")
                        st.caption(f"`{s['file']}`")
                    except: st.warning("Não foi possível ler.")

        st.markdown("---")
        st.markdown("<div style='font-size:0.6rem;color:#2a3a4a;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:8px'>Nova Skill</div>", unsafe_allow_html=True)
        nc1, nc2 = st.columns([1, 2])
        with nc1:
            new_skill_name = st.text_input("", placeholder="ex: meta_ads", label_visibility="collapsed", key="new_skill_name")
        with nc2:
            new_skill_desc = st.text_input("", placeholder="descrição breve", label_visibility="collapsed", key="new_skill_desc")
        new_skill_content = st.text_area(
            "", height=160, label_visibility="collapsed", key="new_skill_content",
            placeholder="# Meta Ads Skill\n\nQuando o usuário perguntar sobre campanhas, use a tool meta_api para..."
        )
        if st.button("💾 Criar Skill", key="create_skill"):
            if new_skill_name and new_skill_content:
                os.makedirs("skills", exist_ok=True)
                path = f"skills/{new_skill_name.lower().replace(' ','_')}.md"
                with open(path, "w") as f: f.write(new_skill_content)
                st.success(f"Criada em `{path}`")
                st.rerun()

    # ── Tools
    with tab_tl:
        tool_dirs = ["nanobot/agent/tools", "agent/tools"]
        tools = []
        for d in tool_dirs:
            if os.path.isdir(d):
                for f in os.listdir(d):
                    if f.endswith(".py") and not f.startswith("_"):
                        tools.append({"name": f.replace(".py","").upper(), "file": os.path.join(d,f)})

        if not tools:
            st.markdown("""
            <div class='card' style='text-align:center;color:#2a3a4a;padding:32px'>
                <div style='font-size:1.5rem;margin-bottom:8px'>🔧</div>
                <div style='font-size:0.7rem;letter-spacing:0.1em'>Nenhuma tool encontrada</div>
                <div style='font-size:0.6rem;margin-top:4px'>Verifique nanobot/agent/tools/</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='font-size:0.6rem;color:#2a3a4a;letter-spacing:0.1em;margin-bottom:12px'>{len(tools)} TOOL(S) DISPONÍVEL(IS)</div>", unsafe_allow_html=True)
            for t in tools:
                with st.expander(f"🔧 {t['name']}"):
                    try:
                        with open(t["file"]) as f: code = f.read()
                        edited_code = st.text_area("", value=code, height=250, key=f"tool_{t['file']}", label_visibility="collapsed")
                        c1, c2 = st.columns([1,4])
                        with c1:
                            if st.button("💾 Salvar", key=f"save_tool_{t['file']}"):
                                with open(t["file"], "w") as f: f.write(edited_code)
                                st.success("Salvo!")
                        st.caption(f"`{t['file']}`")
                    except: st.warning("Não foi possível ler.")

        st.markdown("---")
        st.markdown("<div style='font-size:0.6rem;color:#2a3a4a;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:8px'>Nova Tool</div>", unsafe_allow_html=True)
        new_tool_name = st.text_input("", placeholder="ex: meta_api", label_visibility="collapsed", key="new_tool_name")
        new_tool_content = st.text_area(
            "", height=200, label_visibility="collapsed", key="new_tool_content",
            placeholder='def meta_api(endpoint: str, params: dict) -> dict:\n    """Chama a API do Meta Ads com token configurado"""\n    import requests\n    # ...'
        )
        if st.button("💾 Criar Tool", key="create_tool"):
            if new_tool_name and new_tool_content:
                os.makedirs("nanobot/agent/tools", exist_ok=True)
                path = f"nanobot/agent/tools/{new_tool_name.lower().replace(' ','_')}.py"
                with open(path, "w") as f: f.write(new_tool_content)
                st.success(f"Criada em `{path}`")
                st.rerun()

    # ── Config
    with tab_cfg:
        st.markdown("<div style='font-size:0.6rem;color:#2a3a4a;letter-spacing:0.1em;margin-bottom:8px'>~/.nanobot/config.json</div>", unsafe_allow_html=True)
        config_content = get_config()
        edited_cfg = st.text_area("", value=config_content, height=420, label_visibility="collapsed")
        c1, c2 = st.columns([1, 4])
        with c1:
            if st.button("💾 Salvar", key="save_config"):
                try:
                    json.loads(edited_cfg)
                    path = os.path.expanduser("~/.nanobot/config.json")
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w") as f: f.write(edited_cfg)
                    st.success("Salvo!")
                except json.JSONDecodeError as e:
                    st.error(f"JSON inválido: {e}")


# ─────────────────────────────────────────
# ── TAB: IDENTIDADE
# ─────────────────────────────────────────
elif tab == "identity":
    st.markdown("<div class='sec-title'>Alma & Identidade</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>define a personalidade e comportamento do agente</div>", unsafe_allow_html=True)

    IDENTITY_META = {
        "IDENTITY.md": ("Personalidade", "Tom de voz, nome, como o agente se apresenta"),
        "SOUL.md":     ("Alma & Valores", "Princípios, ética, o que o agente defende"),
        "USER.md":     ("Contexto do Usuário", "Suas preferências, histórico, como o agente te trata"),
        "AGENTS.md":   ("Sub-agentes", "Configuração de agentes especializados"),
    }

    identity_files = get_identity_files()
    tabs_id = st.tabs([f"{v[0]}" for v in IDENTITY_META.values()])

    for (fname, (title, desc)), tab_id in zip(IDENTITY_META.items(), tabs_id):
        with tab_id:
            st.caption(desc)
            content = identity_files.get(fname, f"# {title}\n\n")
            new_content = st.text_area("", value=content, height=440, key=f"id_{fname}", label_visibility="collapsed")
            c1, c2, c3 = st.columns([1, 1, 4])
            with c1:
                if st.button("💾 Salvar", key=f"save_id_{fname}", use_container_width=True):
                    save_identity_file(fname, new_content)
                    st.success(f"{fname} salvo!")
            with c2:
                if st.button("↩ Reverter", key=f"rev_id_{fname}", use_container_width=True):
                    st.rerun()


# ─────────────────────────────────────────
# ── TAB: TELEMETRIA
# ─────────────────────────────────────────
elif tab == "telemetry":
    st.markdown("<div class='sec-title'>Telemetria</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>status do sistema em tempo real</div>", unsafe_allow_html=True)

    auto = st.toggle("Auto-refresh (10s)", value=False)

    def color_pct(p):
        if p < 60: return "#00ff87"
        if p < 85: return "#ffa502"
        return "#ff4757"

    # Main metrics
    c1, c2, c3, c4 = st.columns(4)
    agent_pct = 100 if is_online else 0
    agent_color = "#00ff87" if is_online else "#ff4757"
    agent_label = "ONLINE" if is_online else "OFFLINE"

    for col, label, value, pct, color in [
        (c1, "CPU",    f"{metrics['cpu']}%",   metrics['cpu'],  color_pct(metrics['cpu'])),
        (c2, "RAM",    f"{metrics['ram']}%",   metrics['ram'],  color_pct(metrics['ram'])),
        (c3, "DISCO",  f"{metrics['disk']}%",  metrics['disk'], color_pct(metrics['disk'])),
        (c4, "AGENTE", agent_label,            agent_pct,       agent_color),
    ]:
        with col:
            st.markdown(f"""
            <div class='mcard'>
                <div class='mlabel'>{label}</div>
                <div class='mval' style='color:{color}'>{value}</div>
                <div class='mbar'><div class='mfill' style='width:{pct}%;background:{color}'></div></div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("<div style='font-size:0.55rem;color:#2a3a4a;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:8px'>Memória</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='card'>
            <div style='display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #141c28'>
                <span style='font-size:0.65rem;color:#2a3a4a'>Usado</span>
                <span style='font-size:0.7rem;color:#00ff87'>{metrics['ram_used']} GB</span>
            </div>
            <div style='display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #141c28'>
                <span style='font-size:0.65rem;color:#2a3a4a'>Total</span>
                <span style='font-size:0.7rem;color:#c8d8e8'>{metrics['ram_total']} GB</span>
            </div>
            <div style='display:flex;justify-content:space-between;padding:6px 0'>
                <span style='font-size:0.65rem;color:#2a3a4a'>Livre</span>
                <span style='font-size:0.7rem;color:#c8d8e8'>{round(metrics['ram_total']-metrics['ram_used'],2)} GB</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("<div style='font-size:0.55rem;color:#2a3a4a;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:8px'>Disco</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='card'>
            <div style='display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #141c28'>
                <span style='font-size:0.65rem;color:#2a3a4a'>Usado</span>
                <span style='font-size:0.7rem;color:#00ff87'>{metrics['disk_used']} GB</span>
            </div>
            <div style='display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #141c28'>
                <span style='font-size:0.65rem;color:#2a3a4a'>Total</span>
                <span style='font-size:0.7rem;color:#c8d8e8'>{metrics['disk_total']} GB</span>
            </div>
            <div style='display:flex;justify-content:space-between;padding:6px 0'>
                <span style='font-size:0.65rem;color:#2a3a4a'>Livre</span>
                <span style='font-size:0.7rem;color:#c8d8e8'>{round(metrics['disk_total']-metrics['disk_used'],1)} GB</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_c:
        st.markdown("<div style='font-size:0.55rem;color:#2a3a4a;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:8px'>Rede I/O</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='card'>
            <div style='display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #141c28'>
                <span style='font-size:0.65rem;color:#2a3a4a'>Enviado</span>
                <span style='font-size:0.7rem;color:#00ff87'>{metrics['net_sent']} MB</span>
            </div>
            <div style='display:flex;justify-content:space-between;padding:6px 0'>
                <span style='font-size:0.65rem;color:#2a3a4a'>Recebido</span>
                <span style='font-size:0.7rem;color:#c8d8e8'>{metrics['net_recv']} MB</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Container stats
    if container:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.55rem;color:#2a3a4a;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:8px'>Container Nanobot</div>", unsafe_allow_html=True)
        try:
            stats = container.stats(stream=False)
            cpu_d = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            sys_d = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
            ncpu  = stats["cpu_stats"].get("online_cpus", 1)
            c_cpu = round((cpu_d / sys_d) * ncpu * 100, 2) if sys_d > 0 else 0
            c_mem = round(stats["memory_stats"].get("usage", 0) / 1e6, 1)

            cs1, cs2, cs3 = st.columns(3)
            for col, label, val, color in [
                (cs1, "Container CPU", f"{c_cpu}%", color_pct(c_cpu)),
                (cs2, "Container RAM", f"{c_mem} MB", "#38bdf8"),
                (cs3, "Status", "RUNNING", "#00ff87"),
            ]:
                with col:
                    st.markdown(f"""
                    <div class='mcard'>
                        <div class='mlabel'>{label}</div>
                        <div class='mval' style='color:{color};font-size:1.3rem'>{val}</div>
                    </div>
                    """, unsafe_allow_html=True)
        except:
            st.caption("Stats do container indisponíveis no momento.")

    st.markdown(f"<div style='font-size:0.55rem;color:#1a2a3a;margin-top:16px;text-align:right'>atualizado em {datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

    if auto:
        time.sleep(10)
        st.rerun()
