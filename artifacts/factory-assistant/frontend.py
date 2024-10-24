import os
import re
import asyncio
import yaml
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from azure.kusto.data import KustoConnectionStringBuilder
from azure.kusto.data.aio import KustoClient
from azure.kusto.data.helpers import dataframe_from_result_table
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents.chat_history import ChatHistory

# Load environment variables from .env file
load_dotenv()

async def connect_kusto(database: str, query: str) -> str | pd.DataFrame:
    """Establish an asynchronous connection to the Kusto database and execute a query."""
    kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
        os.getenv('KUSTO_CLUSTER'),
        os.getenv('KUSTO_MANAGED_IDENTITY_APP_ID'),
        os.getenv('KUSTO_MANAGED_IDENTITY_SECRET'),
        os.getenv('AZURE_AD_TENANT_ID')
    )

    async with KustoClient(kcsb) as client:
        try:
            client_execute = await client.execute(database, query)
            results = client_execute.primary_results[0]
            return dataframe_from_result_table(results)
        except SyntaxError as e:
            return f"Syntax error in query: {str(e)}"
        except Exception as e:
            return f"Error while executing query: {str(e)}"

def instantiate_kernel() -> tuple[Kernel, str]:
    """Instantiate the Semantic Kernel with the OpenAI service."""
    kernel = Kernel()
    chat_completion = AzureChatCompletion(
        deployment_name=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
        api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
    )
    kernel.add_service(chat_completion)

    plugin = kernel.add_plugin(
        parent_directory=os.path.join(__file__, "../Plugins/"),
        plugin_name="DataAnalysis"
    )
    return kernel, plugin

async def agent_kusto(kernel: Kernel, plugin: str, prompt: str, database: str, table: str, schema: str, chat_history: ChatHistory) -> str | pd.DataFrame:
    """Generate a Kusto query using the Semantic Kernel and execute it."""
    arguments = KernelArguments(request=prompt, table=table, schema=schema)
    chat_history.add_user_message(prompt)

    sk_invoke = await kernel.invoke(plugin["KustoQL"], arguments, chat_history=chat_history)
    cleaned_output = str(sk_invoke).replace("kusto", "").replace("```kql", "").replace("```", "")
    sk_response = re.search(r"RESPONSE_START\n((.|\n)*)\nRESPONSE_END", cleaned_output)

    if sk_response:
        query_statement = sk_response.group(1).strip()

        if "kql" not in str(sk_invoke).lower():
            chat_history.add_assistant_message(query_statement)
            return query_statement

        print(f"\n[DEBUG] QUERY:\n{query_statement}\n")

        execute_query_kusto_db = await connect_kusto(database, query_statement)

        if isinstance(execute_query_kusto_db, str):
            return execute_query_kusto_db  # Return the error message

        if execute_query_kusto_db.empty:
            return "No data found for the given query."

        chat_history.add_assistant_message(execute_query_kusto_db.to_json(orient="records"))
        return execute_query_kusto_db  # Return the DataFrame for display

    chat_history.add_assistant_message(cleaned_output)
    return cleaned_output

def clear_input() -> None:
    """Clear the session state for chat messages and reset the application state."""
    st.session_state.pop("messages", None)
    st.session_state.pop("chat_history", None)

# Instantiate Semantic Kernel and Plugin
kernel, plugin = instantiate_kernel()

# Retrieve Kusto Table Schema
query_schema = asyncio.run(connect_kusto(
    os.getenv('KUSTO_DATABASE_NAME'),
    f".show table {os.getenv('KUSTO_TABLE_NAME')} schema as json"
))
schema = str(query_schema.Schema[0])

# Configure Streamlit application
with open('./frontend_config.yml', 'r') as file:
    config = yaml.safe_load(file)
title = config['streamlit']['title']

# Load sample questions from JSON file
with open('sample_questions.json', 'r', encoding="utf-8") as file:
    example_questions = json.load(file)
question_list = [q for q in example_questions.values()]

# Set the full-screen page configuration for the app
st.set_page_config(page_title=config['streamlit']['tab_title'], layout='wide')

# Display logo and title
st.image(config['streamlit']['logo'], width=800)
st.title(title)

# Initialize session state for messages if not already present
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": config['streamlit']['assistant_intro_message']}]

# Ensure chat history is initialized as well
if "chat_history" not in st.session_state:
    st.session_state.chat_history = ChatHistory()

# Sidebar for displaying example questions and reset button
with st.sidebar:
    st.header("FAQ")
    for question in question_list:
        with st.expander(label=question, expanded=False):
            if st.button("Ask", key=question):  # Unique key for each button
                # Check if the question has already been asked
                if not any(isinstance(msg["content"], str) and msg["content"] == question for msg in st.session_state.messages):
                    st.session_state.messages.append({"role": "user", "content": question})

    if st.button("Reset Chat"):
        clear_input()  # Clear session state and reinitialize

# Display chat messages in the chat window
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": config['streamlit']['assistant_intro_message']}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        content = message["content"]
        if isinstance(content, pd.DataFrame):
            st.dataframe(content.style.format(na_rep='NA'))
        else:
            st.markdown(f"**{message['role'].capitalize()}:** {content.strip()}")  # Enhanced formatting for readability

# User-provided input for additional prompts
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f"**User:** {prompt.strip()}")  # Enhanced formatting

last_msg = st.session_state.messages[-1]

# Generate a new response if the last message is not from the assistant
if last_msg["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner('Thinking...'):
            response = asyncio.run(agent_kusto(
                kernel, plugin, last_msg["content"],
                os.getenv('KUSTO_DATABASE_NAME'), os.getenv('KUSTO_TABLE_NAME'), schema,
                st.session_state.chat_history  # Pass chat history to the agent
            ))
        if isinstance(response, pd.DataFrame):
            st.dataframe(response.style.format(na_rep='NA'))  # Ensure DataFrame is displayed correctly
        else:
            st.markdown(response.strip())  # Use markdown for other responses
    st.session_state.messages.append({"role": "assistant", "content": response})