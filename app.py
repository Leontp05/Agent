import streamlit as st
import streamlit.components.v1 as components
import os
import datetime
import json
from dotenv import load_dotenv
from groq import Groq

# 1. Config and Setup
load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

st.set_page_config(page_title="Sia.AI", page_icon="✨")

# 2. Define Custom Styles (Galaxy Theme 🌌)
def setup_custom_styles():
    st.markdown("""
    <style>
        .stApp { background-color: #0b1021; color: #FFFFFF; }
        [data-testid="stChatMessage"] {
            background-color: #2b1b3d;
            background-image: 
                radial-gradient(rgba(255,255,255,0.2) 1px, transparent 1px), 
                radial-gradient(rgba(255,255,255,0.2) 1px, transparent 1px);
            background-position: 0 0, 25px 25px;
            background-size: 50px 50px;
            border: 1px solid #3e2a52; border-radius: 15px;
        }
        .stChatInput { border-color: #1a1025 !important; background-color: #1a1025 !important; }
        .stChatInput textarea { background-color: #1a1025 !important; color: #FFFFFF !important; }
        [data-testid="stChatInputSubmitButton"] { background-color: #1a1025 !important; color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)

setup_custom_styles()

st.title("✨ Sia.AI")
st.caption("Your witty, code-savvy AI companion.")

# 3. Define the Tools
def get_current_time():
    now = datetime.datetime.now()
    return json.dumps({"current_time": now.strftime("%Y-%m-%d %H:%M:%S")})

available_functions = { "get_current_time": get_current_time }

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current real-world time",
            "parameters": { "type": "object", "properties": {}, "required": [] },
        },
    }
]

# 4. Helper Functions
def parse_groq_stream(stream):
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

def scroll_to_bottom():
    js = """
    <script>
        var textArea = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
        if (textArea) { textArea.scrollIntoView({behavior: "smooth", block: "end", inline: "nearest"}); }
    </script>
    """
    components.html(js, height=0)

# 5. Memory Initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "You are Sia.AI, a witty and casual AI. You crack jokes but write serious, clean code when asked."
        }
    ]

# 6. Display History (With Feedback & Retry Buttons)
for index, message in enumerate(st.session_state.messages[1:]):
    # Determine the actual index in the full list (offset by 1 due to system prompt)
    real_index = index + 1
    
    with st.chat_message(message["role"]):
        if message.get("content"):
            st.markdown(message["content"])
            
            # --- Add Buttons Only for AI Messages ---
            if message["role"] == "assistant":
                col1, col2 = st.columns([0.15, 0.85])
                
                with col1:
                    # Like/Dislike Feedback
                    st.feedback("thumbs", key=f"feedback_{real_index}")
                
                with col2:
                    # Retry Button 🔄
                    if st.button("🔄 Retry", key=f"retry_{real_index}"):
                        # Delete this AI message
                        st.session_state.messages.pop(real_index)
                        # Rerun immediately - this will trigger the logic below!
                        st.rerun()

# 7. Handle New Input
if prompt := st.chat_input("Chat with Sia..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun() # Force a rerun to update the display immediately

# 8. The "Brain" Logic (Runs if the last message is from the User)
# This checks: "Did we just get a user message? Or did we just delete an AI message?"
last_message = st.session_state.messages[-1]

if last_message["role"] == "user":
    
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.7,
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            # 1. Log tool call
            st.session_state.messages.append({
                "role": response_message.role,
                "tool_calls": tool_calls,
                "content": response_message.content
            })
            
            # 2. Run tools
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_response = function_to_call()
                
                st.session_state.messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })
            
            # 3. Final Answer
            stream = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages,
                stream=True
            )
            final_response = st.write_stream(parse_groq_stream(stream))
            st.session_state.messages.append({"role": "assistant", "content": final_response})
            
        else:
            # Normal text response
            st.markdown(response_message.content)
            st.session_state.messages.append({"role": "assistant", "content": response_message.content})
            
    scroll_to_bottom()
    st.rerun() # One final rerun to show the feedback buttons on the new message