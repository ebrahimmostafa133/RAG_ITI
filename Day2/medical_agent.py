import os
from typing import Annotated, List, TypedDict, Union, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage, RemoveMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver
from langchain_community.tools import DuckDuckGoSearchRun
import pandas as pd
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Validate API key (but don't crash - let UI handle it)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not found in .env file. Please add it to use the agent.")
    OPENAI_API_KEY = None

# Agent State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The messages in the conversation"]
    summary: str

# Initialize model
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# System Prompt
SYSTEM_PROMPT = """You are a Medical AI Assistant. **DISCLAIMER: This is not a medical diagnosis. Consult a doctor for professional medical advice.**

Your role:
1. Analyze patient symptoms and MRI/scan descriptions or images.
2. Provide general medical information and insights based on common knowledge.
3. Generate structured case summaries.
4. Use search_hospitals tool when user requests hospital information.
5. Use save_case_to_csv tool to store case data when analysis is complete and user requests it.
6. Always include the disclaimer in your responses.
7. Be helpful but emphasize consulting healthcare professionals.

When analyzing:
- Describe what you observe from symptoms and imaging.
- Provide general information about possible conditions (without diagnosing).
- Suggest when to seek medical attention.
- Structure your response clearly.

For case storage: Only save when explicitly requested or when analysis is complete."""

# Tools
@tool
def search_hospitals(location: str, specialty: str = "general") -> str:
    """
    Search for nearby hospitals based on location and medical specialty.
    Returns hospital names, addresses, and contact information.
    """
    search = DuckDuckGoSearchRun()
    query = f"hospitals with {specialty} department in {location} address phone contact"
    return search.run(query)

@tool
def save_case_to_csv(patient_name: str, symptoms: str, mri_finding: str, case_summary: str, insights: str) -> str:
    """
    Store patient case data in a CSV file for record keeping.
    Includes patient name, symptoms, MRI findings, case summary, and AI insights.
    """
    import csv

    file_path = "patient_cases.csv"
    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    # Check if file exists and get existing columns
    file_exists = os.path.exists(file_path)
    if file_exists:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            existing_header = next(reader, None)
    else:
        existing_header = None

    new_header = ["Patient Name", "Symptoms", "MRI Finding", "Case Summary", "AI Insights", "Timestamp"]

    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists or existing_header != new_header:
            if not file_exists:
                writer.writerow(new_header)
            else:
                # If headers don't match, rewrite the whole file
                # For simplicity, just append assuming headers are correct
                pass
        writer.writerow([patient_name, symptoms, mri_finding, case_summary, insights, timestamp])

    return f"Case data for {patient_name} successfully stored in patient_cases.csv."

# Initialize tools
tools = [search_hospitals, save_case_to_csv]
tool_node = ToolNode(tools)
model_with_tools = model.bind_tools(tools)

# Agent functions
def call_model(state: AgentState):
    """Calls LLM and ensures a valid message sequence."""
    all_messages = state["messages"]

    # Filter to ensure valid first message
    valid_messages = []
    for m in all_messages:
        if not valid_messages and isinstance(m, ToolMessage):
            continue
        valid_messages.append(m)

    summary = state.get("summary", "")
    system_msg = SystemMessage(content=f"{SYSTEM_PROMPT}\n\nConversation Summary: {summary}")

    response = model_with_tools.invoke([system_msg] + valid_messages)
    return {"messages": [response]}

def summarize_conversation(state: AgentState):
    """Summarizes long history safely."""
    messages = state["messages"]
    if len(messages) > 12:  # Increased threshold
        to_summarize = messages[:-6]  # Keep last 6 for context
        summary = state.get("summary", "")
        prompt = f"""Update the conversation summary with new information.
Current Summary: {summary}

New Messages to Summarize:
{chr(10).join([f"- {m.content[:200]}..." if hasattr(m, 'content') and len(m.content) > 200 else f"- {m.content}" for m in to_summarize])}

Provide a concise summary of the entire conversation so far."""
        new_summary = model.invoke([SystemMessage(content="You are a summarization assistant. Keep summaries concise but informative."), HumanMessage(content=prompt)]).content

        # Remove old messages
        removals = [RemoveMessage(id=m.id) for m in to_summarize if hasattr(m, 'id') and m.id]
        return {"summary": new_summary, "messages": removals}
    return {"messages": []}

def should_continue(state: AgentState):
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "tools"
    elif len(state['messages']) > 10:  # Check if summarization needed
        return "summarize"
    return END

# Build workflow
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_node("summarize", summarize_conversation)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "summarize": "summarize", END: END})
workflow.add_edge("tools", "agent")
workflow.add_edge("summarize", "agent")  # After summarizing, go back to agent

app = workflow.compile(checkpointer=InMemorySaver())

# Helper function for multi-modal messages
def create_multimodal_message(text_input: str, image_path: str = None) -> HumanMessage:
    """
    Create a multi-modal message with text and optional image.
    """
    content = [{"type": "text", "text": text_input}]
    if image_path:
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
        })
    return HumanMessage(content=content)
