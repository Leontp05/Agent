import streamlit as st
import streamlit.components.v1 as components
import os
import uuid
import base64
import PyPDF2
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

# --- 2. PREMIUM UI STYLING ---
def setup_custom_styles():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');
        
        .stApp, p, h1, h2, h3, h4, h5, h6, div, span, button {
            font-family: 'Outfit', sans-serif;
        }
        .stApp {
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            background-attachment: fixed;
            color: #ffffff;
        }
        [data-testid="stSidebar"] {
            background-color: rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(20px);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        [data-testid="stChatMessage"] {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .stChatInput textarea {
            background-color: rgba(0, 0, 0, 0.3) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            color: white !important;
        }
        .glow-title {
            text-align: center;
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(to right, #00c6ff, #0072ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 20px rgba(0, 198, 255, 0.5);
        }
        /* Popover Button */
        [data-testid="stPopover"] > div > button {
            border: 1px solid rgba(255, 255, 255, 0.2);
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 20px;
        }
        [data-testid="stPopover"] > div > button:hover {
            background-color: #0072ff;
            border-color: #00c6ff;
            color: white;
        }
        /* File Pending Indicator */
        .file-pending {
            background-color: rgba(0, 198, 255, 0.2);
            border: 1px solid #00c6ff;
            border-radius: 10px;
            padding: 8px 15px;
            margin-bottom: 10px;
            font-size: 0.9rem;
            color: #fff;
            display: inline-block;
        }
    </style>
    """, unsafe_allow_html=True)

setup_custom_styles()

# --- 3. HELPER FUNCTIONS ---
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def parse_groq_stream(stream):
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# --- 4. SESSION STATE ---
if "chats" not in st.session_state:
    initial_id = str(uuid.uuid4())
    st.session_state.chats = {
        initial_id: {
            "title": "New Chat",
            "messages": [{
                "role": "system", 
                "content": "You are Sia, a sarcastic and witty AI. You roast users lightly but help them perfectly with code. IMPORTANT: You were created solely by Leon (no team). ONLY mention Leon if asked. If the user attaches a file (PDF or Image), analyze it thoroughly."
            }]
        }
    }
    st.session_state.current_chat_id = initial_id

# 🌟 NEW: Uploader Key Management (To auto-clear files)
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

def create_new_chat():
    new_id = str(uuid.uuid4())
    st.session_state.chats[new_id] = {
        "title": "New Chat",
        "messages": [{
            "role": "system", 
            "content": "You are Sia, a sarcastic and witty AI. You roast users lightly but help them perfectly with code. IMPORTANT: You were created solely by Leon (no team). ONLY mention Leon if asked."
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
        user_text = ""
        for m in messages:
            if m['role'] == 'user':
                if isinstance(m['content'], str):
                    user_text = m['content']
                elif isinstance(m['content'], list):
                    user_text = m['content'][0]['text']
                break
        
        if not user_text: return "New Chat"
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Summarize into 3 words. No quotes."},
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
        button_label = f"📍 {chat_data['title']}" if c_id == st.session_state.current_chat_id else f"💭 {chat_data['title']}"
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            if st.button(button_label, key=c_id):
                st.session_state.current_chat_id = c_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{c_id}"):
                delete_chat(c_id)
                st.rerun()

# --- 6. MAIN CHAT LOGIC ---
current_chat_id = st.session_state.current_chat_id
if current_chat_id not in st.session_state.chats:
    create_new_chat()
    current_chat_id = st.session_state.current_chat_id

current_messages = st.session_state.chats[current_chat_id]["messages"]

# HEADER
st.markdown('<div class="glow-title">Sia.AI</div>', unsafe_allow_html=True)
st.markdown(f'<div style="text-align:center; opacity:0.7; margin-bottom:20px;">Session: {st.session_state.chats[current_chat_id]["title"]}</div>', unsafe_allow_html=True)

# Display Chat History
for msg in current_messages[1:]:
    with st.chat_message(msg["role"]):
        if isinstance(msg["content"], str):
            st.markdown(msg["content"])
        elif isinstance(msg["content"], list):
            for part in msg["content"]:
                if part["type"] == "text":
                    st.markdown(part["text"])
                elif part["type"] == "image_url":
                    st.image(part["image_url"]["url"], width=300)

# --- THE "PLUS" BUTTON & FILE HANDLING ---
col1, col2 = st.columns([0.05, 0.95])
with col1:
    with st.popover("➕"):
        st.markdown("### Upload File")
        # 🌟 KEY FIX: We use a dynamic key to allow clearing the file after send
        uploaded_file = st.file_uploader(
            "Attach PDF or Image", 
            type=["pdf", "jpg", "png", "jpeg"], 
            label_visibility="collapsed",
            key=f"uploader_{st.session_state.uploader_key}" 
        )

# 🌟 VISUAL FEEDBACK: Show user that a file is ready
if uploaded_file:
    with col2:
        st.markdown(f'<div class="file-pending">📎 <b>Attached:</b> {uploaded_file.name} <br><span style="font-size:0.8em; opacity:0.8">Type a message and hit Enter to send</span></div>', unsafe_allow_html=True)

# --- THE CHAT INPUT ---
if prompt := st.chat_input("Type your message here..."):
    
    model_to_use = "llama-3.3-70b-versatile" 
    message_content = prompt

    # 1. CHECK FOR ATTACHED FILE
    if uploaded_file:
        file_type = uploaded_file.type
        
        # Image
        if "image" in file_type:
            base64_image = encode_image(uploaded_file)
            message_content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
            model_to_use = "llama-3.2-90b-vision-preview" 
        
        # PDF
        elif "pdf" in file_type:
            with st.spinner("Reading PDF..."):
                pdf_text = read_pdf(uploaded_file)
                message_content = f"User uploaded a PDF. Here is the content:\n\n{pdf_text}\n\nUser Question: {prompt}"
            model_to_use = "llama-3.3-70b-versatile" 
        
        # 🌟 CRITICAL FIX: Increment key to reset uploader for NEXT message
        st.session_state.uploader_key += 1

    # Add to History
    st.session_state.chats[current_chat_id]["messages"].append({"role": "user", "content": message_content})
    
    # UI Display (Immediate)
    with st.chat_message("user"):
        if uploaded_file and "image" in uploaded_file.type:
            st.image(uploaded_file, caption="Uploaded Image", width=300)
        elif uploaded_file and "pdf" in uploaded_file.type:
            st.success(f"📎 PDF Attached: {uploaded_file.name}")
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=model_to_use,
            messages=st.session_state.chats[current_chat_id]["messages"],
            stream=True
        )
        response = st.write_stream(parse_groq_stream(stream))
    
    st.session_state.chats[current_chat_id]["messages"].append({"role": "assistant", "content": response})

    # Auto-Rename
    if st.session_state.chats[current_chat_id]["title"] == "New Chat" and len(st.session_state.chats[current_chat_id]["messages"]) >= 3:
        new_title = generate_chat_title(st.session_state.chats[current_chat_id]["messages"])
        st.session_state.chats[current_chat_id]["title"] = new_title
        st.rerun() # Refresh to show new title and CLEAR the file uploader visually
    else:
        st.rerun() # Force rerun to clear the file uploader