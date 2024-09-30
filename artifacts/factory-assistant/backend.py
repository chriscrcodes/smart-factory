# Import Python Libraries
import os, re
from datetime import datetime
from azure.kusto.data import KustoConnectionStringBuilder
from azure.kusto.data.aio import KustoClient
from azure.kusto.data.helpers import dataframe_from_result_table
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments

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