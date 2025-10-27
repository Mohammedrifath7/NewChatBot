import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
# -------------------- Load environment and initialize Groq --------------------
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize Groq client
client = Groq(api_key=groq_api_key)

# -------------------- Initialize Firebase --------------------

#firebase_key = json.loads(st.secrets["FIREBASE_KEY"])

# Initialize Firebase (only once)
if not firebase_admin._apps:
    cred = credentials.Certificate(st.secrets["FIREBASE_KEY"])
    firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()
# -------------------- Streamlit UI Setup --------------------
st.set_page_config(page_title="Groq Chatbot", page_icon="💬", layout="centered")

# Custom chat CSS
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

# -------------------- Chat session state --------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "system",
        "content": (
            "You are a friendly, helpful, and polite chatbot. "
            
        )
    }]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -------------------- Display chat history --------------------
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-container"><div class="chat-message user-message">🧑‍💻 {msg["content"]}</div></div>', unsafe_allow_html=True)
    elif msg["role"] == "assistant":
        st.markdown(f'<div class="chat-container"><div class="chat-message bot-message">💃 {msg["content"]}</div></div>', unsafe_allow_html=True)

# -------------------- Chat input --------------------
user_input = st.chat_input("Type your message...")

if user_input:
    # Append user message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Display user message
    st.markdown(f'<div class="chat-container"><div class="chat-message user-message">🧑‍💻 {user_input}</div></div>', unsafe_allow_html=True)

    # Typing placeholder
    typing_placeholder = st.empty()
    typing_placeholder.markdown(
        '<div class="chat-container"><div class="chat-message bot-message">💃 Typing...</div></div>',
        unsafe_allow_html=True
    )

    # -------------------- Get Groq response --------------------
    response = client.chat.completions.create(
        messages=st.session_state.messages,
        model="llama-3.3-70b-versatile"
    )
    reply = response.choices[0].message.content

    # Update placeholder with actual reply
    typing_placeholder.markdown(
        f'<div class="chat-container"><div class="chat-message bot-message">💃 {reply}</div></div>',
        unsafe_allow_html=True
    )

    # Save to session
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

    # -------------------- Save chat to Firestore --------------------
    db.collection("chats").add({
        "user": user_input,
        "bot": reply,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
