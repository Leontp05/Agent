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
# Try to get key from Cloud Secrets first, then local .env
api_key = os.environ.get("GROQ_API_KEY")

# Streamlit Config
st.set_page_config(page_title="Sia.AI", layout="wide")

# Initialize Client
try:
    client = Groq(api_key=api_key)
except Exception as e:
    st.error(f"API Key Error: {e}")
    st.stop()

# --- 2. CUSTOM STYLES ---
def setup_custom_styles():
    st.markdown("""
    <style>
        .stApp { background-color: #0b1021; color: #FFFFFF; }
        [data-testid="stSidebar"] { background-color: #1a1025; border-right: 1px solid #3e2a52; }
        [data-testid="stChatMessage"] {
            background-color: #2b1b3d;
            border: 1px solid #3e2a52;
            border-radius: 15px;
        }
        .stButton button { width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

setup_custom_styles()

# --- 3. SESSION STATE MANAGEMENT ( The Brain for History) ---
if "chats" not in st.session_state:
    # Initialize with one empty chat
    initial_id = str(uuid.uuid4())
    st.session_state.chats = {
        initial_id: {
            "title": "New Chat",
            "messages": [{"role": "system", "content": "You are Sia, a witty AI agent."}]
        }
    }
    st.session_state.current_chat_id = initial_id

def create_new_chat():
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = {
        "title": "New Chat",
        "messages": [{"role": "system", "content": "You are Sia, a witty AI agent."}]
    }
    st.session_state.current_chat_id = new_id

def delete_chat(chat_id):
    if chat_id in st.session_state.chats:
        del st.session_state.chats[chat_id]
        # If we deleted the current chat, switch to another one or create new
        if st.session_state.current_chat_id == chat_id:
            if st.session_state.chats:
                st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
            else:
                create_new_chat()

def generate_chat_title(messages):
    """Ask Groq to summarize the chat into a 3-4 word title"""
    try:
        # We look at the first few user messages to guess the topic
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

# --- 4. SIDEBAR (History & Controls) ---
with st.sidebar:
    st.title("🗂️ History")
    
    if st.button("➕ New Chat", type="primary"):
        create_new_chat()
        st.rerun()
    
    st.markdown("---")
    
    # List all chats (Newest on top logic could be added)
    chat_ids = list(st.session_state.chats.keys())
    
    for c_id in chat_ids:
        chat_data = st.session_state.chats[c_id]
        
        # Determine if this button is "active"
        button_type = "secondary" if c_id != st.session_state.current_chat_id else "primary"
        
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button(chat_data["title"], key=c_id, type=button_type):
                st.session_state.current_chat_id = c_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{c_id}"):
                delete_chat(c_id)
                st.rerun()

# --- 5. MAIN CHAT LOGIC ---

# Get current chat data
current_chat_id = st.session_state.current_chat_id
# Safety check
if current_chat_id not in st.session_state.chats:
    create_new_chat()
    current_chat_id = st.session_state.current_chat_id

current_messages = st.session_state.chats[current_chat_id]["messages"]

# Title
st.title("Sia.AI")
st.caption(f"Current Session: {st.session_state.chats[current_chat_id]['title']}")

# Display Messages
for msg in current_messages[1:]: # Skip system prompt
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle Input
if prompt := st.chat_input("Ask Sia..."):
    # 1. Add User Message
    st.session_state.chats[current_chat_id]["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate Response
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.chats[current_chat_id]["messages"],
            stream=True
        )
        response = st.write_stream(stream)
    
    # 3. Add Assistant Message
    st.session_state.chats[current_chat_id]["messages"].append({"role": "assistant", "content": response})

    # 4. Auto-Rename Chat (If it's the first exchange)
    # Check if title is still default and we have enough messages
    if st.session_state.chats[current_chat_id]["title"] == "New Chat" and len(st.session_state.chats[current_chat_id]["messages"]) >= 3:
        new_title = generate_chat_title(st.session_state.chats[current_chat_id]["messages"])
        st.session_state.chats[current_chat_id]["title"] = new_title
        st.rerun() # Refresh to show new title in sidebar