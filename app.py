import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


load_dotenv()

NOTEBOOK_PATH = Path("mp3_assignment_tanh0549_yuyang14_final.ipynb")
MODEL_SMALL = "gpt-4o-mini"
MODEL_LARGE = "gpt-4o"

st.set_page_config(page_title="Mini Project 3 Agents", page_icon="💬", layout="wide")
st.title("Mini Project 3 Agent Chat")


def load_notebook_agents() -> dict:
    if "notebook_globals" in st.session_state:
        return st.session_state.notebook_globals

    notebook = json.loads(NOTEBOOK_PATH.read_text())
    code_cells = {
        idx: "".join(cell["source"])
        for idx, cell in enumerate(notebook["cells"])
        if cell["cell_type"] == "code"
    }
    needed_cells = [4, 6, 8, 10, 12, 14, 15, 19, 25]

    namespace = {"__builtins__": __builtins__}
    for cell_idx in needed_cells:
        source = code_cells[cell_idx]
        for marker in ['print("=== Tool 6 tests ===")', "# Quick test"]:
            if marker in source:
                source = source.split(marker, 1)[0]
        exec(source, namespace)

    st.session_state.notebook_globals = namespace
    return namespace


def check_config() -> str | None:
    if os.getenv("OPENAI_API_KEY") in (None, "", "YOUR_KEY"):
        return "OPENAI_API_KEY is missing. Set it in your environment or .env file."
    if os.getenv("ALPHAVANTAGE_API_KEY") in (None, "", "YOUR_KEY"):
        return "ALPHAVANTAGE_API_KEY is missing. Set it in your environment or .env file."
    if not Path("stocks.db").exists():
        return "Local database not found: stocks.db"
    return None


def build_question_with_history(question: str) -> str:
    history = st.session_state.messages[-6:]
    if not history:
        return question

    conversation = []
    for message in history:
        role = "User" if message["role"] == "user" else "Assistant"
        conversation.append(f"{role}: {message['content']}")
    conversation.append(f"Current user question: {question}")
    return "\n".join(conversation)


def run_selected_agent(question: str, architecture: str, model: str) -> dict:
    agents = load_notebook_agents()
    agents["ACTIVE_MODEL"] = model
    full_question = build_question_with_history(question)

    if architecture == "Single Agent":
        result = agents["run_single_agent"](full_question, verbose=False)
        return {"answer": result.answer, "architecture": architecture, "model": model}

    result = agents["run_multi_agent"](full_question, verbose=False)
    return {"answer": result["final_answer"], "architecture": architecture, "model": model}


def clear_conversation() -> None:
    st.session_state.messages = []


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    architecture = st.selectbox("Agent selector", ["Single Agent", "Multi-Agent"])
    model = st.selectbox("Model selector", [MODEL_SMALL, MODEL_LARGE])
    st.button("Clear conversation", on_click=clear_conversation, use_container_width=True)

config_error = check_config()
if config_error:
    st.error(config_error)
    st.stop()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            st.caption(f"{message['architecture']} | {message['model']}")

if prompt := st.chat_input("Ask about stocks, sectors, fundamentals, or sentiment"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Running agent..."):
            reply = run_selected_agent(prompt, architecture, model)
        st.markdown(reply["answer"])
        st.caption(f"{reply['architecture']} | {reply['model']}")

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": reply["answer"],
            "architecture": reply["architecture"],
            "model": reply["model"],
        }
    )
