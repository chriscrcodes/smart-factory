### Part 1 - Provision resources (Edge and Cloud)

#### Prepare and provision Cloud platform
   - From your computer, open up the [Azure Portal](https://portal.azure.com/)
   - Use the [Azure Cloud Shell (**Bash**)](https://learn.microsoft.com/en-us/azure/Cloud-shell/get-started/ephemeral?tabs=azurecli#start-Cloud-shell)
   - Set Environment Variables for services to create in Azure:
     ```bash
     export SUBSCRIPTION_ID="<YOUR_SUBSCRIPTION_ID>"
     export LOCATION="<YOUR_REGION>"
     export RESOURCE_GROUP="<YOUR_RESOURCE_GROUP>"
     export KEYVAULT_NAME="<YOUR_KEYVAULT_NAME>"
     export EVENTHUB_NAMESPACE="<YOUR_EVENTHUB_NAMESPACE>"
     export EVENTHUB_NAME="<YOUR_EVENTHUB_NAME>"
     export AZURE_OPENAI_NAME="<YOUR_AZURE_OPENAI_NAME>"
     ```
     **Note(1)**: **keep a note of the environment variables for future use**.
   - Set Azure Subscription context:
     ```bash
     az account set -s $SUBSCRIPTION_ID
     ```
   - Create a service principal (service account) to manage Azure:
     ```bash
     SPN=$(az ad sp create-for-rbac -n AIO_SP_Contrib --role Contributor --scopes /subscriptions/$SUBSCRIPTION_ID)
     ```
      **Note(2)**: create 3 variables with: `appId`, `password` and `tenant`, from the output of the command, and **keep a note of them for future use**.
     ```bash
     export APP_ID=$(echo $SPN | jq -r .appId)
     export APP_SECRET=$(echo $SPN | jq -r .password)
     export TENANT=$(echo $SPN | jq -r .tenant)
     ```
   - Create a service principal (service account) for the Factory Assistant:
     ```bash
     SPN2=$(az ad sp create-for-rbac -n GenAI_Factory_Assistant)
     ```
      **Note(2)**: create 3 variables with: `appId`, `password` and `tenant`, from the output of the command, and **keep a note of them for future use**.
     ```bash
     export ASSISTANT_APP_ID=$(echo $SPN2 | jq -r .appId)
     export ASSISTANT_APP_SECRET=$(echo $SPN2 | jq -r .password)
     export ASSISTANT_TENANT=$(echo $SPN2 | jq -r .tenant)
     ```
   - Get `objectId` of `Microsoft Entra ID` application and create 1 variable:
     ```bash
     export OBJECT_ID=$(az ad sp show --id bc313c14-388c-4e7d-a58e-70017303ee3b --query id -o tsv)
     ```
   - Register required Resource Providers (execute this step only once per subscription):
     ```bash
     az provider register -n "Microsoft.ExtendedLocation"
     az provider register -n "Microsoft.Kubernetes"
     az provider register -n "Microsoft.KubernetesConfiguration"
     az provider register -n "Microsoft.IoTOperationsOrchestrator"
     az provider register -n "Microsoft.IoTOperations"
     az provider register -n "Microsoft.DeviceRegistry"
     ```
   - Create a Resource Group:
     ```bash
     az group create --location $LOCATION --resource-group $RESOURCE_GROUP --subscription $SUBSCRIPTION_ID
     ```
   - Create an Azure Key Vault:
     ```bash
     az keyvault create --enable-rbac-authorization false --name $KEYVAULT_NAME --resource-group $RESOURCE_GROUP
     ```
   - Create an Event Hub name space:
     ```bash
     az eventhubs namespace create --name $EVENTHUB_NAMESPACE --resource-group $RESOURCE_GROUP --location $LOCATION
     ```
   - Create an Event Hub:
     ```bash
     az eventhubs eventhub create --name $EVENTHUB_NAME --resource-group $RESOURCE_GROUP --namespace-name $EVENTHUB_NAMESPACE
     ```
   - Retrieve the Event Hub Connection String and create 2 variables:
     ```bash
     EVENTHUB_INFO=$(az eventhubs namespace authorization-rule keys list --resource-group $RESOURCE_GROUP --namespace-name $EVENTHUB_NAMESPACE --name RootManageSharedAccessKey)
     export EVENTHUB_KEYNAME=$(echo $EVENTHUB_INFO | jq -r .keyName)
     export EVENTHUB_KEY=$(echo $EVENTHUB_INFO | jq -r .primaryKey)
     ```
   - Create an Azure OpenAI resource:
     ```bash
     az cognitiveservices account create --name $AZURE_OPENAI_NAME --resource-group $RESOURCE_GROUP --location eastus --kind OpenAI --sku s0 --subscription $SUBSCRIPTION_ID
     ```
   - Retrieve the Azure OpenAI resource keys and create 1 variable:
     ```bash
     export AZURE_OPENAI_KEY=$(az cognitiveservices account keys list --name $AZURE_OPENAI_NAME --resource-group $RESOURCE_GROUP --query key1 -o tsv)
     ```
#### Prepare and provision Edge platform

- Hardware requirements
  - **Resources**: 
      - CPU: `4 vCPU`
      - Memory: `16GB`
      - Storage: `30GB`

  - **Operating System**: the solution requires a Linux-based system, specifically a VM or physical machine running `Linux Ubuntu 22.04`. This system will perform as an Edge server, handling queries directly from the production line and interfacing with other operational systems.

- Option A (Virtual Machine in Azure)
   - If you want to use a Virtual Machine in Azure, you can deploy it using the Deploy button below:  
      [![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fchriscrcodes%2Fsmart-factory%2Frefs%2Fheads%2Fmain%2Fartifacts%2Ftemplates%2Fvm%2Fazuredeploy.json)
      - `Review + create` > `Create`

      **Note**: `Standard_D4s_v3` is the recommended size for the Azure VM.

- Option B (your own Industrial PC or Virtual Machine)
  - Install `Linux Ubuntu 22.04`

- Prepare a K3s Kubernetes Cluster on Ubuntu (login and execute the following commands on your Ubuntu Machine)
   - Install `curl` and `nano`:
     ```bash
     sudo apt update
     sudo apt install curl nano jq -y
     ```
- Install K3s
   - Run the `K3s installation script`:
     ```bash
     curl -sfL https://get.k3s.io | sh -
     ```
   - Create a `K3s configuration` file in `.kube/config`:
     ```bash
     mkdir ~/.kube
     sudo KUBECONFIG=~/.kube/config:/etc/rancher/k3s/k3s.yaml kubectl config view --flatten > ~/.kube/merged
     mv ~/.kube/merged ~/.kube/config
     chmod  0600 ~/.kube/config
     export KUBECONFIG=~/.kube/config
     kubectl config use-context default
     ```
   - Increase user watch/instance limits:
     ```bash
     echo fs.inotify.max_user_instances=8192 | sudo tee -a /etc/sysctl.conf
     echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
     sudo sysctl -p
     ```
   - Increase file descriptor limit:
     ```bash
     echo fs.file-max = 100000 | sudo tee -a /etc/sysctl.conf
     sudo sysctl -p
     ```
- Check k3s installation
  ```bash
  kubectl get node
  ```
- Install Azure prerequisites
  - Install `Azure CLI`:
    ```bash
    curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
    ```
  - Install `Azure arc extension`:
    ```bash
    az extension add --allow-preview true --name connectedk8s
    ```
  - Install `Azure IoT Operations extension` (v0.5.1b1, to be able to use the Data Processor component):
    ```bash
    az extension add --allow-preview true --name azure-iot-ops --version 0.5.1b1
    ```
- **You can now continue to** > [Part 2 - Connect your Edge platform to Cloud platform](./INSTALL-2.md)