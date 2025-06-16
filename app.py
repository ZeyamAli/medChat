import streamlit as st
import requests
import json
import time
from datetime import datetime

# Configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "internlm2:1.8b"

def check_ollama_connection():
    """Check if Ollama is running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_model_exists():
    """Check if model is available."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return any(model['name'] == MODEL_NAME for model in models)
    except:
        return False

def pull_model():
    """Download the model."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        response = requests.post(
            "http://localhost:11434/api/pull",
            json={"name": MODEL_NAME},
            stream=True,
            timeout=600
        )
        
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if 'status' in data:
                        status_text.text(f"📥 {data['status']}")
                    if 'completed' in data and 'total' in data:
                        progress = data['completed'] / data['total']
                        progress_bar.progress(progress)
                    if data.get('completed', False):
                        status_text.text("✅ Model downloaded successfully!")
                        progress_bar.progress(1.0)
                        break
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        st.error(f"❌ Error downloading model: {e}")

def chat_with_ollama(prompt, history):
    """Send message to Ollama and get streaming response."""
    # Build context from chat history
    context = ""
    for msg in history[-5:]:  # Last 5 messages for context
        role = "Human" if msg["role"] == "user" else "Assistant"
        context += f"{role}: {msg['content']}\n"
    
    full_prompt = context + f"Human: {prompt}\nAssistant: "
    
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": True,
        "options": {
            "temperature": st.session_state.get('temperature', 0.7),
            "num_predict": st.session_state.get('max_tokens', 1000)
        }
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, stream=True, timeout=60)
        response.raise_for_status()
        
        full_response = ""
        response_placeholder = st.empty()
        
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if 'response' in data:
                        full_response += data['response']
                        response_placeholder.markdown(full_response + "▋")
                    if data.get('done', False):
                        response_placeholder.markdown(full_response)
                        break
                except json.JSONDecodeError:
                    continue
        
        return full_response
    
    except Exception as e:
        return f"❌ Error: {e}"

# Custom CSS for beautiful interface
def load_css():
    st.markdown("""
    <style>
    /* Main app styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
    }
    
    /* Chat message styling */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Custom header */
    .custom-header {
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #ffeaa7);
        background-size: 300% 300%;
        animation: gradientShift 8s ease infinite;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .custom-header h1 {
        color: white;
        font-size: 3rem;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        font-weight: 700;
    }
    
    .custom-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
    }
    
    /* Status cards */
    .status-card {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
    }
    
    .status-success {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        color: white;
    }
    
    .status-warning {
        background: linear-gradient(135deg, #ff9800, #f57c00);
        color: white;
    }
    
    .status-error {
        background: linear-gradient(135deg, #f44336, #d32f2f);
        color: white;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 15px;
        color: white;
        backdrop-filter: blur(10px);
    }
    
    /* Metrics styling */
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
        border-radius: 15px;
        padding: 1rem;
        text-align: center;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin: 0.5rem 0;
    }
    
    /* Chat input */
    .stChatInput {
        border-radius: 25px;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Sidebar content */
    .sidebar-content {
        color: white;
    }
    
    /* Animation for typing indicator */
    @keyframes typing {
        0%, 60%, 100% { opacity: 1; }
        30% { opacity: 0.4; }
    }
    
    .typing-indicator {
        animation: typing 1.5s infinite;
    }
    </style>
    """, unsafe_allow_html=True)

# Streamlit App Configuration
st.set_page_config(
    page_title="🤖 AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_css()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7
if "max_tokens" not in st.session_state:
    st.session_state.max_tokens = 1000

# Custom Header
st.markdown("""
<div class="custom-header">
    <h1>🤖 AI ChatBot</h1>
    <p>Powered by InternLM2 & Ollama</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    
    # Header
    st.markdown("## 🎛️ Control Panel")
    
    # Connection Status
    st.markdown("### 📡 Connection Status")
    
    if check_ollama_connection():
        st.markdown("""
        <div class="status-card status-success">
            <h4>✅ Ollama Server</h4>
            <p>Connected & Running</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Model Status
        if check_model_exists():
            st.markdown("""
            <div class="status-card status-success">
                <h4>🧠 InternLM2 Model</h4>
                <p>Ready to Chat!</p>
            </div>
            """, unsafe_allow_html=True)
            model_ready = True
        else:
            st.markdown("""
            <div class="status-card status-warning">
                <h4>⚠️ Model Missing</h4>
                <p>Click to download</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📥 Download InternLM2", key="download_btn"):
                with st.spinner("🔄 Downloading model... Please wait..."):
                    pull_model()
                    st.success("🎉 Model downloaded successfully!")
                    time.sleep(2)
                    st.rerun()
            model_ready = False
    else:
        st.markdown("""
        <div class="status-card status-error">
            <h4>❌ Connection Failed</h4>
            <p>Please start Ollama server</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        ### 🚀 Quick Start
        1. Open Command Prompt
        2. Run: `ollama serve`
        3. Refresh this page
        """)
        model_ready = False
    
    # Settings
    st.markdown("---")
    st.markdown("### ⚙️ Chat Settings")
    
    st.session_state.temperature = st.slider(
        "🌡️ Temperature", 
        min_value=0.0, 
        max_value=2.0, 
        value=st.session_state.temperature,
        step=0.1,
        help="Higher values make responses more creative"
    )
    
    st.session_state.max_tokens = st.slider(
        "📝 Max Response Length", 
        min_value=100, 
        max_value=2000, 
        value=st.session_state.max_tokens,
        step=100,
        help="Maximum number of tokens in response"
    )
    
    # Chat Statistics
    st.markdown("---")
    st.markdown("### 📊 Chat Stats")
    
    total_messages = len(st.session_state.messages)
    user_messages = len([m for m in st.session_state.messages if m["role"] == "user"])
    ai_messages = len([m for m in st.session_state.messages if m["role"] == "assistant"])
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>💬</h3>
            <p>{total_messages}</p>
            <small>Total Messages</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🤖</h3>
            <p>{ai_messages}</p>
            <small>AI Responses</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Control Buttons
    st.markdown("---")
    st.markdown("### 🎮 Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", key="clear_btn"):
            st.session_state.messages = []
            st.success("Chat cleared!")
            time.sleep(1)
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh", key="refresh_btn"):
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: rgba(255,255,255,0.7);">
        <small>Made with ❤️ using Streamlit</small><br>
        <small>Current time: {}</small>
    </div>
    """.format(datetime.now().strftime("%H:%M:%S")), unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main Chat Interface
if model_ready:
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Welcome message
        if not st.session_state.messages:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; background: rgba(255,255,255,0.1); 
                        border-radius: 20px; margin: 2rem 0; backdrop-filter: blur(10px);">
                <h2 style="color: white;">Welcome to AI ChatBot!</h2>
                <p style="color: rgba(255,255,255,0.8); font-size: 1.1rem;">
                    I'm powered by InternLM2 and ready to help you with anything!<br>
                    Ask me questions, have a conversation, or just say hello!
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Display chat messages
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.markdown(f"**You:** {message['content']}")
                else:
                    st.markdown(f"**AI:** {message['content']}")
    
    # Chat input
    if prompt := st.chat_input("💭 Type your message here...", key="chat_input"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(f"**You:** {prompt}")
        
        # Generate AI response
        with st.chat_message("assistant"):
            st.markdown("**AI:** <span class='typing-indicator'>Thinking...</span>", unsafe_allow_html=True)
            response = chat_with_ollama(prompt, st.session_state.messages[:-1])
        
        # Add AI response to history
        st.session_state.messages.append({"role": "assistant", "content": response})

else:
    # Model not ready message
    st.markdown("""
    <div style="text-align: center; padding: 3rem; background: rgba(255,255,255,0.1); 
                border-radius: 20px; margin: 2rem 0; backdrop-filter: blur(10px);">
        <h2 style="color: white;">🚀 Getting Ready...</h2>
        <p style="color: rgba(255,255,255,0.8); font-size: 1.1rem;">
            Please ensure Ollama is running and download the InternLM2 model to start chatting!
        </p>
        <div style="margin-top: 2rem;">
            <p style="color: rgba(255,255,255,0.6);">
                ⚡ Fast responses • 🧠 Smart AI • 💬 Natural conversations
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)