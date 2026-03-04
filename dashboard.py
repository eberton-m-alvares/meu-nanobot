"""
NANOBOT COMMAND CENTER v3.0
Foco: capacidades operacionais avançadas do agente
"""

import datetime
import json
import os
import queue
import re
import threading
import time
from dataclasses import dataclass, field

import docker
import psutil
import streamlit as st
import streamlit.components.v1 as components
from ansi2html import Ansi2HTMLConverter

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NANOBOT · Command Center",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #05070a !important;
    color: #c9d1e0 !important;
    font-family: 'Syne', sans-serif !important;
}

#MainMenu, footer, header { visibility: hidden; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0d1021; }
::-webkit-scrollbar-thumb { background: #2563eb44; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #3b82f6; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b0d1a 0%, #05070a 100%) !important;
    border-right: 1px solid #1e2640 !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

.logo-zone {
    background: linear-gradient(135deg, #0f1729 0%, #05070a 100%);
    border-bottom: 1px solid #1e2640;
    padding: 28px 24px 20px;
    margin-bottom: 8px;
    position: relative;
    overflow: hidden;
}
.logo-zone::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 120px; height: 120px;
    background: radial-gradient(circle, #3b82f644 0%, transparent 70%);
    border-radius: 50%;
}
.logo-zone .bot-name {
    font-family: 'Space Mono', monospace;
    font-size: 1.35rem; font-weight: 700;
    color: #e2e8f0; letter-spacing: 0.12em; line-height: 1;
}
.logo-zone .bot-name span { color: #3b82f6; }
.logo-zone .bot-sub {
    font-size: 0.68rem; color: #4a5568;
    letter-spacing: 0.25em; text-transform: uppercase; margin-top: 4px;
}
.status-dot {
    display: inline-block; width: 7px; height: 7px; border-radius: 50%;
    background: #22c55e; box-shadow: 0 0 8px #22c55e88;
    margin-right: 6px; animation: pulse-dot 2s ease-in-out infinite;
}
.status-dot.offline { background: #ef4444; box-shadow: 0 0 8px #ef444488; animation: none; }
@keyframes pulse-dot {
    0%, 100% { opacity: 1; box-shadow: 0 0 8px #22c55e88; }
    50%       { opacity: .6; box-shadow: 0 0 16px #22c55ecc; }
}

[data-testid="stRadio"] label {
    font-size: 0.82rem !important; letter-spacing: 0.05em !important;
    color: #94a3b8 !important; padding: 8px 12px !important;
    border-radius: 8px !important; transition: all .2s !important;
    font-family: 'Space Mono', monospace !important;
}
[data-testid="stRadio"] label:hover { color: #94a3b8 !important; background: #ffffff06 !important; }

.glass-card {
    background: linear-gradient(135deg, #0f1729cc 0%, #05070acc 100%);
    border: 1px solid #1e2640; border-radius: 14px;
    padding: 20px 22px;
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    position: relative; overflow: hidden;
}
.glass-card::before {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, #3b82f622, transparent);
}

.sec-header {
    font-family: 'Space Mono', monospace; font-size: 0.72rem;
    letter-spacing: 0.22em; text-transform: uppercase;
    color: #3b82f6; margin-bottom: 14px;
    display: flex; align-items: center; gap: 8px;
}
.sec-header::after {
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, #1e2640, transparent);
}

/* CHAT */
[data-testid="stChatMessage"] {
    background: transparent !important; border: none !important; padding: 6px 0 !important;
}
[data-testid="stChatInput"] {
    background: #0d1525 !important; border: 1px solid #1e2a40 !important;
    border-radius: 12px !important; color: #c9d1e0 !important;
    font-family: 'Space Mono', monospace !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #3b82f6 !important; box-shadow: 0 0 0 3px #3b82f618 !important;
}

/* LOG BOX */
.log-box {
    background: #020408; border: 1px solid #0f1929; border-radius: 10px;
    padding: 14px 16px; font-family: 'Space Mono', monospace;
    font-size: 0.72rem; line-height: 1.7; color: #4a7c99;
    height: 420px; overflow-y: auto; white-space: pre-wrap; word-break: break-all;
}
.log-line-info  { color: #3b82f6; }
.log-line-ok    { color: #22c55e; }
.log-line-warn  { color: #f59e0b; }
.log-line-err   { color: #ef4444; }

/* TERMINAL BOX */
.term-box {
    background: #010306; border: 1px solid #0f1929; border-radius: 10px;
    padding: 14px 16px; font-family: 'Space Mono', monospace;
    font-size: 0.75rem; line-height: 1.8; color: #22c55e;
    min-height: 200px; max-height: 400px; overflow-y: auto;
    white-space: pre-wrap; word-break: break-all;
}

/* METRIC CARD */
.metric-card {
    background: linear-gradient(135deg, #0f1729 0%, #05070a 100%);
    border: 1px solid #1e2640; border-radius: 12px;
    padding: 18px 20px; text-align: center; position: relative; overflow: hidden;
}
.metric-card .m-label {
    font-family: 'Space Mono', monospace; font-size: 0.65rem;
    letter-spacing: 0.2em; text-transform: uppercase; color: #4a5568; margin-bottom: 8px;
}
.metric-card .m-value {
    font-family: 'Space Mono', monospace; font-size: 1.9rem;
    font-weight: 700; color: #e2e8f0; line-height: 1;
}
.metric-card .m-accent { color: #3b82f6; }
.metric-card .m-sub { font-size: 0.72rem; color: #64748b; margin-top: 4px; }

.prog-wrap { margin-top: 8px; }
.prog-track { background: #0d1525; border-radius: 99px; height: 4px; overflow: hidden; }
.prog-fill { height: 100%; border-radius: 99px; transition: width .6s ease; }
.prog-fill.blue  { background: linear-gradient(90deg, #1d4ed8, #60a5fa); }
.prog-fill.green { background: linear-gradient(90deg, #15803d, #4ade80); }
.prog-fill.amber { background: linear-gradient(90deg, #b45309, #fbbf24); }
.prog-fill.red   { background: linear-gradient(90deg, #7f1d1d, #ef4444); }

/* CRON TABLE */
.cron-row {
    display: grid; grid-template-columns: 160px 1fr 80px;
    gap: 12px; align-items: center;
    padding: 10px 14px; margin-bottom: 6px;
    background: #0a0f1e; border: 1px solid #1a2035;
    border-radius: 8px; font-family: 'Space Mono', monospace; font-size: 0.72rem;
}
.cron-schedule { color: #3b82f6; }
.cron-cmd { color: #94a3b8; word-break: break-all; }
.cron-badge {
    background: #0f2d1a; color: #22c55e; border: 1px solid #1a4a2a;
    border-radius: 6px; padding: 2px 8px; font-size: 0.62rem;
    letter-spacing: 0.1em; text-transform: uppercase; text-align: center;
}

/* MEMORY FILE CARD */
.mem-card {
    background: #0a0f1e; border: 1px solid #1a2035; border-radius: 8px;
    padding: 12px 16px; margin-bottom: 8px; cursor: pointer;
    transition: border-color .2s;
}
.mem-card:hover { border-color: #3b82f644; }
.mem-card .mem-name {
    font-family: 'Space Mono', monospace; font-size: 0.78rem;
    color: #60a5fa; margin-bottom: 4px;
}
.mem-card .mem-meta { font-size: 0.66rem; color: #2a3a54; }

/* TOOL BADGE */
.tool-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #0d1525; border: 1px solid #1e2640;
    border-radius: 8px; padding: 6px 14px; margin: 4px;
    font-family: 'Space Mono', monospace; font-size: 0.72rem; color: #64748b;
    transition: all .2s; cursor: default;
}
.tool-badge.active { border-color: #1d4ed8; color: #60a5fa; background: #0d1f40; }

/* INPUTS */
textarea, input[type="text"], input[type="password"] {
    background: #05070a !important; border: 1px solid #1e2640 !important;
    border-radius: 10px !important; color: #94a3b8 !important;
    font-family: 'Space Mono', monospace !important; font-size: 0.8rem !important;
}
textarea:focus, input:focus { border-color: #3b82f6 !important; box-shadow: none !important; }

[data-testid="stSelectbox"] > div > div {
    background: #05070a !important; border: 1px solid #1e2640 !important;
    border-radius: 8px !important; color: #94a3b8 !important;
    font-family: 'Space Mono', monospace !important; font-size: 0.8rem !important;
}

/* BUTTONS */
.stButton > button {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
    color: #e2e8f0 !important; border: 1px solid #3b82f6 !important; border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important; font-size: 0.75rem !important;
    letter-spacing: 0.08em !important; padding: 10px 20px !important; transition: all .2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
    transform: translateY(-1px) !important; box-shadow: 0 0 15px rgba(59, 130, 246, 0.4) !important;
}

/* DANGER BUTTON */
.danger-btn > button {
    background: transparent !important; border: 1px solid #3f1515 !important;
    color: #7f3535 !important;
}
.danger-btn > button:hover {
    border-color: #ef4444 !important; color: #ef4444 !important;
    box-shadow: 0 0 12px #ef444422 !important; transform: none !important;
}

/* STATUS */
[data-testid="stStatus"] {
    background: #0d1525 !important; border: 1px solid #1e2a40 !important;
    border-radius: 10px !important;
}
hr { border-color: #1e2640 !important; }

/* LOGIN */
.login-wrap { max-width: 420px; margin: 60px auto 0; }
.login-title {
    font-family: 'Space Mono', monospace; font-size: 1.5rem; font-weight: 700;
    color: #e2e8f0; text-align: center; letter-spacing: 0.1em;
}
.login-title span { color: #3b82f6; }
.login-sub {
    text-align: center; font-size: 0.72rem; color: #4a5568;
    letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 28px;
}
.login-glow {
    width: 100px; height: 100px;
    background: radial-gradient(circle, #3b82f633 0%, transparent 70%);
    border-radius: 50%; margin: 0 auto 12px;
    display: flex; align-items: center; justify-content: center; font-size: 2.5rem;
}

/* TABS */
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #1e2640 !important; gap: 4px !important;
}
[data-testid="stTabs"] [role="tab"] {
    font-family: 'Space Mono', monospace !important; font-size: 0.72rem !important;
    letter-spacing: 0.1em !important; color: #4a5568 !important;
    border-radius: 6px 6px 0 0 !important; padding: 8px 16px !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #60a5fa !important; border-bottom: 2px solid #3b82f6 !important;
}

/* EXPANDER */
[data-testid="stExpander"] {
    background: #0a0f1e !important; border: 1px solid #1a2035 !important;
    border-radius: 10px !important;
}

/* WHATSAPP QR CARD */
.qr-card {
    background: #ffffff !important;
    color: #000000 !important;
    font-family: 'Space Mono', monospace !important;
    padding: 24px !important;
    border-radius: 12px !important;
    line-height: 1.05 !important;
    display: inline-block;
    border: 6px solid #3b82f6 !important;
    margin: 15px 0;
}

/* GLASS LOGIN */
.glass-login {
    background: rgba(15, 23, 41, 0.8);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid #1e2a40;
    border-radius: 16px;
    padding: 40px;
    max-width: 420px;
    margin: 40px auto;
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  UTILS
# ─────────────────────────────────────────────
def color_log_line(line: str) -> str:
    log_line_lower = line.lower()
    if any(k in log_line_lower for k in ("error", "exception", "fail", "traceback", "critical")):
        return f'<span class="log-line-err">{line}</span>'
    if any(k in log_line_lower for k in ("warn", "warning")):
        return f'<span class="log-line-warn">{line}</span>'
    if any(k in log_line_lower for k in ("success", "done", "complete", "✓", "ok", "finish")):
        return f'<span class="log-line-ok">{line}</span>'
    if any(k in log_line_lower for k in ("info", "start", "run", "agent", "tool", "call", "fetch")):
        return f'<span class="log-line-info">{line}</span>'
    return line

def render_log(raw: str, filter_kw: str = "") -> str:
    lines = raw.split("\n")
    if filter_kw:
        lines = [log_line for log_line in lines if filter_kw.lower() in log_line.lower()]
    return "<br>".join(color_log_line(log_line) for log_line in lines)

def prog_html(pct: float, cls: str) -> str:
    w = min(max(pct, 0), 100)
    return f'<div class="prog-wrap"><div class="prog-track"><div class="prog-fill {cls}" style="width:{w}%"></div></div></div>'

def metric_card_html(label, value, sub, bar_pct=None, bar_cls="blue"):
    bar = prog_html(bar_pct, bar_cls) if bar_pct is not None else ""
    return f'<div class="metric-card"><div class="m-label">{label}</div><div class="m-value">{value}</div><div class="m-sub">{sub}</div>{bar}</div>'

def workspace_files() -> list[dict]:
    """Lista arquivos do workspace com metadados."""
    results = []
    ws = "workspace"
    if not os.path.exists(ws):
        return results
    for f in sorted(os.listdir(ws)):
        fp = os.path.join(ws, f)
        if os.path.isfile(fp):
            stat = os.stat(fp)
            results.append({
                "name": f,
                "path": fp,
                "size": stat.st_size,
                "mtime": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m %H:%M"),
            })
    return results

def exec_in_container(container, cmd: str, timeout: int = 30) -> tuple[int, str]:
    """Executa comando no container, retorna (exit_code, output)."""
    try:
        result = container.exec_run(
            ["/bin/sh", "-c", cmd],
            demux=False,
            workdir="/workspace",
        )
        out = result.output.decode("utf-8", errors="replace") if result.output else ""
        return result.exit_code or 0, out
    except Exception as e:
        return 1, f"Erro: {e}"

def ensure_whatsapp_enabled(container) -> bool:
    """Garante que o WhatsApp está habilitado no config.json do container."""
    if container is None:
        return False
    py_cmd = (
        "import json, os; p='/root/.nanobot/config.json'; "
        "d=json.load(open(p)) if os.path.exists(p) and open(p).read() else {}; "
        "d.setdefault('channels', {}).setdefault('whatsapp', {})['enabled']=True; "
        "json.dump(d, open(p, 'w'), indent=2)"
    )
    code, out = exec_in_container(container, f"python3 -c \"{py_cmd}\"")
    return code == 0

def clear_whatsapp_session(container) -> bool:
    """Remove a pasta de autenticação do WhatsApp para resetar a conexão."""
    if container is None:
        return False
    code, out = exec_in_container(container, "rm -rf /root/.nanobot/whatsapp-auth")
    return code == 0

def get_cron_jobs(container) -> list[dict]:
    """Lê crontab do container."""
    try:
        code, out = exec_in_container(container, "crontab -l 2>/dev/null || echo '__EMPTY__'")
        if "__EMPTY__" in out or not out.strip():
            return []
        jobs = []
        for line in out.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 5)
            if len(parts) >= 6:
                schedule = " ".join(parts[:5])
                cmd = parts[5]
                jobs.append({"schedule": schedule, "cmd": cmd, "raw": line})
        return jobs
    except Exception:
        return []

def save_history():
    os.makedirs("workspace", exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(st.session_state.messages, f, ensure_ascii=False, indent=2)


@dataclass
class ManagedProcess:
    name: str
    command: str
    container_name: str
    exec_id: str | None = None
    pid: int | None = None
    running: bool = False
    exit_code: int | None = None
    output_queue: queue.Queue = field(default_factory=queue.Queue)
    output_lines: list[str] = field(default_factory=list)
    reader_thread: threading.Thread | None = None
    qr_code: str = ""
    status_text: str = "stopped"


def init_managed_state() -> None:
    if "managed_processes" not in st.session_state:
        st.session_state.managed_processes = {}
    if "ansi_converter" not in st.session_state:
        st.session_state.ansi_converter = Ansi2HTMLConverter(inline=True)


def _stream_exec_output(proc_key: str, stream, client: docker.DockerClient) -> None:
    managed = st.session_state.managed_processes.get(proc_key)
    if not managed:
        return
    buf = ""
    # Regex flexível para capturar blocos ASCII de QR code (permite espaços entre blocos)
    qr_line_pattern = re.compile(r"^[\s\u2580-\u259F]{15,}$")
    try:
        managed.running = True
        managed.status_text = "running"
        for chunk in stream:
            if chunk is None:
                continue
            text = chunk.decode("utf-8", errors="replace") if isinstance(chunk, (bytes, bytearray)) else str(chunk)
            buf += text
            while "\n" in buf:
                line, buf = buf.split("\n", 1)

                # Captura PID
                if line.startswith("__NB_PID__:"):
                    pid_raw = line.split(":", 1)[1].strip()
                    if pid_raw.isdigit():
                        managed.pid = int(pid_raw)
                    continue

                # Detecta QR Code
                if qr_pattern.search(line):
                    if not managed.qr_code:
                        managed.qr_code = ""
                    managed.qr_code += line + "\n"
                    managed.status_text = "awaiting_scan"

                # Detecta status pelas keywords
                l_line = line.lower()
                if "connected to whatsapp" in l_line or "bot online" in l_line:
                    managed.status_text = "online"
                    managed.qr_code = ""
                elif "link device via qr code" in l_line or "starting bridge" in l_line:
                    managed.status_text = "connecting"
                elif "error" in l_line or "failed" in l_line:
                    managed.status_text = "error"

                managed.output_queue.put(line + "\n")
        if buf:
            managed.output_queue.put(buf)
    finally:
        managed.running = False
        if managed.exec_id:
            try:
                inspect = client.api.exec_inspect(managed.exec_id)
                managed.exit_code = inspect.get("ExitCode")
            except Exception:
                managed.exit_code = None


def start_managed_process(proc_key: str, name: str, command: str, container) -> None:
    if container is None:
        st.error("Container nanobot indisponível.")
        return
    current = st.session_state.managed_processes.get(proc_key)
    if current and current.running:
        st.warning(f"{name} já está em execução.")
        return

    run_cmd = f"{command} & pid=$!; echo __NB_PID__:$pid; wait $pid"
    exec_result = container.exec_run(
        ["/bin/sh", "-lc", run_cmd],
        stream=True,
        demux=False,
        workdir="/workspace",
    )

    managed = ManagedProcess(
        name=name,
        command=command,
        container_name=container.name,
        exec_id=getattr(exec_result, "exec_id", None),
        running=True,
    )
    st.session_state.managed_processes[proc_key] = managed

    thread = threading.Thread(
        target=_stream_exec_output,
        args=(proc_key, exec_result.output, docker_client),
        daemon=True,
    )
    managed.reader_thread = thread
    thread.start()


def _terminate_process(container, managed: ManagedProcess) -> None:
    if not managed.running:
        return
    try:
        if managed.pid:
            container.exec_run(
                ["/bin/sh", "-lc", f"kill -TERM {managed.pid} 2>/dev/null || true"],
                workdir="/workspace",
            )
    except Exception:
        managed.output_queue.put("Falha ao enviar sinal de término via Docker API.\n")
    finally:
        managed.running = False


def stop_managed_processes(container) -> None:
    if container is None:
        st.session_state.managed_processes = {}
        return
    for key, managed in list(st.session_state.managed_processes.items()):
        _terminate_process(container, managed)
        st.session_state.managed_processes.pop(key, None)


def flush_managed_queues() -> None:
    for managed in st.session_state.managed_processes.values():
        while True:
            try:
                managed.output_lines.append(managed.output_queue.get_nowait())
            except queue.Empty:
                break


def render_managed_terminal(managed: ManagedProcess) -> None:
    terminal_text = "".join(managed.output_lines[-500:])
    if not terminal_text.strip():
        st.caption("Sem saída ainda...")
        return

    terminal_html = st.session_state.ansi_converter.convert(terminal_text, full=False)
    components.html(
        f"""
        <div style=\"background:#05070f;border:1px solid #1a2035;border-radius:8px;padding:12px;max-height:320px;overflow:auto;\">
            {terminal_html}
        </div>
        """,
        height=340,
        scrolling=True,
    )


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────
def check_password() -> bool:
    if st.session_state.get("auth", False):
        return True

    # Centraliza o login usando colunas do Streamlit
    _, col, _ = st.columns([1, 1.2, 1])

    with col:
        st.markdown("""
        <div class="glass-login">
          <div class="login-glow">⬡</div>
          <div class="login-title">NANO<span>BOT</span></div>
          <div class="login-sub">Command Center · Secure Access</div>
          <div style="height: 20px;"></div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="username", label_visibility="collapsed")
        password = st.text_input("Token", type="password", placeholder="access token", label_visibility="collapsed")

        if st.button("⬡  AUTHENTICATE", use_container_width=True):
            u_env = os.getenv("DASHBOARD_USER", "admin").strip()
            p_env = os.getenv("DASHBOARD_PASS", "admin123").strip()
            if username.strip() == u_env and password.strip() == p_env:
                st.session_state["auth"] = True
                st.session_state["auth_time"] = datetime.datetime.now().strftime("%H:%M · %d/%m/%Y")
                st.session_state["cmd_history"] = []
                st.rerun()
            else:
                st.error("⚠ Credenciais inválidas")

        st.markdown("</div>", unsafe_allow_html=True)

    return False

if not check_password():
    st.stop()


# ─────────────────────────────────────────────
#  DOCKER
# ─────────────────────────────────────────────
@st.cache_resource
def get_docker():
    try:
        client = docker.from_env(environment={"DOCKER_HOST": "unix:///var/run/docker.sock"})
        container = client.containers.get("nanobot")
        return client, container
    except Exception:
        return None, None

docker_client, nanobot = get_docker()
container_online = nanobot is not None

def container_status() -> tuple[str, str]:
    if not container_online:
        return "OFFLINE", "#ef4444"
    try:
        s = nanobot.status
        return s.upper(), "#22c55e" if s == "running" else "#f59e0b"
    except Exception:
        return "UNKNOWN", "#f59e0b"

c_status, c_color = container_status()

# ─────────────────────────────────────────────
#  PERSISTENCE
# ─────────────────────────────────────────────
HISTORY_PATH = "workspace/chat_history.json"

if "messages" not in st.session_state:
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                st.session_state.messages = json.load(f)
        except Exception:
            st.session_state.messages = []
    else:
        st.session_state.messages = []

if "cmd_history" not in st.session_state:
    st.session_state.cmd_history = []

if "term_output" not in st.session_state:
    st.session_state.term_output = ""

if "last_exec_result" not in st.session_state:
    st.session_state.last_exec_result = None

init_managed_state()
flush_managed_queues()


# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    dot_cls = "status-dot" if container_online else "status-dot offline"
    st.markdown(f"""
    <div class="logo-zone">
      <div class="bot-name">⬡ NANO<span>BOT</span></div>
      <div class="bot-sub"><span class="{dot_cls}"></span>{'System active' if container_online else 'Container offline'}</div>
      <div style="margin-top:14px; font-family:'Space Mono',monospace; font-size:0.65rem; color:#1e3a6e; letter-spacing:0.1em;">
        Container &nbsp;<span style="color:{c_color}; font-weight:700;">{c_status}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    menu = st.radio(
        "Nav",
        [
            "⬡  Terminal",
            "📱 WhatsApp",
            "⌘  Shell Direto",
            "◈  Identidade",
            "⏱  Cron / Agenda",
            "🗂  Memória & Workspace",
            "⚙  Ferramentas",
            "◉  Telemetria",
        ],
        label_visibility="collapsed",
    )

    st.markdown("<br><hr>", unsafe_allow_html=True)

    auth_time = st.session_state.get("auth_time", "—")
    st.markdown(f"""
    <div style="padding:0 12px; font-family:'Space Mono',monospace; font-size:0.63rem; color:#2a3650; line-height:1.9;">
      Session<br><span style="color:#3b4f6e;">{auth_time}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("⏻  Logout", use_container_width=True):
        st.session_state["auth"] = False
        st.rerun()


# ═══════════════════════════════════════════════════
#  PAGE: TERMINAL (AGENTE)
# ═══════════════════════════════════════════════════
if "Terminal" in menu:
    col_chat, col_brain = st.columns([0.55, 0.45], gap="large")

    st.markdown('<div class="sec-header">⚡ Processos CLI Nanobot</div>', unsafe_allow_html=True)
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        if st.button("Iniciar nanobot channels login", use_container_width=True):
            start_managed_process("channels_login", "nanobot channels login", "nanobot channels login", nanobot)
            st.success("Processo de login iniciado em background.")
    with btn_col2:
        if st.button("Iniciar nanobot gateway", use_container_width=True):
            start_managed_process("gateway", "nanobot gateway", "nanobot gateway", nanobot)
            st.success("Gateway iniciado em background.")
    with btn_col3:
        if st.button("Parar Processos", use_container_width=True):
            stop_managed_processes(nanobot)
            st.info("Processos do nanobot encerrados.")

    if st.session_state.managed_processes:
        for key, managed in st.session_state.managed_processes.items():
            status = "🟢 Rodando" if managed.running else "🔴 Finalizado"
            pid_label = managed.pid if managed.pid is not None else "n/a"
            st.markdown(f"**{managed.name}** · PID `{pid_label}` · {status}")
            render_managed_terminal(managed)

    with col_chat:
        st.markdown('<div class="sec-header">⬡ Chat com o Agente</div>', unsafe_allow_html=True)

        # mode selector
        mode_col, clear_col = st.columns([2, 1])
        with mode_col:
            agent_mode = st.selectbox(
                "Modo",
                ["agent", "quick", "web", "task"],
                format_func=lambda x: {
                    "agent": "🤖 Agent (padrão)",
                    "quick": "⚡ Quick (sem tools)",
                    "web":   "🌐 Web Search",
                    "task":  "📋 Task Runner",
                }[x],
                label_visibility="collapsed",
            )
        with clear_col:
            if st.button("✕ Limpar", use_container_width=True):
                st.session_state.messages = []
                if os.path.exists(HISTORY_PATH):
                    os.remove(HISTORY_PATH)
                st.rerun()

        chat_box = st.container(height=450, border=False)
        with chat_box:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if prompt := st.chat_input("Insira o comando para o agente..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_box:
                with st.chat_message("user"):
                    st.markdown(prompt)

            if not container_online:
                err = "⚠ Container `nanobot` offline. Verifique o Docker."
                st.session_state.messages.append({"role": "assistant", "content": err})
                with chat_box:
                    with st.chat_message("assistant"):
                        st.error(err)
            else:
                # Monta comando conforme modo
                cmd_map = {
                    "agent": f"nanobot agent -m '{prompt}'",
                    "quick": f"nanobot chat -m '{prompt}'",
                    "web":   f"nanobot agent --tools web -m '{prompt}'",
                    "task":  f"nanobot task run '{prompt}'",
                }
                cmd = cmd_map.get(agent_mode, f"nanobot agent -m '{prompt}'")

                with chat_box:
                    with st.chat_message("assistant"):
                        with st.status("⬡ Processando...", expanded=False) as status:
                            try:
                                code, response_text = exec_in_container(nanobot, cmd)
                                st.markdown(response_text)
                                st.session_state.messages.append({"role": "assistant", "content": response_text})
                                save_history()
                                if code == 0:
                                    status.update(label="✓ Concluído", state="complete")
                                else:
                                    status.update(label=f"⚠ Exit code {code}", state="error")
                            except Exception as e:
                                err_msg = f"Erro: `{e}`"
                                st.error(err_msg)
                                st.session_state.messages.append({"role": "assistant", "content": err_msg})
                                status.update(label="✗ Falhou", state="error")

    # THOUGHT STREAM
    with col_brain:
        st.markdown('<div class="sec-header">◈ Thought Stream</div>', unsafe_allow_html=True)

        tab_logs, tab_stats = st.tabs(["  Logs  ", "  Stats  "])

        with tab_logs:
            log_filter = st.text_input("Filtrar logs", placeholder="ex: error, tool, agent...", label_visibility="collapsed")
            live = st.toggle("Live 5s", value=False)
            log_placeholder = st.empty()

            if container_online:
                try:
                    raw_logs = nanobot.logs(tail=100).decode("utf-8", errors="replace")
                    colored_html = render_log(raw_logs, filter_kw=log_filter)
                    log_placeholder.markdown(f'<div class="log-box">{colored_html}</div>', unsafe_allow_html=True)
                except Exception as e:
                    log_placeholder.error(f"Erro ao buscar logs: {e}")
            else:
                log_placeholder.markdown('<div class="log-box"><span class="log-line-err">⚠ Container offline</span></div>', unsafe_allow_html=True)

            if container_online and st.button("💾 Exportar Logs"):
                try:
                    raw = nanobot.logs(tail=500).decode("utf-8", errors="replace")
                    fname = f"nanobot_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    os.makedirs("workspace", exist_ok=True)
                    with open(f"workspace/{fname}", "w") as lf:
                        lf.write(raw)
                    st.success(f"Salvo em workspace/{fname}")
                except Exception as e:
                    st.error(f"Erro: {e}")

            if live:
                time.sleep(5)
                st.rerun()

        with tab_stats:
            if container_online:
                try:
                    stats = nanobot.stats(stream=False)
                    # CPU
                    cpu_delta  = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                    sys_delta  = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
                    num_cpus   = stats["cpu_stats"].get("online_cpus", 1)
                    cpu_pct    = (cpu_delta / sys_delta) * num_cpus * 100.0 if sys_delta > 0 else 0
                    # MEM
                    mem_usage  = stats["memory_stats"].get("usage", 0) / 1e6
                    mem_limit  = stats["memory_stats"].get("limit", 1) / 1e6
                    mem_pct    = (mem_usage / mem_limit) * 100 if mem_limit > 0 else 0
                    # NET
                    net_stats  = stats.get("networks", {})
                    rx_total   = sum(v.get("rx_bytes", 0) for v in net_stats.values()) / 1e6
                    tx_total   = sum(v.get("tx_bytes", 0) for v in net_stats.values()) / 1e6

                    st.markdown(metric_card_html("Container CPU", f"<span class='m-accent'>{cpu_pct:.1f}</span>%", f"{num_cpus} vCPUs", cpu_pct, "blue"), unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(metric_card_html("Container RAM", f"<span class='m-accent'>{mem_usage:.0f}</span> MB", f"{mem_pct:.1f}% de {mem_limit:.0f} MB", mem_pct, "green"), unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    cols = st.columns(2)
                    cols[0].markdown(metric_card_html("NET RX", f"<span class='m-accent'>{rx_total:.1f}</span>", "MB recebidos"), unsafe_allow_html=True)
                    cols[1].markdown(metric_card_html("NET TX", f"<span class='m-accent'>{tx_total:.1f}</span>", "MB enviados"), unsafe_allow_html=True)
                except Exception as e:
                    st.warning(f"Stats indisponíveis: {e}")
            else:
                st.error("Container offline")

    if any(p.running for p in st.session_state.managed_processes.values()):
        time.sleep(1)
        st.rerun()

# ═══════════════════════════════════════════════════
#  PAGE: WHATSAPP
# ═══════════════════════════════════════════════════
elif "WhatsApp" in menu:
    st.markdown('<div class="sec-header">📱 Integração Nativa WhatsApp</div>', unsafe_allow_html=True)

    if not container_online:
        st.error("⚠ Container `nanobot` offline. Verifique o Docker.")
    else:
        # Garante configuração habilitada
        if ensure_whatsapp_enabled(nanobot):
            st.caption("✓ WhatsApp habilitado no config.json")

        col_ctrl, col_qr = st.columns([0.4, 0.6], gap="large")

        with col_ctrl:
            st.markdown('<div class="sec-header">⚡ Controle de Conexão</div>', unsafe_allow_html=True)

            # Status Visual
            ws_proc = st.session_state.managed_processes.get("channels_login") or st.session_state.managed_processes.get("wa_gateway")
            current_stat = ws_proc.status_text if ws_proc else "stopped"

            stat_map = {
                "stopped": ("🔴 Desconectado", "error"),
                "running": ("🟡 Inicializando...", "running"),
                "connecting": ("🟡 Conectando Bridge...", "running"),
                "awaiting_scan": ("🔵 Aguardando Scan...", "running"),
                "online": ("🟢 Bot Online", "complete"),
                "error": ("🔴 Erro na Conexão", "error")
            }
            label, state = stat_map.get(current_stat, ("⚪ Desconhecido", "error"))

            with st.status(label, state=state, expanded=True):
                if current_stat == "awaiting_scan":
                    st.write("Aponte o WhatsApp do celular para o QR Code ao lado.")
                elif current_stat == "online":
                    st.write("O bot está conectado e pronto para responder mensagens.")
                elif current_stat == "stopped":
                    st.write("Inicie o processo de login ou gateway.")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("🔗 Iniciar Conexão (QR Code)", use_container_width=True):
                start_managed_process("channels_login", "WhatsApp Login", "nanobot channels login", nanobot)
                st.rerun()

            if st.button("🚀 Iniciar Gateway Background", use_container_width=True):
                start_managed_process("wa_gateway", "WhatsApp Gateway", "nanobot gateway", nanobot)
                st.rerun()

            st.markdown("<br><hr>", unsafe_allow_html=True)

            if st.button("🛑 Parar Todos os Processos", use_container_width=True):
                stop_managed_processes(nanobot)
                st.rerun()

            st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
            if st.button("🗑️ Limpar Sessão / Logout", use_container_width=True):
                if clear_whatsapp_session(nanobot):
                    st.success("Sessão limpa com sucesso.")
                    stop_managed_processes(nanobot)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with col_qr:
            st.markdown('<div class="sec-header">📸 QR Code de Autenticação</div>', unsafe_allow_html=True)

            proc = st.session_state.managed_processes.get("channels_login")
            if proc and proc.qr_code:
                st.markdown(f'<div class="qr-card"><pre style="margin:0; padding:0; line-height:1;">{proc.qr_code}</pre></div>', unsafe_allow_html=True)
                if st.button("🔄 Forçar Atualização UI"):
                    st.rerun()
            elif proc and proc.running:
                st.info("Aguardando geração do QR Code...")
                st.spinner("Processando...")
            else:
                st.info("O QR Code aparecerá aqui após iniciar a conexão.")

    if any(p.running for p in st.session_state.managed_processes.values()):
        time.sleep(2)
        st.rerun()

# ═══════════════════════════════════════════════════
#  PAGE: SHELL DIRETO
# ═══════════════════════════════════════════════════
elif "Shell" in menu:
    st.markdown('<div class="sec-header">⌘ Shell Direto no Container</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.72rem; color:#374151; font-family:Space Mono,monospace; margin-bottom:16px;">'
        'Execute comandos shell diretamente no container nanobot — útil para debug, inspeção e operações avançadas.'
        '</div>',
        unsafe_allow_html=True,
    )

    col_cmd, col_opts = st.columns([3, 1])
    with col_cmd:
        shell_cmd = st.text_input(
            "Comando",
            placeholder="ls -la workspace/ | head -20",
            label_visibility="collapsed",
        )
    with col_opts:
        workdir = st.selectbox("Diretório", ["/workspace", "/", "/tmp", "/app"], label_visibility="collapsed")

    col_run, col_clear, col_presets = st.columns([1, 1, 2])
    with col_run:
        run_btn = st.button("▶ Executar", use_container_width=True)
    with col_clear:
        if st.button("✕ Limpar", use_container_width=True):
            st.session_state.term_output = ""
            st.session_state.cmd_history = []
            st.rerun()

    # Preset commands
    PRESETS = {
        "ls workspace":   "ls -la /workspace/",
        "env vars":       "env | sort",
        "processos":      "ps aux",
        "disco":          "df -h",
        "memoria":        "free -h",
        "python version": "python3 --version && pip3 list 2>/dev/null | head -20",
        "nanobot help":   "nanobot --help 2>&1 || nanobot -h 2>&1",
        "nanobot version":"nanobot version 2>&1 || nanobot --version 2>&1",
        "crontab":        "crontab -l 2>&1",
        "network":        "ip addr && echo '---' && curl -s --max-time 3 https://api.ipify.org 2>/dev/null",
        "pip list":       "pip3 list 2>/dev/null",
        "history":        "cat /workspace/chat_history.json 2>/dev/null | python3 -m json.tool | head -60",
    }

    with col_presets:
        preset = st.selectbox("Comandos rápidos", ["— escolha —"] + list(PRESETS.keys()), label_visibility="collapsed")
        if preset != "— escolha —":
            shell_cmd = PRESETS[preset]

    if (run_btn or preset != "— escolha —") and shell_cmd.strip():
        if not container_online:
            st.error("Container offline")
        else:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            with st.spinner("Executando..."):
                actual_cmd = f"cd {workdir} && {shell_cmd}"
                code, out = exec_in_container(nanobot, actual_cmd)

            entry = f"[{ts}] $ {shell_cmd}\n{out}\n{'─'*60}\n"
            st.session_state.term_output = entry + st.session_state.term_output
            st.session_state.cmd_history.insert(0, {"ts": ts, "cmd": shell_cmd, "code": code})

    # Output terminal
    st.markdown(
        f'<div class="term-box">{st.session_state.term_output or "# Aguardando comando..."}</div>',
        unsafe_allow_html=True,
    )

    # Command history
    if st.session_state.cmd_history:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="sec-header">⬡ Histórico de Comandos</div>', unsafe_allow_html=True)
        for entry in st.session_state.cmd_history[:15]:
            code_color = "#22c55e" if entry["code"] == 0 else "#ef4444"
            st.markdown(
                f'<div style="font-family:Space Mono,monospace; font-size:0.68rem; padding:6px 12px; '
                f'background:#0a0f1e; border:1px solid #1a2035; border-radius:6px; margin-bottom:4px;">'
                f'<span style="color:#2a3a54;">[{entry["ts"]}]</span> '
                f'<span style="color:#94a3b8;">{entry["cmd"][:80]}</span> '
                f'<span style="color:{code_color}; float:right;">exit {entry["code"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════
#  PAGE: IDENTIDADE
# ═══════════════════════════════════════════════════
elif "Identidade" in menu:
    st.markdown('<div class="sec-header">◈ Gestão de Identidade & Alma</div>', unsafe_allow_html=True)

    FILES = {
        "IDENTITY.md": "Quem o agente é — função, especialidade, missão.",
        "SOUL.md":     "Tom de voz, ética e valores centrais.",
        "USER.md":     "Memória persistente sobre o usuário.",
        "AGENTS.md":   "Configuração de sub-agentes e delegações.",
        "TOOLS.md":    "Ferramentas disponíveis e instruções de uso.",
        "MEMORY.md":   "Memória de longo prazo estruturada.",
    }

    col_sel, col_actions = st.columns([2, 1])
    with col_sel:
        selected = st.selectbox("Arquivo", list(FILES.keys()), format_func=lambda x: f"⬡ {x}", label_visibility="collapsed")
    with col_actions:
        new_file = st.text_input("Novo arquivo", placeholder="CUSTOM.md", label_visibility="collapsed")

    if new_file.strip():
        selected = new_file.strip()
        if not selected.endswith(".md"):
            selected += ".md"

    if selected:
        desc = FILES.get(selected, "Arquivo customizado.")
        st.markdown(
            f'<div style="font-size:0.72rem; color:#374151; margin-bottom:12px; font-family:Space Mono,monospace;">{desc}</div>',
            unsafe_allow_html=True,
        )

        path = f"workspace/{selected}"
        content = ""
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

        col_edit, col_preview = st.tabs(["  ✎ Editor  ", "  👁 Preview  "])

        with col_edit:
            new_content = st.text_area(
                "Conteúdo",
                value=content,
                height=420,
                placeholder=f"# {selected}\n\n",
                label_visibility="collapsed",
            )

            col_save, col_reset, col_delete, _ = st.columns([1, 1, 1, 2])
            with col_save:
                if st.button("💾 Salvar", use_container_width=True):
                    os.makedirs("workspace", exist_ok=True)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    st.success(f"✓ {selected} salvo.")
                    # Recarrega no container se online
                    if container_online:
                        exec_in_container(nanobot, f"cp /workspace/{selected} /workspace/{selected}.bak 2>/dev/null; echo ok")
            with col_reset:
                if st.button("↺ Resetar", use_container_width=True):
                    st.rerun()
            with col_delete:
                with st.container():
                    if os.path.exists(path):
                        if st.button("🗑 Deletar", use_container_width=True):
                            os.remove(path)
                            st.warning(f"✗ {selected} removido.")
                            st.rerun()

            chars = len(new_content)
            words = len(new_content.split()) if new_content.strip() else 0
            lines = new_content.count("\n") + 1 if new_content else 0
            st.markdown(
                f'<div style="font-size:0.63rem; color:#1e2640; font-family:Space Mono,monospace; margin-top:6px;">'
                f'{words} palavras · {chars} chars · {lines} linhas</div>',
                unsafe_allow_html=True,
            )

        with col_preview:
            if content:
                st.markdown(content)
            else:
                st.markdown("_Arquivo vazio ou não encontrado._")


# ═══════════════════════════════════════════════════
#  PAGE: CRON / AGENDA
# ═══════════════════════════════════════════════════
elif "Cron" in menu:
    st.markdown('<div class="sec-header">⏱ Gerenciador de Tarefas Agendadas</div>', unsafe_allow_html=True)

    if not container_online:
        st.error("⚠ Container offline — sem acesso ao crontab.")
    else:
        tab_list, tab_add, tab_ref = st.tabs(["  Lista  ", "  Adicionar  ", "  Referência  "])

        with tab_list:
            jobs = get_cron_jobs(nanobot)
            if not jobs:
                st.markdown(
                    '<div class="glass-card" style="text-align:center; color:#2a3650; font-family:Space Mono,monospace; font-size:0.78rem;">'
                    'Nenhuma tarefa agendada.<br><span style="font-size:0.65rem;">Use a aba Adicionar para criar.</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f'<div style="font-size:0.68rem; color:#2a3650; font-family:Space Mono,monospace; margin-bottom:12px;">{len(jobs)} tarefa(s) ativa(s)</div>', unsafe_allow_html=True)
                for i, job in enumerate(jobs):
                    col_info, col_del = st.columns([5, 1])
                    with col_info:
                        st.markdown(
                            f'<div class="cron-row">'
                            f'<span class="cron-schedule">{job["schedule"]}</span>'
                            f'<span class="cron-cmd">{job["cmd"]}</span>'
                            f'<span class="cron-badge">ATIVO</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    with col_del:
                        if st.button("✕", key=f"del_cron_{i}", help="Remover tarefa"):
                            # Remove linha do crontab
                            code, current = exec_in_container(nanobot, "crontab -l 2>/dev/null")
                            new_cron = "\n".join(
                                cron_line for cron_line in current.split("\n")
                                if cron_line.strip() != job["raw"].strip() and cron_line.strip()
                            )
                            exec_in_container(nanobot, f"echo '{new_cron}' | crontab -")
                            st.success("Tarefa removida.")
                            st.rerun()

            # Botão para executar cron manualmente agora
            st.markdown("<br>", unsafe_allow_html=True)
            if jobs:
                st.markdown('<div class="sec-header">⬡ Execução Manual</div>', unsafe_allow_html=True)
                job_sel = st.selectbox("Tarefa", [j["cmd"] for j in jobs], label_visibility="collapsed")
                if st.button("▶ Executar Agora", use_container_width=False):
                    with st.spinner("Executando..."):
                        code, out = exec_in_container(nanobot, job_sel)
                    if code == 0:
                        st.success("✓ Executado com sucesso")
                    else:
                        st.error(f"Exit code {code}")
                    st.code(out, language="text")

        with tab_add:
            st.markdown(
                '<div style="font-size:0.72rem; color:#374151; font-family:Space Mono,monospace; margin-bottom:16px;">'
                'Adiciona nova tarefa ao crontab do container nanobot.'
                '</div>',
                unsafe_allow_html=True,
            )

            col_sched, col_cmd2 = st.columns([1, 2])
            with col_sched:
                schedule_preset = st.selectbox(
                    "Schedule",
                    ["Personalizado", "@hourly", "@daily", "@weekly", "@reboot",
                     "*/5 * * * *", "*/15 * * * *", "*/30 * * * *",
                     "0 * * * *", "0 0 * * *", "0 9 * * 1-5"],
                    label_visibility="collapsed",
                )
                if schedule_preset == "Personalizado":
                    cron_schedule = st.text_input("Schedule manual", placeholder="*/10 * * * *", label_visibility="collapsed")
                else:
                    cron_schedule = schedule_preset
                    st.markdown(f'<div style="font-size:0.65rem; color:#3b82f6; font-family:Space Mono,monospace;">{cron_schedule}</div>', unsafe_allow_html=True)

            with col_cmd2:
                cron_cmd = st.text_input("Comando", placeholder="nanobot agent -m 'relatório diário'", label_visibility="collapsed")

            if st.button("+ Adicionar Tarefa", use_container_width=False):
                if cron_schedule and cron_cmd:
                    new_line = f"{cron_schedule} {cron_cmd}"
                    code, current = exec_in_container(nanobot, "crontab -l 2>/dev/null || echo ''")
                    current = current.strip()
                    new_cron = (current + "\n" + new_line).strip()
                    r_code, _ = exec_in_container(nanobot, f'echo "{new_cron}" | crontab -')
                    if r_code == 0:
                        st.success(f"✓ Tarefa adicionada: `{new_line}`")
                        st.rerun()
                    else:
                        st.error("Erro ao salvar crontab.")
                else:
                    st.warning("Preencha schedule e comando.")

        with tab_ref:
            st.markdown("""
            <div class="glass-card" style="font-family:'Space Mono',monospace; font-size:0.72rem; line-height:2.2; color:#64748b;">
              <span style="color:#3b82f6;">Formato:</span> <span style="color:#94a3b8;">min hora dia mês dia_semana comando</span><br><br>
              <span style="color:#2a3a54;">┌── minuto (0-59)</span><br>
              <span style="color:#2a3a54;">│ ┌── hora (0-23)</span><br>
              <span style="color:#2a3a54;">│ │ ┌── dia do mês (1-31)</span><br>
              <span style="color:#2a3a54;">│ │ │ ┌── mês (1-12)</span><br>
              <span style="color:#2a3a54;">│ │ │ │ ┌── dia da semana (0=Dom, 6=Sab)</span><br>
              <span style="color:#60a5fa;">* * * * * comando</span><br><br>
              <span style="color:#3b82f6;">Exemplos:</span><br>
              <span style="color:#22c55e;">*/5 * * * *</span> → a cada 5 minutos<br>
              <span style="color:#22c55e;">0 9 * * 1-5</span> → 9h de segunda a sexta<br>
              <span style="color:#22c55e;">@daily</span> → uma vez por dia à meia-noite<br>
              <span style="color:#22c55e;">@reboot</span> → ao iniciar o container
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
#  PAGE: MEMÓRIA & WORKSPACE
# ═══════════════════════════════════════════════════
elif "Memória" in menu:
    st.markdown('<div class="sec-header">🗂 Memória & Workspace do Agente</div>', unsafe_allow_html=True)

    files = workspace_files()

    col_files, col_viewer = st.columns([0.35, 0.65], gap="large")

    with col_files:
        st.markdown('<div class="sec-header">⬡ Arquivos</div>', unsafe_allow_html=True)

        # Disk usage do workspace
        total_size = sum(f["size"] for f in files)
        st.markdown(
            f'<div style="font-family:Space Mono,monospace; font-size:0.65rem; color:#2a3650; margin-bottom:12px;">'
            f'{len(files)} arquivos · {total_size/1e3:.1f} KB total'
            f'</div>',
            unsafe_allow_html=True,
        )

        if not files:
            st.markdown('<div class="glass-card" style="font-family:Space Mono,monospace; font-size:0.72rem; color:#2a3650;">Workspace vazio.</div>', unsafe_allow_html=True)
        else:
            selected_file = st.radio(
                "Arquivo",
                [f["name"] for f in files],
                label_visibility="collapsed",
                format_func=lambda x: f"⬡ {x}",
            )

            # Upload de novo arquivo
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="sec-header">⬡ Upload</div>', unsafe_allow_html=True)
            uploaded = st.file_uploader("Enviar para workspace", label_visibility="collapsed")
            if uploaded:
                os.makedirs("workspace", exist_ok=True)
                with open(f"workspace/{uploaded.name}", "wb") as uf:
                    uf.write(uploaded.getbuffer())
                st.success(f"✓ {uploaded.name} enviado.")
                st.rerun()

    with col_viewer:
        st.markdown('<div class="sec-header">⬡ Visualizador / Editor</div>', unsafe_allow_html=True)

        if not files:
            st.markdown('<div class="glass-card" style="text-align:center; font-family:Space Mono,monospace; font-size:0.78rem; color:#2a3650;">Nenhum arquivo no workspace.</div>', unsafe_allow_html=True)
        else:
            sel_f = next((f for f in files if f["name"] == selected_file), None)
            if sel_f:
                size_kb = sel_f["size"] / 1e3
                st.markdown(
                    f'<div style="font-family:Space Mono,monospace; font-size:0.65rem; color:#2a3650; margin-bottom:8px;">'
                    f'{sel_f["name"]} · {size_kb:.1f} KB · modificado {sel_f["mtime"]}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                ext = sel_f["name"].rsplit(".", 1)[-1].lower()
                try:
                    with open(sel_f["path"], "r", encoding="utf-8") as f:
                        file_content = f.read()

                    if ext == "json":
                        # Viewer JSON formatado
                        try:
                            parsed = json.loads(file_content)
                            view_tab, edit_tab = st.tabs(["  👁 JSON  ", "  ✎ Editar  "])
                            with view_tab:
                                st.json(parsed)
                            with edit_tab:
                                edited = st.text_area("JSON", value=json.dumps(parsed, indent=2, ensure_ascii=False), height=400, label_visibility="collapsed")
                                if st.button("💾 Salvar JSON"):
                                    try:
                                        json.loads(edited)  # valida
                                        with open(sel_f["path"], "w", encoding="utf-8") as f:
                                            f.write(edited)
                                        st.success("✓ Salvo.")
                                    except json.JSONDecodeError as je:
                                        st.error(f"JSON inválido: {je}")
                        except json.JSONDecodeError:
                            st.code(file_content, language="text")
                    elif ext in ("md", "txt", "sh", "py", "yaml", "yml", "toml", "ini", "env"):
                        lang_map = {"md": "markdown", "sh": "bash", "py": "python",
                                    "yaml": "yaml", "yml": "yaml", "toml": "toml"}
                        lang = lang_map.get(ext, "text")
                        view_tab, edit_tab = st.tabs(["  👁 View  ", "  ✎ Editar  "])
                        with view_tab:
                            if ext == "md":
                                st.markdown(file_content)
                            else:
                                st.code(file_content, language=lang)
                        with edit_tab:
                            edited_txt = st.text_area("Conteúdo", value=file_content, height=420, label_visibility="collapsed")
                            col_sv, col_dl2, _ = st.columns([1, 1, 2])
                            with col_sv:
                                if st.button("💾 Salvar"):
                                    with open(sel_f["path"], "w", encoding="utf-8") as f:
                                        f.write(edited_txt)
                                    st.success("✓ Salvo.")
                            with col_dl2:
                                st.download_button("⬇ Download", file_content, file_name=sel_f["name"])
                    else:
                        st.code(file_content[:5000], language="text")
                        if len(file_content) > 5000:
                            st.caption("(Truncado nos primeiros 5000 chars)")

                except UnicodeDecodeError:
                    st.warning("Arquivo binário — não é possível visualizar como texto.")
                    with open(sel_f["path"], "rb") as f:
                        bin_data = f.read()
                    st.download_button("⬇ Download binário", bin_data, file_name=sel_f["name"])

                # Delete file
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("⚠ Zona de Perigo"):
                    if st.button(f"🗑 Deletar {sel_f['name']}"):
                        os.remove(sel_f["path"])
                        st.warning(f"✗ {sel_f['name']} deletado.")
                        st.rerun()


# ═══════════════════════════════════════════════════
#  PAGE: FERRAMENTAS
# ═══════════════════════════════════════════════════
elif "Ferramentas" in menu:
    st.markdown('<div class="sec-header">⚙ Painel de Ferramentas do Agente</div>', unsafe_allow_html=True)

    # Verifica quais ferramentas estão disponíveis
    TOOLS = {
        "web_search": {
            "label": "Web Search",
            "icon": "🌐",
            "desc": "Brave / DuckDuckGo Search API",
            "check_cmd": "env | grep -i 'brave\\|search' | head -5",
            "test_cmd": "nanobot tool web_search 'teste conexão' 2>&1 | head -20",
        },
        "file_ops": {
            "label": "File Operations",
            "icon": "📁",
            "desc": "Leitura e escrita de arquivos no workspace",
            "check_cmd": "ls /workspace/ | wc -l",
            "test_cmd": "nanobot tool file read IDENTITY.md 2>&1 | head -10",
        },
        "code_exec": {
            "label": "Code Executor",
            "icon": "⚡",
            "desc": "Execução de scripts Python/Shell",
            "check_cmd": "python3 --version",
            "test_cmd": "python3 -c \"print('OK')\"",
        },
        "telegram": {
            "label": "Telegram",
            "icon": "📱",
            "desc": "Gateway Telegram Bot API",
            "check_cmd": "env | grep -i 'telegram\\|bot_token' | head -3",
            "test_cmd": "nanobot channel telegram status 2>&1",
        },
        "memory": {
            "label": "Memory Store",
            "icon": "🧠",
            "desc": "Persistência de memória de longo prazo",
            "check_cmd": "ls /workspace/*.md 2>/dev/null | wc -l",
            "test_cmd": "nanobot memory list 2>&1 | head -20",
        },
        "mcp": {
            "label": "MCP Protocol",
            "icon": "🔗",
            "desc": "Model Context Protocol — ferramentas externas",
            "check_cmd": "env | grep -i 'mcp' | head -3",
            "test_cmd": "nanobot mcp list 2>&1 | head -20",
        },
    }

    col_grid = st.columns(3)
    for i, (tool_id, tool) in enumerate(TOOLS.items()):
        with col_grid[i % 3]:
            st.markdown(
                f'<div class="glass-card" style="text-align:center; margin-bottom:12px;">'
                f'<div style="font-size:1.8rem; margin-bottom:8px;">{tool["icon"]}</div>'
                f'<div style="font-family:Space Mono,monospace; font-size:0.8rem; color:#94a3b8; font-weight:700;">{tool["label"]}</div>'
                f'<div style="font-size:0.68rem; color:#2a3650; margin-top:4px;">{tool["desc"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Tool tester
    st.markdown('<div class="sec-header">⬡ Teste de Ferramenta</div>', unsafe_allow_html=True)

    col_tool_sel, col_tool_input = st.columns([1, 2])
    with col_tool_sel:
        selected_tool = st.selectbox(
            "Ferramenta",
            list(TOOLS.keys()),
            format_func=lambda x: f"{TOOLS[x]['icon']} {TOOLS[x]['label']}",
            label_visibility="collapsed",
        )
    with col_tool_input:
        tool_input = st.text_input(
            "Input",
            placeholder="Parâmetro ou deixe vazio para teste padrão...",
            label_visibility="collapsed",
        )

    col_check, col_test = st.columns(2)
    with col_check:
        if st.button("🔍 Verificar Disponibilidade", use_container_width=True):
            if container_online:
                with st.spinner("Verificando..."):
                    code, out = exec_in_container(nanobot, TOOLS[selected_tool]["check_cmd"])
                if out.strip():
                    st.success("✓ Ferramenta detectada")
                    st.code(out.strip()[:500], language="text")
                else:
                    st.warning("⚠ Nenhum output — ferramenta pode estar ausente ou não configurada.")
            else:
                st.error("Container offline")

    with col_test:
        if st.button("▶ Testar Ferramenta", use_container_width=True):
            if container_online:
                tool_cmd = TOOLS[selected_tool]["test_cmd"]
                if tool_input.strip():
                    # Substitui parâmetro de teste se input fornecido
                    tool_cmd = f"nanobot tool {selected_tool} '{tool_input}' 2>&1 | head -30"
                with st.spinner("Testando..."):
                    code, out = exec_in_container(nanobot, tool_cmd)
                st.markdown(f'<div class="term-box">{out or "(sem output)"}</div>', unsafe_allow_html=True)
            else:
                st.error("Container offline")

    # Env vars inspector (sem expor valores secretos)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-header">⬡ Variáveis de Ambiente</div>', unsafe_allow_html=True)

    if container_online:
        if st.button("🔍 Listar ENVs configuradas (keys only)"):
            with st.spinner("Listando..."):
                code, out = exec_in_container(nanobot, "env | cut -d= -f1 | sort")
            keys = [env_key for env_key in out.strip().split("\n") if env_key]
            # Destaca vars relacionadas ao nanobot/AI
            AI_KEYS = {"OPENAI_API_KEY", "ANTHROPIC_API_KEY", "BRAVE_API_KEY", "TELEGRAM_TOKEN",
                       "DISCORD_TOKEN", "NANOBOT", "LLM", "MODEL", "GROQ", "MISTRAL"}
            col_env1, col_env2, col_env3 = st.columns(3)
            cols = [col_env1, col_env2, col_env3]
            for i, key in enumerate(keys):
                highlight = any(k in key.upper() for k in AI_KEYS)
                color = "#60a5fa" if highlight else "#2a3a54"
                cols[i % 3].markdown(
                    f'<div style="font-family:Space Mono,monospace; font-size:0.65rem; color:{color}; padding:2px 0;">{key}</div>',
                    unsafe_allow_html=True,
                )


# ═══════════════════════════════════════════════════
#  PAGE: TELEMETRIA
# ═══════════════════════════════════════════════════
elif "Telemetria" in menu:
    st.markdown('<div class="sec-header">◉ Telemetria do Sistema</div>', unsafe_allow_html=True)

    cpu     = psutil.cpu_percent(interval=0.5)
    mem     = psutil.virtual_memory()
    disk    = psutil.disk_usage("/")
    uptime  = datetime.timedelta(seconds=int(time.time() - psutil.boot_time()))
    net     = psutil.net_io_counters()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        bar_cls = "red" if cpu > 90 else "amber" if cpu > 70 else "blue"
        st.markdown(metric_card_html("CPU Usage", f"<span class='m-accent'>{cpu:.1f}</span>%", f"{psutil.cpu_count()} cores", cpu, bar_cls), unsafe_allow_html=True)
    with c2:
        used_gb = mem.used / 1e9
        total_gb = mem.total / 1e9
        bar_cls = "red" if mem.percent > 90 else "amber" if mem.percent > 75 else "green"
        st.markdown(metric_card_html("RAM", f"<span class='m-accent'>{mem.percent:.1f}</span>%", f"{used_gb:.1f} / {total_gb:.1f} GB", mem.percent, bar_cls), unsafe_allow_html=True)
    with c3:
        d_pct = disk.percent
        d_used = disk.used / 1e9
        d_total = disk.total / 1e9
        bar_cls = "red" if d_pct > 90 else "amber" if d_pct > 80 else "blue"
        st.markdown(metric_card_html("Disk", f"<span class='m-accent'>{d_pct:.1f}</span>%", f"{d_used:.0f} / {d_total:.0f} GB", d_pct, bar_cls), unsafe_allow_html=True)
    with c4:
        h, rem = divmod(uptime.seconds, 3600)
        m, _ = divmod(rem, 60)
        st.markdown(metric_card_html("Uptime", f"<span class='m-accent'>{uptime.days}d</span>", f"{h:02d}h {m:02d}m"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_net, col_proc, col_cont = st.columns([1, 1, 1], gap="large")

    with col_net:
        st.markdown('<div class="sec-header">⬡ Rede</div>', unsafe_allow_html=True)
        sent_mb = net.bytes_sent / 1e6
        recv_mb = net.bytes_recv / 1e6
        st.markdown(f"""
        <div class="glass-card">
          <div style="display:flex; gap:24px; align-items:center; flex-wrap:wrap;">
            <div>
              <div style="font-family:'Space Mono',monospace; font-size:0.62rem; letter-spacing:0.15em; color:#4a5568; margin-bottom:4px;">TX</div>
              <div style="font-family:'Space Mono',monospace; font-size:1.3rem; color:#60a5fa; font-weight:700;">{sent_mb:.1f}<span style="font-size:0.72rem; color:#4a5568;"> MB</span></div>
            </div>
            <div style="width:1px; height:36px; background:#1e2640;"></div>
            <div>
              <div style="font-family:'Space Mono',monospace; font-size:0.62rem; letter-spacing:0.15em; color:#4a5568; margin-bottom:4px;">RX</div>
              <div style="font-family:'Space Mono',monospace; font-size:1.3rem; color:#4ade80; font-weight:700;">{recv_mb:.1f}<span style="font-size:0.72rem; color:#4a5568;"> MB</span></div>
            </div>
          </div>
          <div style="margin-top:14px; font-family:'Space Mono',monospace; font-size:0.65rem; color:#2a3650; line-height:1.9;">
            Pkts sent &nbsp;<span style="color:#3b5278;">{net.packets_sent:,}</span><br>
            Pkts recv &nbsp;<span style="color:#3b5278;">{net.packets_recv:,}</span><br>
            Errs out &nbsp;&nbsp;<span style="color:{'#ef4444' if net.errout > 0 else '#3b5278'};">{net.errout}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_proc:
        st.markdown('<div class="sec-header">⬡ Processos</div>', unsafe_allow_html=True)
        procs = sorted(psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]),
                       key=lambda p: p.info.get("cpu_percent") or 0, reverse=True)[:6]
        rows = ""
        for p in procs:
            try:
                mem_mb = (p.info.get("memory_info") and p.info["memory_info"].rss / 1e6) or 0
                cpu_p  = p.info.get("cpu_percent") or 0
                name   = (p.info.get("name") or "?")[:16]
                rows += (
                    f'<div style="display:grid; grid-template-columns:30px 1fr 60px 50px; gap:8px; '
                    f'padding:5px 0; border-bottom:1px solid #0d1525; font-family:Space Mono,monospace; font-size:0.65rem;">'
                    f'<span style="color:#2a3650;">{p.info["pid"]}</span>'
                    f'<span style="color:#64748b;">{name}</span>'
                    f'<span style="color:#3b82f6;">{cpu_p:.1f}%</span>'
                    f'<span style="color:#4a5568;">{mem_mb:.0f}M</span>'
                    f'</div>'
                )
            except Exception:
                continue
        st.markdown(f'<div class="glass-card">{rows}</div>', unsafe_allow_html=True)

    with col_cont:
        st.markdown('<div class="sec-header">⬡ Container</div>', unsafe_allow_html=True)
        if container_online:
            try:
                attrs   = nanobot.attrs
                image   = attrs.get("Config", {}).get("Image", "—")
                created = attrs.get("Created", "")[:19].replace("T", " ")
                name    = attrs.get("Name", "—").lstrip("/")
                c_id    = attrs.get("Id", "—")[:12]
                restart = attrs.get("RestartCount", 0)

                # Container stats
                try:
                    stats = nanobot.stats(stream=False)
                    cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                    sys_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
                    n_cpu = stats["cpu_stats"].get("online_cpus", 1)
                    cont_cpu = (cpu_delta / sys_delta) * n_cpu * 100.0 if sys_delta > 0 else 0
                    cont_mem = stats["memory_stats"].get("usage", 0) / 1e6
                    stats_html = (
                        f'CPU &nbsp;&nbsp;&nbsp;&nbsp; <span style="color:#60a5fa;">{cont_cpu:.1f}%</span><br>'
                        f'RAM &nbsp;&nbsp;&nbsp;&nbsp; <span style="color:#4ade80;">{cont_mem:.0f} MB</span><br>'
                    )
                except Exception:
                    stats_html = ""

                st.markdown(f"""
                <div class="glass-card" style="font-family:'Space Mono',monospace; font-size:0.7rem; line-height:2.1; color:#4a5568;">
                  <span style="color:{c_color}; font-weight:700; letter-spacing:.1em;">● {c_status}</span><br>
                  {stats_html}
                  Name &nbsp;&nbsp;&nbsp; <span style="color:#64748b;">{name}</span><br>
                  ID &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <span style="color:#64748b;">{c_id}</span><br>
                  Image &nbsp;&nbsp; <span style="color:#64748b; font-size:0.62rem;">{image}</span><br>
                  Created &nbsp;<span style="color:#64748b;">{created}</span><br>
                  Restarts <span style="color:{'#ef4444' if restart > 0 else '#64748b'};">{restart}</span>
                </div>
                """, unsafe_allow_html=True)

                # Container actions
                st.markdown("<br>", unsafe_allow_html=True)
                col_r, col_s = st.columns(2)
                with col_r:
                    if st.button("⟳ Restart", use_container_width=True):
                        with st.spinner("Reiniciando..."):
                            nanobot.restart(timeout=10)
                        st.success("✓ Reiniciado.")
                        st.cache_resource.clear()
                        st.rerun()
                with col_s:
                    if st.button("⏸ Stop", use_container_width=True):
                        with st.spinner("Parando..."):
                            nanobot.stop(timeout=5)
                        st.warning("Container parado.")
                        st.cache_resource.clear()
                        st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
        else:
            st.markdown("""
            <div class="glass-card">
              <span style="font-family:'Space Mono',monospace; font-size:0.8rem; color:#ef4444; letter-spacing:.1em;">⚠ OFFLINE</span><br>
              <span style="font-size:0.72rem; color:#4a5568;">
                Execute: <code style="color:#3b82f6;">docker start nanobot</code>
              </span>
            </div>
            """, unsafe_allow_html=True)

            if st.button("▶ Iniciar Container"):
                try:
                    docker_client.containers.get("nanobot").start()
                    st.success("✓ Container iniciado.")
                    st.cache_resource.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao iniciar: {e}")

    # Auto refresh
    st.markdown("<br>", unsafe_allow_html=True)
    if st.toggle("⟳ Auto-refresh (10s)", value=False):
        time.sleep(10)
        st.rerun()
