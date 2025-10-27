import streamlit as st
from groq import Groq
import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json

# -------------------- READ ENV VARIABLES (for Render) --------------------

# Get API key from Render Environment
groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    st.error("⚠️ GROQ_API_KEY not found in environment variables!")

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# Get Firebase credentials from Render Environment
firebase_key_str = os.environ.get("FIREBASE_KEY")
if not firebase_key_str:
    st.error("⚠️ FIREBASE_KEY not found in environment variables!")
else:
    # Parse JSON string (Render stores as single-line env var)
    firebase_key = json.loads(firebase_key_str)

    # Replace literal '\n' with real newlines in private_key
    if "private_key" in firebase_key:
        firebase_key["private_key"] = firebase_key["private_key"].replace("\\n", "\n")

    # Initialize Firebase once
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_key)
        firebase_admin.initialize_app(cred)

    # Firestore client
    db = firestore.client()

# -------------------- STREAMLIT UI SETUP --------------------

st.set_page_config(page_title="Groq Chatbot", page_icon="💬", layout="centered")

# Custom CSS for better chat look
st.markdown("""
    <style>
    .chat-message {
        padding: 10px 15px;
        border-radius: 12px;
        margin: 8px 0;
        max-width: 70%;
        font-size: 16px;
        line-height: 1.4;
        display: inline-block;
        word-wrap: break-word;
    }
    .user-message {
        background-color: #DCF8C6;
        color: black;
        margin-left: auto;
        text-align: right;
    }
    .bot-message {
        background-color: #F1F0F0;
        color: black;
        margin-right: auto;
        text-align: left;
    }
    .chat-container {
        display: flex;
        flex-direction: column;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💬 Chatting System")
st.caption("Made with Groq | Model: LLaMA3-70B")

# -------------------- SESSION STATE --------------------

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "system",
        "content": "You are a friendly, helpful, and polite chatbot."
    }]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -------------------- DISPLAY CHAT HISTORY --------------------

for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-container"><div class="chat-message user-message">🧑‍💻 {msg["content"]}</div></div>', unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f'<div class="chat-container"><div class="chat-message bot-message">💃 {msg["content"]}</div></div>', unsafe_allow_html=True)

# -------------------- USER INPUT --------------------

user_input = st.chat_input("Type your message...")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Show user message
    st.markdown(f'<div class="chat-container"><div class="chat-message user-message">🧑‍💻 {user_input}</div></div>', unsafe_allow_html=True)

    # Placeholder for bot typing
    typing_placeholder = st.empty()
    typing_placeholder.markdown(
        '<div class="chat-container"><div class="chat-message bot-message">💃 Typing...</div></div>',
        unsafe_allow_html=True
    )

    # -------------------- GROQ RESPONSE --------------------
    response = client.chat.completions.create(
        messages=st.session_state.messages,
        model="llama-3.3-70b-versatile"
    )

    reply = response.choices[0].message.content

    # Replace placeholder with actual reply
    typing_placeholder.markdown(
        f'<div class="chat-container"><div class="chat-message bot-message">💃 {reply}</div></div>',
        unsafe_allow_html=True
    )

    # Save assistant message
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

    # -------------------- SAVE TO FIRESTORE --------------------
    try:
        db.collection("chats").add({
            "user": user_input,
            "bot": reply,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        st.warning(f"⚠️ Failed to save to Firestore: {e}")
