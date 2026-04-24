import streamlit as st
import os
from typing import List, Dict, Any
import pandas as pd
from PIL import Image
import base64
import io

# Import LangChain components
from langchain_core.messages import HumanMessage

# Import the agent components
try:
    from medical_agent import (
        app as agent_app,
        create_multimodal_message,
        AgentState,
        OPENAI_API_KEY
    )
    API_KEY_AVAILABLE = OPENAI_API_KEY is not None
except Exception as e:
    st.error(f"Error loading agent: {str(e)}")
    API_KEY_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Medical AI Assistant 🏥",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        color: #1f77b4;
        text-align: center;
        font-size: 2.5em;
        margin-bottom: 1em;
    }
    .disclaimer-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        color: #856404;
    }
    .agent-message {
        background-color: #f0f8ff;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #1f77b4;
    }
    .user-message {
        background-color: #e8f5e8;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #28a745;
        text-align: right;
    }
    .tool-result {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
        border-left: 4px solid #6c757d;
        font-family: monospace;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = "web_session_" + str(hash(str(st.session_state)))

def display_message(message):
    """Display a message in the chat interface"""
    if hasattr(message, 'type') and message.type == 'human':
        st.markdown(f'<div class="user-message">{message.content}</div>', unsafe_allow_html=True)
    elif hasattr(message, 'type') and message.type == 'ai':
        if message.content:
            st.markdown(f'<div class="agent-message">{message.content}</div>', unsafe_allow_html=True)
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                st.markdown(f'<div class="tool-result">🔧 Using tool: {tool_call["name"]}</div>', unsafe_allow_html=True)
    elif hasattr(message, 'type') and message.type == 'tool':
        st.markdown(f'<div class="tool-result">📋 Tool Result: {message.content[:500]}...</div>', unsafe_allow_html=True)

def process_user_input(text_input: str, uploaded_image=None):
    """Process user input and get agent response"""
    try:
        # Create message based on input type
        if uploaded_image is not None:
            # Convert image to base64
            image_data = base64.b64encode(uploaded_image.getvalue()).decode('utf-8')
            message = HumanMessage(content=[
                {"type": "text", "text": text_input},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
            ])
        else:
            message = HumanMessage(content=text_input)

        # Add to session messages
        st.session_state.messages.append(message)

        # Prepare input for agent
        input_msg = {"messages": st.session_state.messages}
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        # Get agent response
        response_messages = []
        for event in agent_app.stream(input_msg, config=config):
            for value in event.values():
                if "messages" in value and value["messages"]:
                    for msg in value["messages"]:
                        if msg not in st.session_state.messages:  # Avoid duplicates
                            st.session_state.messages.append(msg)
                            response_messages.append(msg)

        return response_messages

    except Exception as e:
        st.error(f"Error processing input: {str(e)}")
        return []

def load_cases():
    """Load stored cases from CSV"""
    if os.path.exists("patient_cases.csv"):
        try:
            df = pd.read_csv("patient_cases.csv")
            return df
        except Exception as e:
            st.error(f"Error loading cases: {str(e)}")
            return pd.DataFrame()
    return pd.DataFrame()

# Main UI
def main():
    # Header
    st.markdown('<h1 class="main-header">🏥 Multi-Modal Medical AI Assistant</h1>', unsafe_allow_html=True)

    # API Key Check
    if not API_KEY_AVAILABLE:
        st.error("🔑 **API Key Required**: Please add your OpenAI API key to the `.env` file to use the agent.")
        st.code("OPENAI_API_KEY=sk-your-api-key-here", language="bash")
        st.stop()

    # Disclaimer
    st.markdown("""
    <div class="disclaimer-box">
        <strong>⚠️ MEDICAL DISCLAIMER:</strong> This is not a medical diagnosis or treatment recommendation.
        This AI assistant provides general information only. Always consult qualified healthcare professionals
        for medical advice, diagnosis, and treatment.
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("📋 Case Management")

        # Load and display cases
        cases_df = load_cases()
        if not cases_df.empty:
            st.subheader(f"Stored Cases: {len(cases_df)}")
            st.dataframe(cases_df, use_container_width=True)

            # Download button
            csv_data = cases_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Cases CSV",
                data=csv_data,
                file_name="patient_cases.csv",
                mime="text/csv"
            )
        else:
            st.info("No cases stored yet.")

        # Clear conversation
        if st.button("🗑️ Clear Conversation"):
            st.session_state.messages = []
            st.session_state.thread_id = "web_session_" + str(hash(str(st.session_state)))
            st.rerun()

    # Main chat interface
    st.header("💬 Medical Consultation")

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            display_message(message)

    # Input section
    st.markdown("---")
    col1, col2 = st.columns([3, 1])

    with col1:
        text_input = st.text_area(
            "Describe symptoms and medical information:",
            placeholder="e.g., Patient has severe headache, nausea, and sensitivity to light. MRI shows increased signal in temporal lobe.",
            height=100
        )

    with col2:
        uploaded_image = st.file_uploader(
            "Upload MRI/CT scan (optional):",
            type=['jpg', 'jpeg', 'png', 'dicom'],
            help="Upload medical images for analysis"
        )

        if uploaded_image:
            st.image(uploaded_image, caption="Uploaded Image", width=150)

    # Submit button
    if st.button("🔍 Analyze Case", type="primary", use_container_width=True):
        if not text_input.strip():
            st.error("Please enter symptoms or medical information.")
            return

        with st.spinner("Analyzing case..."):
            # Process the input
            response_messages = process_user_input(text_input, uploaded_image)

            # Display new responses
            for msg in response_messages:
                display_message(msg)

            # Rerun to update the chat
            st.rerun()

    # Quick action buttons
    st.markdown("---")
    st.subheader("🚀 Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🏥 Find Hospitals", use_container_width=True):
            quick_input = "Find hospitals with general medicine department in my area."
            with st.spinner("Searching for hospitals..."):
                response_messages = process_user_input(quick_input)
                for msg in response_messages:
                    display_message(msg)
                st.rerun()

    with col2:
        if st.button("💾 Save Current Case", use_container_width=True):
            if len(st.session_state.messages) > 1:
                quick_input = "Please save this case with the analysis above."
                with st.spinner("Saving case..."):
                    response_messages = process_user_input(quick_input)
                    for msg in response_messages:
                        display_message(msg)
                    st.rerun()
            else:
                st.warning("No case to save. Please analyze a case first.")

    with col3:
        if st.button("📋 View Recent Cases", use_container_width=True):
            cases_df = load_cases()
            if not cases_df.empty:
                st.dataframe(cases_df.tail(3), use_container_width=True)
            else:
                st.info("No cases stored yet.")

if __name__ == "__main__":
    main()
