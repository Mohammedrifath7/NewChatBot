import streamlit as st
from groq import Groq
import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv 

# -------------------- LOAD .env VARIABLES --------------------
load_dotenv()  # 👈 ADD THIS

mongo_uri = os.getenv("MONGO_URI")

# -------------------- MONGODB CONNECTION --------------------
try:
    client_mongo = MongoClient(mongo_uri)
    db = client_mongo["chatbot_db"]
    chats_collection = db["chats"]
    print("✅ Connected to MongoDB Atlas successfully!")
except Exception as e:
    st.error(f"⚠️ MongoDB Atlas connection failed: {e}")
# -------------------- GROQ SETUP --------------------
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    st.error("⚠️ GROQ_API_KEY not found in environment variables!")
else:
    client = Groq(api_key=groq_api_key)
    client = Groq(api_key=groq_api_key)

# -------------------- STREAMLIT UI --------------------
st.set_page_config(page_title="Groq Chatbot", page_icon="💬", layout="centered")

# Custom Chat Styling
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

st.title("💬 Local Chatbot (Groq + MongoDB)")
st.caption("Model: LLaMA3-70B | Data stored locally in MongoDB Compass")

# -------------------- SESSION STATE --------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful, polite chatbot."}]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -------------------- DISPLAY CHAT HISTORY --------------------
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(
            f'<div class="chat-container"><div class="chat-message user-message">🧑‍💻 {msg["content"]}</div></div>',
            unsafe_allow_html=True
        )
    elif msg["role"] == "assistant":
        st.markdown(
            f'<div class="chat-container"><div class="chat-message bot-message">💃 {msg["content"]}</div></div>',
            unsafe_allow_html=True
        )

# -------------------- USER INPUT --------------------
user_input = st.chat_input("Type your message...")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Display user message
    st.markdown(
        f'<div class="chat-container"><div class="chat-message user-message">🧑‍💻 {user_input}</div></div>',
        unsafe_allow_html=True
    )

    # Placeholder for bot typing
    typing_placeholder = st.empty()
    typing_placeholder.markdown(
        '<div class="chat-container"><div class="chat-message bot-message">💃 Typing...</div></div>',
        unsafe_allow_html=True
    )

    # -------------------- GROQ RESPONSE --------------------
    try:
        response = client.chat.completions.create(
            messages=st.session_state.messages,
            model="llama-3.3-70b-versatile"
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"⚠️ Groq error: {e}"

    # Replace placeholder with bot reply
    typing_placeholder.markdown(
        f'<div class="chat-container"><div class="chat-message bot-message">💃 {reply}</div></div>',
        unsafe_allow_html=True
    )

    # Save assistant message
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.chat_history.append({"role": "assistant", "content": reply})

    # -------------------- SAVE CHAT TO MONGODB --------------------
    try:
        chats_collection.insert_one({
            "user": user_input,
            "bot": reply,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        st.warning(f"⚠️ Failed to save to MongoDB: {e}")
