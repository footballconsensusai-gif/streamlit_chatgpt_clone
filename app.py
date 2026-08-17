import os
import json
import streamlit as st
from datetime import datetime

# Try to import Google Generative AI client; if missing, app will show instructions
try:
    import google.generativeai as genai
    GENA_AVAILABLE = True
except Exception:
    GENA_AVAILABLE = False

# Data file for persistent chats
DATA_FILE = os.path.join(os.path.dirname(__file__), "chats.json")

# Utility: load / save
def load_chats():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_chats(chats):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(chats, f, indent=2, ensure_ascii=False)

# Initialize app session
st.set_page_config(page_title="Streamlit Gemini Chat", layout="wide")

if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

if "current_chat" not in st.session_state:
    # default chat
    if len(st.session_state.chats) == 0:
        st.session_state.chats = [
            {"id": 1, "title": "New Chat", "created": str(datetime.utcnow()), "messages": []}
        ]
    st.session_state.current_chat = st.session_state.chats[0]["id"]

# Helpers to work with chats
def get_chat_by_id(cid):
    for c in st.session_state.chats:
        if c["id"] == cid:
            return c
    return None

def add_chat(title="New Chat"):
    new_id = max([c["id"] for c in st.session_state.chats]) + 1 if st.session_state.chats else 1
    chat = {"id": new_id, "title": title, "created": str(datetime.utcnow()), "messages": []}
    st.session_state.chats.insert(0, chat)
    st.session_state.current_chat = new_id
    save_chats(st.session_state.chats)

def delete_chat(cid):
    st.session_state.chats = [c for c in st.session_state.chats if c["id"] != cid]
    if st.session_state.chats:
        st.session_state.current_chat = st.session_state.chats[0]["id"]
    else:
        add_chat()
    save_chats(st.session_state.chats)

# Sidebar: chat list
with st.sidebar:
    st.title("Chats")
    if st.button("+ New Chat"):
        add_chat()

    for c in st.session_state.chats:
        cols = st.columns([6,1,1])
        if cols[0].button(c["title"], key=f"select_{c['id']}"):
            st.session_state.current_chat = c["id"]
        if cols[1].button("✏️", key=f"rename_{c['id']}"):
            new_title = st.text_input("Rename chat", value=c["title"], key=f"rename_input_{c['id']}")
            if st.button("Save", key=f"rename_save_{c['id']}"):
                c["title"] = new_title
                save_chats(st.session_state.chats)
                st.rerun()
        if cols[2].button("🗑", key=f"del_{c['id']}"):
            delete_chat(c["id"])
            st.rerun()

    st.markdown("---")
    st.markdown("API & Settings")
    st.write("Provide your Google API key as an environment variable named GOOGLE_API_KEY, or set it in Streamlit secrets as 'google_api_key'.")
    st.write("Model is configurable via GEMINI_MODEL env var. If not set, the app auto-detects the latest available model.")

    st.markdown("---")
    st.caption("This is a simple local chat UI — do not store secrets in public repos.")

def get_default_model(api_key):
    """Get a currently supported Gemini model from the API."""
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        preferred = [
            "gemini-3.6-flash",
            "gemini-3.0-flash",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-pro"
        ]
        for preferred_name in preferred:
            for model in models:
                model_name = model.name.split("/")[-1]
                if model_name == preferred_name or model_name.startswith(preferred_name):
                    return model_name
        for model in models:
            model_name = model.name.split("/")[-1]
            if "gemini" in model_name.lower():
                return model_name
        return "gemini-3.6-flash"
    except Exception:
        return "gemini-3.6-flash"

def extract_gemini_text(response):
    """Support both legacy and modern google-generativeai response shapes."""
    if response is None:
        return ""

    if hasattr(response, "text") and response.text:
        return response.text

    if isinstance(response, dict):
        if response.get("text"):
            return response["text"]
        candidates = response.get("candidates")
        if candidates:
            first = candidates[0]
            if isinstance(first, dict):
                content = first.get("content", {})
                if isinstance(content, dict):
                    parts = content.get("parts", [])
                    if parts:
                        texts = []
                        for part in parts:
                            if isinstance(part, dict) and part.get("text"):
                                texts.append(part["text"])
                        if texts:
                            return "".join(texts)
                if first.get("text"):
                    return first["text"]

    if hasattr(response, "candidates"):
        for candidate in response.candidates:
            if hasattr(candidate, "content"):
                content = candidate.content
                if hasattr(content, "parts"):
                    texts = []
                    for part in content.parts:
                        if hasattr(part, "text") and part.text:
                            texts.append(part.text)
                    if texts:
                        return "".join(texts)
            if hasattr(candidate, "text") and candidate.text:
                return candidate.text

    return str(response)

