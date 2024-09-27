### Part 4 - Deploy and use the Generative AI Factory Assistant

#### Deploy a Large Language Model (LLM) in Azure Open AI
   - [Deploy a base model](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource?pivots=web-portal#deploy-a-model):
      - Login to [Azure OpenAI Studio](https://oai.azure.com/)
      - Select `gpt-4o` > click `Confirm`
      - Deployment Name: `dev`
      - Model version: `2024-08-06`
      - Name: `gpt-4o`

#### Create an environment variable file
- Rename the file [`.env_template`](./artifacts/factory-assistant/.env_template) to `.env`
```bash
mv .env_template .env
```
- Retrieve the environment following variables you defined in [Part 1 - Provision resources (Edge and Cloud)](./INSTALL-1.md) ==> **Note(2)**:
    ```bash
    $ASSISTANT_APP_ID
    $ASSISTANT_APP_SECRET
    $ASSISTANT_TENANT
    $AZURE_OPENAI_KEY
    ```
- Modify environment variables in `.env` file
```bash
AZURE_OPENAI_ENDPOINT           = < YOUR OPEN AI ENDPOINT IN AZURE > # To be documented
AZURE_OPENAI_API_KEY            = < VALUE OF $AZURE_OPENAI_KEY VARIABLE >
AZURE_OPENAI_DEPLOYMENT_NAME    = "dev"
AZURE_OPENAI_MODEL_NAME         = "gpt-4o"
AZURE_OPENAI_DEPLOYMENT_VERSION = "2024-08-06"

AZURE_AD_TENANT_ID              = < VALUE OF $ASSISTANT_TENANT VARIABLE >
KUSTO_CLUSTER                   = < YOUR FABRIC ENDPOINT > # To be documented
KUSTO_MANAGED_IDENTITY_APP_ID   = < VALUE OF $ASSISTANT_APP_ID VARIABLE >
KUSTO_MANAGED_IDENTITY_SECRET   = < VALUE OF $ASSISTANT_APP_SECRET VARIABLE >
KUSTO_DATABASE_NAME             = < YOUR_DATABASE >
KUSTO_TABLE_NAME                = "aio_gold"
```

#### Start the Factory Assistant Application
- Start a terminal from the [directory](./artifacts/factory-assistant/)
- Execute the following command:
```bash
streamlit run .\frontend.py
```
- A web browser should appear with the following URL to access the application:
```
http://localhost:8501/
```
- You can now query the database using Natural Language  
**Note**: **no data** from the database is transmitted to the Large Language Model in Azure Open AI, but only the prompt, and the model will return the query to execute.  

![Factory Assistant User Interface](./artifacts/media/factory-assistant-ui.png "Factory Assistant User Interface")