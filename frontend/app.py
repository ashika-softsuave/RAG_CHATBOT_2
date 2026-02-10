import streamlit as st
import requests
import json
import os

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="SoftSuave RAG Chatbot",
    page_icon="🤖",
    layout="wide"
)

# ================= PERSISTENCE =================
STORE_FILE = "chat_store.json"

def load_store():
    if os.path.exists(STORE_FILE):
        with open(STORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_store(data):
    with open(STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ================= STYLE =================
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

# ================= SESSION STATE =================
if "token" not in st.session_state:
    st.session_state.token = None

if "projects" not in st.session_state:
    st.session_state.projects = load_store()

if "current_project" not in st.session_state:
    st.session_state.current_project = None

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

if "awaiting_followup" not in st.session_state:
    st.session_state.awaiting_followup = False

# ================= AUTH =================
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

# ================= LOGIN PAGE =================
if not st.session_state.token:
    st.title("🔐 SoftSuave RAG Chatbot")

    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login_user(email, password):
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_email = st.text_input("New Email")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Signup"):
            if signup_user(new_email, new_pass):
                st.success("Signup successful. Please login.")
            else:
                st.error("User already exists")

    st.stop()

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## 🚀 Projects")

    if st.button("➕ New Project"):
        name = f"Project {len(st.session_state.projects) + 1}"
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
            chat_id = f"Chat {len(chats) + 1}"
            chats[chat_id] = {
                "messages": [],
                "history": []
            }
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
        st.session_state.awaiting_followup = False
        st.rerun()

# ================= MAIN CHAT =================
st.title("🤖 SoftSuave AI Assistant")

if not st.session_state.current_project or not st.session_state.current_chat:
    st.info("Create a project and start a new chat.")
    st.stop()

chat = st.session_state.projects[
    st.session_state.current_project
][st.session_state.current_chat]

# Display messages
for msg in chat["messages"]:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-user'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bot'>{msg['content']}</div>", unsafe_allow_html=True)

# ================= CHAT INPUT =================
query = st.chat_input("Ask anything related to SoftSuave documents...")

if query:
    # Show user message immediately
    chat["messages"].append({"role": "user", "content": query})

    payload = {
        "query": query,
        "history": chat["history"],
        "followup_answer": query if st.session_state.awaiting_followup else None,
        "awaiting_followup": st.session_state.awaiting_followup
    }

    res = requests.post(
        f"{API_BASE}/chat/",
        json=payload,
        headers={"Authorization": f"Bearer {st.session_state.token}"}
    )

    if res.status_code == 200:
        data = res.json()

        reply = data["reply"]
        chat["messages"].append({"role": "assistant", "content": reply})

        # 🔑 follow-up state
        st.session_state.awaiting_followup = data["awaiting_followup"]

        save_store(st.session_state.projects)
        st.rerun()
    else:
        st.error("Failed to get response from chatbot")
