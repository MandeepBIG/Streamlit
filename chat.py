import streamlit as st
import json
from datetime import datetime
from streamlit_oauth import OAuth2Component

# --- 1. GOOGLE SSO CONFIGURATION ---
# In production, move these to .streamlit/secrets.toml
CLIENT_ID = "936071945406-udvc62h3ne5ruur0rdda8mvaq7gt58rg.apps.googleusercontent.com"
CLIENT_SECRET = "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"
AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"

def handle_login():
    if "auth" not in st.session_state:
        oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, TOKEN_URL, REVOKE_URL)
        
        result = oauth2.authorize_button(
            name="Continue with Google",
            icon="https://www.google.com/favicon.ico",
            redirect_uri="http://localhost:8501",
            scope="openid email profile",
            key="google_auth",
            use_container_width=False
        )
        
        if result:
            st.session_state.auth = result
            st.rerun()
        st.stop()

# --- 2. SESSION STATE SETUP ---
def init_app_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "feedback" not in st.session_state:
        st.session_state.feedback = {}

# --- 3. MOCK RAG BACKEND (Replace with your API call) ---
def query_rag_engine(prompt, doc_range):
    # This is where you'd use: response = requests.post(url, json=...)
    # Mocking a JSON response from backend:
    return {
        "answer": f"Analysis complete for range {doc_range[0]}-{doc_range[1]}. The prompt '{prompt}' relates to Section 4 of the docs.",
        "confidence": 0.92,
        "sources": [f"Document_{doc_range[0]}.pdf", "Appendix_B.pdf"],
        "server_time": datetime.now().strftime("%H:%M:%S")
    }

# --- 4. MAIN UI ---
def main():
    st.set_page_config(page_title="RAG Intelligence Hub", layout="wide")
    
    # Trigger SSO
    handle_login()
    init_app_state()

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.write(f"Logged in: **{st.session_state.auth.get('token', {}).get('email', 'User')}**")
        st.divider()
        
        # Document Range Slider
        doc_range = st.slider(
            "Select Document Range",
            min_value=1,
            max_value=1000,
            value=(1, 50),
            step=1
        )
        
        if st.button("Log Out"):
            del st.session_state.auth
            st.rerun()

    # --- CHAT DISPLAY ---
    st.title("🔍 RAG Assistant")
    
    # Render historical messages
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
            if msg["role"] == "assistant":
                # Feedback buttons
                f_col1, f_col2, _ = st.columns([0.05, 0.05, 0.9])
                if f_col1.button("👍", key=f"like_{i}"):
                    st.session_state.feedback[i] = "Liked"
                if f_col2.button("👎", key=f"dislike_{i}"):
                    st.session_state.feedback[i] = "Disliked"
                
                if i in st.session_state.feedback:
                    st.caption(f"Feedback submitted: {st.session_state.feedback[i]}")

    # --- INPUT AREA ---
    if prompt := st.chat_input("Enter your query here..."):
        # User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Assistant Response
        with st.chat_message("assistant"):
            with st.spinner("Processing documents..."):
                backend_data = query_rag_engine(prompt, doc_range)
                answer = backend_data["answer"]
                
                st.write(answer)
                with st.expander("View Source Metadata"):
                    st.json(backend_data)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "metadata": backend_data
                })
        st.rerun()

    # --- DOWNLOAD SECTION ---
    if st.session_state.messages:
        st.divider()
        # Prepare chat history for download
        full_history = {
            "user": st.session_state.auth.get('token', {}).get('email'),
            "timestamp": datetime.now().isoformat(),
            "chat": st.session_state.messages,
            "feedback": st.session_state.feedback
        }
        
        st.download_button(
            label="💾 Download Chat History",
            data=json.dumps(full_history, indent=4),
            file_name=f"rag_session_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )

if __name__ == "__main__":
    main()