# Current chat view
chat = get_chat_by_id(st.session_state.current_chat)
if chat is None:
    add_chat()
    chat = get_chat_by_id(st.session_state.current_chat)

# Main layout: messages and input
st.header("Streamlit Gemini Chat")

# Create two containers: one for messages (scrollable), one for input (fixed)
messages_container = st.container(height=500)
input_container = st.container()

with messages_container:
    for msg in chat["messages"]:
        if msg["role"] == "user":
            st.markdown(f"**You** — <span style='color:gray;font-size:12px'>{msg.get('time','')}</span>", unsafe_allow_html=True)
            st.markdown(msg["content"])  # user content
        else:
            st.markdown(f"**Assistant** — <span style='color:gray;font-size:12px'>{msg.get('time','')}</span>", unsafe_allow_html=True)
            # assistant content should be markdown already (code blocks preserved)
            st.markdown(msg["content"])
        st.markdown("---")

# Input area fixed at bottom
with input_container:
    with st.form("input_form", clear_on_submit=False):
        cols = st.columns([0.8, 4.2])
        
        with cols[0]:
            uploaded_file = st.file_uploader("Upload file", label_visibility="collapsed")
        
        with cols[1]:
            user_input = st.text_area("", key="user_input", placeholder="Ask a coding question or anything...", height=80)
        
        col1, col2, col3, col4 = st.columns([1, 1, 1, 6])
        # Use environment variable or detect from API
        if os.environ.get("GEMINI_MODEL"):
            model_hint = os.environ.get("GEMINI_MODEL")
        else:
            model_hint = "(auto-detected)"
        col4.markdown(f"**Model:** `{model_hint}`")
        submitted = col1.form_submit_button("Send")

if submitted and (user_input.strip() or uploaded_file):
    # Handle file if uploaded
    file_content = ""
    if uploaded_file:
        file_content = f"\n[File uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)]"
    
    # append user message
    display_input = user_input + file_content
    umsg = {"role": "user", "content": display_input, "time": str(datetime.utcnow())}
    chat["messages"].append(umsg)
    save_chats(st.session_state.chats)

    # Build prompt: instruct to respond in markdown with syntax-highlighted code when appropriate
    system_instructions = (
        "You are a helpful coding assistant. When the user asks for code or examples, respond in Markdown only. "
        "Include fenced code blocks with language identifiers for syntax highlighting. Keep explanations concise and show runnable examples where applicable."
    )

    # Choose whether to call Gemini (if available) or produce a fallback
    reply_md = ""
    if GENA_AVAILABLE:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key and hasattr(st, "secrets"):
            api_key = st.secrets.get("google_api_key")

        if not api_key:
            reply_md = "**Error:** GOOGLE_API_KEY not found in environment or Streamlit secrets. Set the env var and restart."
        else:
            try:
                genai.configure(api_key=api_key)
                # Use explicit model from env var, or auto-detect the latest available
                if os.environ.get("GEMINI_MODEL"):
                    model_name = os.environ.get("GEMINI_MODEL")
                else:
                    model_name = get_default_model(api_key)
                if not model_name.startswith("models/"):
                    model_name = f"models/{model_name}"
                prompt = f"{system_instructions}\n\nUser: {user_input}\nAssistant:"

                try:
                    model = genai.GenerativeModel(model_name=model_name)
                    response = model.generate_content(prompt)
                    reply_md = extract_gemini_text(response)
                except AttributeError:
                    response = genai.generate_text(model=model_name, prompt=prompt, temperature=0.2)
                    reply_md = extract_gemini_text(response)
                    if not reply_md:
                        reply_md = str(response)
            except Exception as e:
                reply_md = f"**Error calling Gemini API:** {e}.\n\nMake sure GOOGLE_API_KEY is valid."
    else:
        reply_md = "_Google Generative AI client library not installed._\n\nTo enable Gemini responses install 'google-generative-ai' and set GOOGLE_API_KEY.\n\nFallback response (echo):\n\n````\n" + user_input + "\n````"

    # Append assistant reply
    amsg = {"role": "assistant", "content": reply_md, "time": str(datetime.utcnow())}
    chat["messages"].append(amsg)
    save_chats(st.session_state.chats)

    st.rerun()

# Small footer with tips
st.sidebar.markdown("---")
st.sidebar.markdown("Tips: ask for 'python example', 'javascript function', or 'sql query' to get code-formatted answers.")

# End of app
