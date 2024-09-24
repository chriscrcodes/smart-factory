# Import Python Libraries
import os
import asyncio
from dotenv import load_dotenv
import pandas as pd
import yaml
import json
import streamlit as st
from backend import SKernel, KustoConnect, AgentKusto
from azure.kusto.data.helpers import dataframe_from_result_table

# Load variables from .env file
load_dotenv()

# Instantiate Semantic Kernel and Plugin
kernel, plugin = SKernel()

# Retrieve Kusto Table Schema
query_schema = asyncio.run(KustoConnect(
    os.getenv('KUSTO_DATABASE_NAME'),
    f".show table {os.getenv('KUSTO_TABLE_NAME')} schema as json"
))
schema = str(dataframe_from_result_table(query_schema).Schema[0])

# Clear chat session
def clear_input():
    st.session_state.pop("question", None)
    st.session_state.pop("messages", None)
    st.session_state.selected_question = ""

# Configure Streamlit
with open('./frontend_config.yml', 'r') as file:
    config = yaml.safe_load(file)

title = config['streamlit']['title']

# Load sample questions
with open('sample_questions.json', 'r', encoding="utf-8") as file:
    example_questions = json.load(file)
question_list = [q for q in example_questions.values()]

# Set page config
st.set_page_config(
    page_title=config['streamlit']['tab_title']
)
st.image(config['streamlit']['logo'], width=400)
st.caption(config['streamlit']['caption'])

# Set sidebar
st.sidebar.title("About")
st.sidebar.info(config['streamlit']['about'])
reset = st.sidebar.button("Reset Chat", on_click=clear_input)

# Initialize session state
if "question" not in st.session_state:
    st.session_state.question = ""
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": config['streamlit']['assistant_intro_message']}]

# Example questions select box
question = st.selectbox("Example Questions:", [""] + question_list, key="selected_question")

# Check for duplicates
if question and not any(isinstance(msg["content"], str) and msg["content"] == question for msg in st.session_state.messages):
    st.session_state.messages.append({"role": "user", "content": question})

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if type(message["content"]) == pd.DataFrame:
            st.dataframe(message["content"])
        else:
            st.write(message["content"])

# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

last_msg = st.session_state.messages[-1]

# Generate a new response if last message is not from assistant
if last_msg["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner('Thinking...'):
            prompt = last_msg["content"]
            response = asyncio.run(AgentKusto(
                kernel, plugin, prompt,
                os.getenv('KUSTO_DATABASE_NAME'), os.getenv('KUSTO_TABLE_NAME'), schema
            ))
    st.write(response)
    st.session_state.messages.append({"role": "assistant", "content": response})