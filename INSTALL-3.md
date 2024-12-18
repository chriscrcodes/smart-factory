# Part 4 - Deploy and use the Generative AI Factory Assistant

## Deploy a Large Language Model (LLM) in Azure Open AI
   - [Deploy a base model](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource?pivots=web-portal#deploy-a-model):
      - Login to [Azure AI Foundry Portal](https://ai.azure.com/)
      - Select your deployment in `Shared resources` > `Deployments` > `smart-factory`
      - Copy the following information in `Endpoint` section: `Target URI` and `Key`. We will need them in the next section.

## Create an environment variable file
- Rename the file [`.env_template`](./artifacts/factory-assistant/.env_template) to `.env`
- Retrieve the environment following variables you defined in [Part 1 - Provision resources (Edge and Cloud)](./INSTALL-1.md) ==> file `variables.yaml`:
    ```bash
    FACTORY_AGENT_SP_APPID
    FACTORY_AGENT_SP_SECRET
    TENANT
    ```
- Select 'Real-Time Intelligence' from the [Fabric homepage](https://app.powerbi.com/home?experience=kusto).  
![fabric-home](./artifacts/media/fabric-home.png "fabric-home")
- Click on `Workspaces` > `Smart Factory`
- Select the database `AIO` (type: `KQL Database`)
- Retrieve the Fabric endpoint from `Overview` > `Query URI` > click `Copy URI`
- Modify environment variables in `.env` file
    ```bash
    AZURE_OPENAI_ENDPOINT           = < Azure AI Foundry Portal => Target URI >
    AZURE_OPENAI_API_KEY            = < Azure AI Foundry Portal => Key >
    AZURE_OPENAI_DEPLOYMENT_NAME    = "smart-factory"
    AZURE_OPENAI_MODEL_NAME         = "gpt-4o"
    AZURE_OPENAI_DEPLOYMENT_VERSION = "2024-08-06"

    AZURE_AD_TENANT_ID              = < variables.yaml => TENANT >
    KUSTO_CLUSTER                   = < Microsoft Fabric => Query URI >
    KUSTO_MANAGED_IDENTITY_APP_ID   = < variables.yaml => FACTORY_AGENT_SP_APPID >
    KUSTO_MANAGED_IDENTITY_SECRET   = < variables.yaml => FACTORY_AGENT_SP_SECRET >
    KUSTO_DATABASE_NAME             = "AIO"
    KUSTO_TABLE_NAME                = "aio_gold"
    ```

## Start the Factory Assistant Application
- Option 1 (from command line)
    - Start a terminal from the [directory](./artifacts/factory-assistant/)
    - Execute the following commands:
        ```bash
        pip install -r requirements.txt
        streamlit run .\frontend.py
        ```
- Option 2 (Docker)
    - Start a terminal from the [directory](./artifacts/factory-assistant/)
    - Execute the following commands:
        ```bash
        docker build . -t factory-assistant:v1.0
        docker run -p 8501:8501 factory-assistant:v1.0
        ```
- Launch a browser with the following URL to access the application:
    ```
    http://localhost:8501/
    ```
- You can now query the database using Natural Language  
    > **IMPORTANT**: No actual data from the database is transmitted to the Large Language Model; only the prompt and the database schema are shared. The LLM will generate the query to be executed against the database, but it won't execute the query itself.  
- Some example queries are provided.

    ![Factory Assistant User Interface](./artifacts/media/demo-video.gif "Factory Assistant User Interface")