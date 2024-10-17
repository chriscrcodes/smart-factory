# Import Python Libraries
import os, re, asyncio, yaml, json
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
from datetime import datetime
from azure.kusto.data import KustoConnectionStringBuilder
from azure.kusto.data.aio import KustoClient
from azure.kusto.data.helpers import dataframe_from_result_table
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments

# Load variables from .env file
load_dotenv()

# Create connection to Kusto Database
async def KustoConnect(database, query):
    kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
        os.getenv('KUSTO_CLUSTER'),
        os.getenv('KUSTO_MANAGED_IDENTITY_APP_ID'),
        os.getenv('KUSTO_MANAGED_IDENTITY_SECRET'),
        os.getenv('AZURE_AD_TENANT_ID')
    )
    try:
        async with KustoClient(kcsb) as client:
            clientExecute = await client.execute(database, query)
            results = clientExecute.primary_results[0]
    except:
        results = "Error while executing query."
    return results

# Instantiate Semantic Kernel
def SKernel():
    kernel = Kernel()
    chat_completion = AzureChatCompletion(
        deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
        api_key = os.getenv('AZURE_OPENAI_API_KEY'),
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    )
    kernel.add_service(chat_completion)
    plugin = kernel.add_plugin(
        parent_directory = os.path.join(__file__, "../Plugins/"),
        plugin_name = "DataAnalysis"
    )
    return kernel, plugin

# Load Custom Plugin for Kusto Query Language
async def AgentKusto(kernel, plugin, prompt, database, table, schema):
    arguments = KernelArguments(
        request = prompt,
        table = table,
        schema = schema
    )
    SKInvoke = await kernel.invoke(plugin["KustoQL"], arguments)
    cleaned_output = str(SKInvoke).replace("kusto", "").replace("```kql", "").replace("```", "")
    SKResponse = re.search(r"RESPONSE_START\n((.|\n)*)\nRESPONSE_END", str(cleaned_output))
    if (SKResponse):
        queryStatement = SKResponse.group(1)
        now = datetime.now()
        date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
        print(date_time + ': ' + prompt)
        print("QUERY:" + queryStatement)
        try:
            ExecuteQueryKustoDB = await KustoConnect(database, SKResponse.group(1))
            dataframe = dataframe_from_result_table(ExecuteQueryKustoDB)
            if not dataframe.empty:
                results = dataframe
            else:
                results = "Query returned 0 result."
        except:
            results = "Error while executing query."
    else:
        results = str(SKInvoke)
    return results

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
with open('sample_questions.json', 'r', encoding = "utf-8") as file:
    example_questions = json.load(file)
question_list = [q for q in example_questions.values()]

# Set page config
st.set_page_config(
    page_title = config['streamlit']['tab_title']
)

left_co, cent_co,last_co = st.columns(3)
with cent_co:
    st.image(config['streamlit']['logo'], width = 400)
st.title(config['streamlit']['title'])

# Set sidebar
st.sidebar.info(config['streamlit']['about'])
reset = st.sidebar.button("Reset Chat", on_click = clear_input)

# Initialize session state
if "question" not in st.session_state:
    st.session_state.question = ""
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": config['streamlit']['assistant_intro_message']}]

# Example questions select box
question = st.selectbox("Example Questions:", [""] + question_list, key = "selected_question")

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