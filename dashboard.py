import streamlit as st
import docker
import os
import json
import psutil
import time

# --- 1. CONFIGURAÇÃO DE ALTO NÍVEL ---
st.set_page_config(page_title="NANOBOT CORE | Command Center", page_icon="⚡", layout="wide")

# CSS Avançado para estabilidade e estética
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .thinking-box { 
        background-color: #0a0c10; border-left: 3px solid #238636; 
        padding: 10px; border-radius: 5px; font-family: 'Courier New', monospace;
        font-size: 0.8rem; color: #8b949e; height: 500px; overflow-y: auto;
    }
    /* Esconde o menu nativo do Streamlit para parecer um App real */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. SISTEMA DE LOGIN (CORRIGIDO PARA NÃO PISCAR) ---
def check_password():
    if st.session_state.get("password_correct", False):
        return True

    # Se não estiver logado, mostra APENAS a tela de login
    st.markdown("<h2 style='text-align: center; color: #58a6ff;'>⚡ NANOBOT CORE LOGIN</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        u = st.text_input("Username").strip()
        p = st.text_input("Security Token", type="password").strip()
        if st.button("AUTHENTICATE", use_container_width=True):
            user_env = os.getenv("DASHBOARD_USER", "admin").strip()
            pass_env = os.getenv("DASHBOARD_PASS", "admin123").strip()
            if u == user_env and p == pass_env:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Access Denied")
    return False

# Interrompe aqui se não estiver logado (evita mostrar o resto no fundo)
if not check_password():
    st.stop()

# --- 3. CONEXÃO DOCKER E PERSISTÊNCIA ---
@st.cache_resource
def get_docker():
    try:
        client = docker.from_env()
        return client, client.containers.get("nanobot")
    except:
        return None, None

docker_client, nanobot = get_docker()

HISTORY_PATH = "workspace/chat_history.json"
if "messages" not in st.session_state:
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "r", encoding="utf-8") as f: st.session_state.messages = json.load(f)
    else: st.session_state.messages = []

# --- 4. BARRA LATERAL ---
with st.sidebar:
    if os.path.exists("nanobot_logo.png"):
        st.image("nanobot_logo.png", width=120)
    else:
        st.title("🤖 NANOBOT")
    
    st.markdown("---")
    menu = st.radio("Navegação", ["🎮 Terminal Tático", "🧠 Alma & Identidade", "📊 Telemetria"])
    
    st.markdown("---")
    if st.button("🔒 Logout"):
        st.session_state["password_correct"] = False
        st.rerun()

# ==========================================
# MODO: TERMINAL TÁTICO
# ==========================================
if menu == "🎮 Terminal Tático":
    col_chat, col_brain = st.columns([0.55, 0.45], gap="medium")

    with col_chat:
        st.subheader("💬 Operações de Campo")
        chat_container = st.container(height=500, border=False)
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if prompt := st.chat_input("Insira o comando..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"): st.markdown(prompt)
            
            with chat_container:
                with st.chat_message("assistant"):
                    with st.status("⚡ Processando...", expanded=False) as status:
                        try:
                            exec_res = nanobot.exec_run(f"nanobot agent -m '{prompt}'")
                            response_text = exec_res.output.decode("utf-8")
                            st.markdown(response_text)
                            st.session_state.messages.append({"role": "assistant", "content": response_text})
                            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                                json.dump(st.session_state.messages, f, ensure_ascii=False)
                            status.update(label="✅ Concluído", state="complete")
                        except Exception as e:
                            st.error(f"Erro: {e}")

    with col_brain:
        st.subheader("🧠 Thought Stream")
        run_logs = st.toggle("Live Stream", value=False, help="Ative para ver os logs em tempo real (pode causar leve oscilação)")
        log_placeholder = st.empty()
        
        # Lógica de atualização de logs
        try:
            raw_logs = nanobot.logs(tail=50).decode("utf-8")
            log_placeholder.markdown(f'<div class="thinking-box">{raw_logs}</div>', unsafe_allow_html=True)
        except:
            log_placeholder.error("Container Offline")

        if run_logs:
            time.sleep(3) # Aumentado para 3 segundos para reduzir o piscar
            st.rerun()

# ==========================================
# MODO: ALMA & IDENTIDADE
# ==========================================
elif menu == "🧠 Alma & Identidade":
    st.header("🧠 Gestão de Identidade")
    files = ["IDENTITY.md", "SOUL.md", "USER.md", "AGENTS.md"]
    selected_file = st.selectbox("Selecione o arquivo:", files)
    path = f"workspace/{selected_file}"
    
    content = ""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f: content = f.read()
    
    new_content = st.text_area("Editor:", value=content, height=400)
    if st.button("💾 Salvar Alterações", use_container_width=True):
        with open(path, "w", encoding="utf-8") as f: f.write(new_content)
        st.success("Salvo!")

# ==========================================
# MODO: TELEMETRIA
# ==========================================
elif menu == "📊 Telemetria":
    st.header("📊 Status da VPS")
    c1, c2, c3 = st.columns(3)
    c1.metric("CPU", f"{psutil.cpu_percent()}%")
    c2.metric("RAM", f"{psutil.virtual_memory().percent}%")
    c3.metric("Disk", f"{psutil.disk_usage('/').percent}%")
    st.progress(psutil.cpu_percent() / 100)
    st.progress(psutil.virtual_memory().percent / 100)
