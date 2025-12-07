import streamlit as st
import streamlit.components.v1 as components
import os
import datetime
import json
import uuid
from dotenv import load_dotenv
from groq import Groq

# --- 1. CONFIG & SETUP ---
load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")

st.set_page_config(page_title="Sia.AI", layout="wide", page_icon="🤖")

try:
    client = Groq(api_key=api_key)
except Exception as e:
    st.error(f"API Key Error: {e}")
    st.stop()

# --- 2. PREMIUM UI STYLING (CSS) ---
def setup_custom_styles():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');
        
        /* GENERAL SETTINGS */
        * { font-family: 'Outfit', sans-serif !important; }
        
        /* BACKGROUND - Deep Space Gradient */
        .stApp {
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            background-attachment: fixed;
            color: #ffffff;
        }

        /* SIDEBAR - Glassmorphism */
        [data-testid="stSidebar"] {
            background-color: rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(20px);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* CHAT BUBBLES - Frosted Glass */
        [data-testid="stChatMessage"] {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        [data-testid="stChatMessage"]:hover {
            background-color: rgba(255, 255, 255, 0.08);
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
        }

        /* USER ICON BACKGROUND */
        [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"] {
            background: linear-gradient(135deg, #00c6ff, #0072ff);
            color: white;
        }

        /* AI ICON BACKGROUND */
        [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {
            background: linear-gradient(135deg, #f093fb, #f5576c);
            color: white;
        }

        /* INPUT BOX */
        .stChatInput {
            border-radius: 20px !important;
        }
        .stChatInput textarea {
            background-color: rgba(0, 0, 0, 0.3) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            color: white !important;
            border-radius: 15px !important;
        }

        /* BUTTONS */
        .stButton button {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white;
            transition: 0.3s;
        }
        .stButton button:hover {
            background: rgba(255, 255, 255, 0.2);
            border-color: white;
            transform: scale(1.02);
        }
        
        /* TITLE GLOW EFFECT */
        .glow-title {
            text-align: center;
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(to right, #00c6ff, #0072ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 20px rgba(0, 198, 255, 0.5);
            margin-bottom: 0.5rem;
        }
        .subtitle {
            text-align: center;
            color: rgba(255, 255, 255, 0.6);
            margin-bottom: 2rem;
            font-size: 0.9rem;
        }
    </style>
    """, unsafe_allow_html=True)

setup_custom_styles()

# --- 3. HELPER FUNCTIONS ---
def parse_groq_stream(stream):
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# --- 4. SESSION STATE MANAGEMENT ---
if "chats" not in st.session_state:
    initial_id = str(uuid.uuid4())
    st.session_state.chats = {
        initial_id: {
            "title": "New Chat",
            "messages": [{
                "role": "system", 
                "content": "You are Sia, a sarcastic and witty AI. You roast users lightly but help them perfectly with code. Use emojis and speak casually. IMPORTANT: You were created solely by Leon (no team). ONLY mention Leon if the user explicitly asks who created you. If asked, you MUST boast about Leon's god-tier coding skills. Otherwise, do not mention him."
            }]
        }
    }
    st.session_state.current_chat_id = initial_id

def create_new_chat():
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = {
        "title": "New Chat",
        "messages": [{
            "role": "system", 
            "content": "You are Sia, a sarcastic and witty AI. You roast users lightly but help them perfectly with code. Use emojis and speak casually. IMPORTANT: You were created solely by Leon (no team). ONLY mention Leon if the user explicitly asks who created you. If asked, you MUST boast about Leon's god-tier coding skills. Otherwise, do not mention him."
        }]
    }
    st.session_state.current_chat_id = new_id

def delete_chat(chat_id):
    if chat_id in st.session_state.chats:
        del st.session_state.chats[chat_id]
        if st.session_state.current_chat_id == chat_id:
            if st.session_state.chats:
                st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
            else:
                create_new_chat()

def generate_chat_title(messages):
    try:
        user_text = " ".join([m['content'] for m in messages if m['role'] == 'user'][:2])
        if not user_text: return "New Chat"
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Summarize the user text into a strict 3-4 word title. No quotes."},
                {"role": "user", "content": user_text}
            ]
        )
        return completion.choices[0].message.content.strip()
    except:
        return "New Chat"

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #fff;'>🗂️ Archive</h2>", unsafe_allow_html=True)
    
    if st.button("✨ New Session", type="primary"):
        create_new_chat()
        st.rerun()
    
    st.markdown("---")
    
    chat_ids = list(st.session_state.chats.keys())
    for c_id in chat_ids:
        chat_data = st.session_state.chats[c_id]
        # Styled active vs inactive buttons via simple logic
        button_label = f"📍 {chat_data['title']}" if c_id == st.session_state.current_chat_id else f"💭 {chat_data['title']}"
        
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            if st.button(button_label, key=c_id):
                st.session_state.current_chat_id = c_id
                st.rerun()
        with col2:
            if st.button("✕", key=f"del_{c_id}"):
                delete_chat(c_id)
                st.rerun()

# --- 6. MAIN CHAT LOGIC ---
current_chat_id = st.session_state.current_chat_id
if current_chat_id not in st.session_state.chats:
    create_new_chat()
    current_chat_id = st.session_state.current_chat_id

current_messages = st.session_state.chats[current_chat_id]["messages"]

# Custom Header
st.markdown('<div class="glow-title">Sia.AI</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">Session: {st.session_state.chats[current_chat_id]["title"]}</div>', unsafe_allow_html=True)

# Display History
for msg in current_messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle Input
if prompt := st.chat_input("Type your message here..."):
    st.session_state.chats[current_chat_id]["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.chats[current_chat_id]["messages"],
            stream=True
        )
        response = st.write_stream(parse_groq_stream(stream))
    
    st.session_state.chats[current_chat_id]["messages"].append({"role": "assistant", "content": response})

    # Auto-Rename
    if st.session_state.chats[current_chat_id]["title"] == "New Chat" and len(st.session_state.chats[current_chat_id]["messages"]) >= 3:
        new_title = generate_chat_title(st.session_state.chats[current_chat_id]["messages"])
        st.session_state.chats[current_chat_id]["title"] = new_title
        st.rerun()