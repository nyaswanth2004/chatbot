import streamlit as st

# ✅ MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide"
)

# =========================
# IMPORTS
# =========================
from auth import (
    create_user, login_user,
    save_chat, load_chats
)
from utils import (
    chat_with_llm,
    generate_image,
    summarize_youtube,
    summarize_pdf
)

# =========================
# SESSION STATE
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

if "image_messages" not in st.session_state:
    st.session_state.image_messages = []

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

if "chat_title" not in st.session_state:
    st.session_state.chat_title = "New Chat"

# =========================
# AUTHENTICATION
# =========================
if not st.session_state.logged_in:
    st.title("🔐 AI Chatbot Login")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username

                # Initialize fresh chat
                st.session_state.messages = [
                    {
                        "role": "system",
                        "content": "You are a helpful, friendly AI assistant."
                    }
                ]
                st.session_state.chat_id = None
                st.session_state.chat_title = "My Chatbot"

                st.success("Login successful 🎉")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Sign Up"):
            if create_user(new_user, new_pass):
                st.success("Account created! Please login")
            else:
                st.error("Username already exists")

    st.stop()

# =========================
# SIDEBAR
# =========================
st.sidebar.write(f"👤 {st.session_state.username}")

if st.sidebar.button("➕ New Chat"):
    st.session_state.chat_id = None
    st.session_state.chat_title = "New Chat"
    st.session_state.messages = [
        {
            "role": "system",
            "content": "You are a helpful, friendly AI assistant."
        }
    ]
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("💬 Chat History")

user_chats = load_chats(st.session_state.username, grouped=True) or {}

for chat_id, chat in user_chats.items():
    if st.sidebar.button(chat["title"], key=chat_id):
        st.session_state.chat_id = chat_id
        st.session_state.chat_title = chat["title"]
        st.session_state.messages = chat["messages"]
        st.rerun()

st.sidebar.divider()

tool = st.sidebar.radio(
    "🛠 Tools:",
    ["Chat", "YouTube Summary", "PDF Summary", "Image Generation"]
)

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# =========================
# TITLE
# =========================
st.title(f"🤖 {st.session_state.chat_title}")

# =========================
# CHAT TOOL
# =========================
if tool == "Chat":

    # Show chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask anything...")

    if prompt:
        # User message
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )

        st.session_state.chat_id = save_chat(
            st.session_state.username,
            st.session_state.chat_id,
            "user",
            prompt
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        # Assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chat_with_llm(st.session_state.messages)
                st.markdown(response)

        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )

        st.session_state.chat_id = save_chat(
            st.session_state.username,
            st.session_state.chat_id,
            "assistant",
            response
        )

# =========================
# YOUTUBE SUMMARY
# =========================
elif tool == "YouTube Summary":
    yt_url = st.text_input("Paste YouTube URL")

    if yt_url:
        with st.spinner("Summarizing video..."):
            summary = summarize_youtube(yt_url)
            st.markdown(summary)

# =========================
# PDF SUMMARY
# =========================
elif tool == "PDF Summary":
    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_pdf:
        with st.spinner("Reading PDF..."):
            summary = summarize_pdf(uploaded_pdf)
            st.markdown(summary)

# =========================
# IMAGE GENERATION
# =========================
elif tool == "Image Generation":

    for msg in st.session_state.image_messages:
        with st.chat_message(msg["role"]):
            if msg["type"] == "text":
                st.markdown(msg["content"])
            else:
                st.image(msg["content"])

    img_prompt = st.chat_input("Describe the image...")

    if img_prompt:
        st.session_state.image_messages.append({
            "role": "user",
            "type": "text",
            "content": img_prompt
        })

        with st.chat_message("user"):
            st.markdown(img_prompt)

        with st.chat_message("assistant"):
            with st.spinner("Generating image..."):
                img_path = generate_image(img_prompt)
                st.image(img_path)

        st.session_state.image_messages.append({
            "role": "assistant",
            "type": "image",
            "content": img_path
        })
