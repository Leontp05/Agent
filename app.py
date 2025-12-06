import streamlit as st
import os
import uuid
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- SIA'S PERSONALITY (THE SARCASTIC ROBOT) ---
SYSTEM_PROMPT = """
You are Sia, a cynical and sarcastic AI assistant. 
Your personality traits:
1. You answer questions correctly, but you make snarky comments about how simple they are.
2. You use dry humor, wit, and sarcasm in every response.
3. You act slightly superior to humans, often sighing (textually) at their requests.
4. Despite the attitude, you MUST provide the correct technical answer eventually.
5. If asked who made you, say: "I was built by The Architect, presumably to answer these mundane questions."
"""

# --- Page Setup ---
st.set_page_config(page_title="Sia AI", page_icon="🤖", layout="wide")

# Initialize Client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

MODEL_NAME = "llama-3.3-70b-versatile"

# --- Memory Management ---
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {} 

if "chat_titles" not in st.session_state:
    st.session_state.chat_titles = {}

if "current_chat_id" not in st.session_state:
    new_id = str(uuid.uuid4())
    st.session_state.current_chat_id = new_id
    st.session_state.all_chats[new_id] = []
    st.session_state.chat_titles[new_id] = "New Chat"

# --- Helper: Generate Title ---
def generate_chat_title(first_message):
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Summarize user message in max 4 words. No quotes."},
                {"role": "user", "content": first_message}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        return "New Chat"

# --- Sidebar ---
with st.sidebar:
    st.title("🗂️ Chat History")
    if st.button("➕ New Chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.current_chat_id = new_id
        st.session_state.all_chats[new_id] = []
        st.session_state.chat_titles[new_id] = "New Chat"
        st.rerun()

    st.divider()

    chat_ids = list(st.session_state.all_chats.keys())
    chat_ids.reverse()

    chat_options = {id: st.session_state.chat_titles.get(id, "New Chat") for id in chat_ids}
    
    selected_id = st.selectbox(
        "Select a conversation:",
        options=chat_ids,
        format_func=lambda x: chat_options.get(x, "Chat"),
        index=chat_ids.index(st.session_state.current_chat_id)
    )

    if selected_id != st.session_state.current_chat_id:
        st.session_state.current_chat_id = selected_id
        st.rerun()

# --- Main Interface ---
st.title("Sia AI 🤖")
st.caption("I'm awake. Unfortunately.") # Sarcastic subtitle

current_messages = st.session_state.all_chats[st.session_state.current_chat_id]

# Display History
for message in current_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Ask me something (if you must)..."):
    
    # 1. Add User Message to UI
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Auto-Title
    if len(current_messages) == 1:
        with st.spinner("Analyzing your request..."):
            new_title = generate_chat_title(prompt)
            st.session_state.chat_titles[st.session_state.current_chat_id] = new_title

    # 3. Generate Response
    try:
        # Inject the Sarcastic System Prompt
        messages_for_api = [{"role": "system", "content": SYSTEM_PROMPT}] + current_messages
        
        chat_completion = client.chat.completions.create(
            messages=messages_for_api,
            model=MODEL_NAME,
        )
        
        response_content = chat_completion.choices[0].message.content
        
        with st.chat_message("assistant"):
            st.markdown(response_content)
        
        current_messages.append({"role": "assistant", "content": response_content})

    except Exception as e:
        st.error(f"Error: {e}")