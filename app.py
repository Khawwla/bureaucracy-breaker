import streamlit as st
import os
import time
import json
import glob
from google import genai
from google.genai import types

# Page Config
st.set_page_config(page_title="Bureaucracy Breaker", page_icon="🛡️", layout="wide")

# Custom CSS
# Custom CSS
st.markdown("""
<style>
    /* Make the button look like a primary action */
    .stButton>button {
        width: 100%;
        background-color: #4285F4;
        color: white;
        border-radius: 5px;
    }
    
    /* Fix for text visibility: Ensure chat messages have high contrast */
    [data-testid="stChatMessage"] {
        background-color: transparent;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
</style>
""", unsafe_allow_html=True)
# Title & Header
col1, col2 = st.columns([1, 4])
with col1:
    st.title("🛡️")
with col2:
    st.title("Bureaucracy Breaker")
    st.caption(f"Powered by **Gemini 3 Flash Preview** | Status: ONLINE")

# 1. SETUP API
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

# CONFIGURATION FOR GEMINI 3
# We enable 'include_thoughts' to show the reasoning process
gemini_config = {
    "thinking_config": {
        "include_thoughts": True
    }
}

# FOLDER FOR SAVED CASES
if not os.path.exists("saved_cases"):
    os.makedirs("saved_cases")

def save_case(filename, history):
    with open(f"saved_cases/{filename}.json", "w") as f:
        json.dump(history, f)
    st.sidebar.success(f"Case '{filename}' saved!")

def load_case(filename):
    with open(f"saved_cases/{filename}", "r") as f:
        return json.load(f)

if api_key:
    client = genai.Client(api_key=api_key)

    # --- SIDEBAR: CASE MANAGEMENT ---
    st.sidebar.header("📂 Case Files")
    saved_files = glob.glob("saved_cases/*.json")
    case_names = [os.path.basename(f) for f in saved_files]
    
    selected_case = st.sidebar.selectbox("Load a Previous Case", ["Start New Case"] + case_names)

    # Initialize History
    if "history" not in st.session_state or selected_case == "Start New Case":
        if selected_case == "Start New Case" and "history" not in st.session_state:
             st.session_state['history'] = []
    else:
        if st.sidebar.button("📂 Load Selected Case"):
            st.session_state['history'] = load_case(selected_case)
            st.session_state['file_processed'] = True
            st.rerun()

    # --- MAIN INTERFACE ---

    # 1. NEW CASE UPLOAD
    if not st.session_state.get('file_processed'):
        st.subheader("Start a New Fight")
        uploaded_file = st.file_uploader("Upload Document (PDF/Image)", type=["pdf", "jpg", "png"])

        if uploaded_file is not None:
            # Save locally
            with open("temp_doc.pdf", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            if st.button("🚀 Analyze & Find Loopholes"):
                with st.spinner("Gemini 3 is analyzing fine print..."):
                    try:
                        # Upload to Gemini
                        sample_file = client.files.upload(
                            file='temp_doc.pdf',
                            config={'mime_type': 'application/pdf'} 
                        )
                        time.sleep(3) 

                        # THE "LAWYER" PROMPT
                        prompt = """
                        You are an aggressive, high-level bureaucratic advocate. 
                        Analyze this document.
                        1. Summarize the document in plain English.
                        2. Identify 3 specific "Gotcha" clauses that are dangerous.
                        3. Identify 1 "Loophole" or exit strategy for the user.
                        """
                        
                        # Generate with GEMINI 3
                        response = client.models.generate_content(
                            model="gemini-3-flash-preview",  # <--- YOUR NEW MODEL
                            contents=[sample_file, prompt],
                            config=gemini_config
                        )
                        
                        # Save to State
                        st.session_state['history'] = [
                            {"role": "user", "parts": [{"text": prompt}]},
                            {"role": "model", "parts": [{"text": response.text}]} 
                        ]
                        st.session_state['file_processed'] = True
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error: {e}")

    # 2. ACTIVE CASE INTERFACE
    else:
        st.info("✅ Case Active. Context Loaded.")
        
        # Display Chat History
        for msg in st.session_state['history']:
            role = "🤖 Agent" if msg['role'] == "model" else "👤 You"
            with st.chat_message(msg['role']):
                st.markdown(msg['parts'][0]['text'])

        # User Input
        user_input = st.chat_input("Ask for a draft, a summary, or legal clarification...")
        
        if user_input:
            # Add user message
            st.session_state['history'].append({"role": "user", "parts": [{"text": user_input}]})
            with st.chat_message("user"):
                st.markdown(user_input)

            # Generate Reply
            with st.chat_message("model"):
                with st.spinner("Thinking..."):
                    response = client.models.generate_content(
                        model="gemini-3-flash-preview", # <--- YOUR NEW MODEL
                        contents=st.session_state['history'],
                        config=gemini_config
                    )
                    
                    # Show Thoughts (If Gemini 3 provides them)
                    # Note: Depending on the exact preview version, thought parts might vary.
                    # We check if there are candidates with thoughts.
                    try:
                         # This is a basic check for thoughts in the new SDK
                         if hasattr(response, 'candidates') and response.candidates:
                            for part in response.candidates[0].content.parts:
                                if hasattr(part, 'thought') and part.thought:
                                    with st.expander("🧠 View Gemini 3 Reasoning Chain"):
                                        st.markdown(part.thought)
                    except:
                        pass # Ignore if no thoughts returned

                    st.markdown(response.text)
            
            # Save AI message
            st.session_state['history'].append({"role": "model", "parts": [{"text": response.text}]})

        # --- SAVE BUTTON ---
        st.divider()
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            save_name = st.text_input("Case Name", placeholder="e.g., Landlord Dispute")
        with col_s2:
            st.write("") 
            st.write("") 
            if st.button("💾 Save Case State"):
                if save_name:
                    save_case(save_name, st.session_state['history'])
                else:
                    st.warning("Please name the case first.")

else:
    st.warning("👈 Please enter your API Key in the sidebar to start.")