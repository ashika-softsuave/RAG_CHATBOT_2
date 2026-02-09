import streamlit as st
import requests
import json
import os

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="🤖",
    layout="wide"
)

# ---------------- PERSISTENCE ----------------
STORE_FILE = "chat_store.json"

def load_store():
    if os.path.exists(STORE_FILE):
        with open(STORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_store(data):
    with open(STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ---------------- STYLE ----------------
st.markdown("""
<style>
.chat-user {
    background: linear-gradient(135deg, #ff7a18, #ffb347);
    padding: 12px;
    border-radius: 14px;
    margin: 8px 0;
    color: black;
    max-width: 80%;
}
.chat-bot {
    background: linear-gradient(135deg, #232526, #414345);
    padding: 12px;
    border-radius: 14px;
    margin: 8px 0;
    color: white;
    max-width: 80%;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "token" not in st.session_state:
    st.session_state.token = None

if "projects" not in st.session_state:
    st.session_state.projects = load_store()

if "current_project" not in st.session_state:
    st.session_state.current_project = None

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

# ---------------- AUTH ----------------
def login_user(username, password):
    res = requests.post(
        f"{API_BASE}/auth/login",
        json={"username": username, "password": password}
    )
    if res.status_code == 200:
        st.session_state.token = res.json()["access_token"]
        return True
    return False

def signup_user(username, password):
    res = requests.post(
        f"{API_BASE}/auth/register",
        json={"username": username, "password": password}
    )
    return res.status_code == 200

# ---------------- LOGIN ----------------
if not st.session_state.token:
    st.title("🔐 RAG Chatbot")

    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        u = st.text_input("Email")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            if login_user(u, p):
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        nu = st.text_input("New Email")
        np = st.text_input("New Password", type="password")
        if st.button("Signup"):
            if signup_user(nu, np):
                st.success("Signup successful. Please login.")
            else:
                st.error("User already exists")

    st.stop()

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("## 🚀 Projects")

    if st.button("➕ New Project"):
        name = f"Project {len(st.session_state.projects)+1}"
        st.session_state.projects[name] = {}
        st.session_state.current_project = name
        st.session_state.current_chat = None
        save_store(st.session_state.projects)
        st.rerun()

    for project in st.session_state.projects:
        if st.button(project, key=f"proj-{project}"):
            st.session_state.current_project = project
            st.session_state.current_chat = None
            st.rerun()

    if st.session_state.current_project:
        st.markdown("---")
        st.markdown("## 💬 Chats")

        chats = st.session_state.projects[st.session_state.current_project]

        if st.button("➕ New Chat"):
            chat_id = f"Chat {len(chats)+1}"
            chats[chat_id] = {"messages": [], "history": []}
            st.session_state.current_chat = chat_id
            save_store(st.session_state.projects)
            st.rerun()

        for chat_id, chat in chats.items():
            title = chat["messages"][0]["content"][:30] if chat["messages"] else chat_id
            if st.button(title, key=f"chat-{chat_id}"):
                st.session_state.current_chat = chat_id
                st.rerun()

    st.markdown("---")
    if st.button("Logout"):
        st.session_state.token = None
        st.rerun()

# ---------------- MAIN CHAT ----------------
st.title("🤖 RAG Chatbot")

if not st.session_state.current_project or not st.session_state.current_chat:
    st.info("Create a project and start a new chat.")
    st.stop()

chat = st.session_state.projects[
    st.session_state.current_project
][st.session_state.current_chat]

for msg in chat["messages"]:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-user'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bot'>{msg['content']}</div>", unsafe_allow_html=True)

query = st.chat_input("Ask anything...")

if query:
    chat["messages"].append({"role": "user", "content": query})

    res = requests.post(
        f"{API_BASE}/chat/",
        json={"query": query},
        headers={"Authorization": f"Bearer {st.session_state.token}"}
    )

    if res.status_code == 200:
        reply = res.json()["reply"]
        chat["messages"].append({"role": "assistant", "content": reply})
        chat["history"].append(f"User: {query}")
        chat["history"].append(f"Assistant: {reply}")

        save_store(st.session_state.projects)  # 🔑 THIS IS THE KEY
        st.rerun()
    else:
        st.error("Failed to get response from chatbot")
