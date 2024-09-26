### Part 1 - Provision resources (Edge and Cloud)

#### Prepare and provision Cloud platform
   - Use the [Azure Cloud Shell (Bash)](https://learn.microsoft.com/en-us/azure/Cloud-shell/get-started/ephemeral?tabs=azurecli#start-Cloud-shell) to provision resources in Azure Cloud 
   - Set Environment Variables:
     ```bash
     export SUBSCRIPTION_ID=<YOUR_SUBSCRIPTION_ID>
     export LOCATION=<YOUR_REGION>
     export RESOURCE_GROUP=<YOUR_RESOURCE_GROUP>
     export KEYVAULT_NAME=<YOUR_KEYVAULT_NAME>
     export EVENTHUB_NAMESPACE=<YOUR_EVENTHUB_NAMESPACE>
     export EVENTHUB_NAME=<YOUR_EVENTHUB_NAME>
     export AZURE_OPENAI_NAME=<AZURE_OPENAI_NAME>
     ```
   - Set Azure Subscription context:
     ```bash
     az account set -s $SUBSCRIPTION_ID
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
   - Create an Azure OpenAI resource:
     ```bash
     az cognitiveservices account create --name $AZURE_OPENAI_NAME --resource-group $RESOURCE_GROUP --location $LOCATION --kind OpenAI --sku s0 --subscription $SUBSCRIPTION_ID
     ```
   - If you want to use a Virtual Machine in Azure, you can deploy it using the Deploy button below:  
      [![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fchriscrcodes%2Fsmart-factory%2Frefs%2Fheads%2Fmain%2Fartifacts%2Ftemplates%2Fvm%2Fazuredeploy.json)

      **Note**: `Standard_D4s_v3` is the recommended size for the Azure VM.

#### Prepare and provision Edge platform

- Prepare a K3s Kubernetes Cluster on Ubuntu (login and execute the following commands on your Ubuntu Machine)
   - Install `curl` and `nano`:
     ```bash
     sudo apt update
     sudo apt install curl nano -y
     ```
   - Install `Azure CLI`:
     ```bash
     curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
     ```
   - Install `Azure arc extension`:
    ```bash
     az extension add --upgrade --name connectedk8s
     ```
   - Install `Azure IoT Operations extension` (v0.5.1b1, to be able to use the Data Processor component):
     ```bash
     az extension add --name azure-iot-ops --version 0.5.1b1
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