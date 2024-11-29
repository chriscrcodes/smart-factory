#!/bin/bash

set -e

LOG_FILE="1_prepare-cloud.log"
exec > >(tee -a "$LOG_FILE") 2>&1

source aio-settings.txt

# Function to log and exit on error
handle_error() {
    local exit_code=$?
    local line_no=$1
    echo "Error on line $line_no. Exiting."
    exit $exit_code
}
trap 'handle_error $LINENO' ERR

# Register the required resource providers in your subscription
echo "--- Selecting Azure subscription..."
az account set --subscription "$SUBSCRIPTION_ID"

echo "--- Registering Azure subscription providers..."
az provider register --name "Microsoft.ExtendedLocation"
az provider register --name "Microsoft.Kubernetes"
az provider register --name "Microsoft.KubernetesConfiguration"
az provider register --name "Microsoft.IoTOperations"
az provider register --name "Microsoft.DeviceRegistry"
az provider register --name "Microsoft.SecretSyncController"

# Get the objectId of the Microsoft Entra ID application that the Azure Arc service uses in your tenant
echo "--- Retrieving Azure Arc Object Id..."
ARC_OBJECT_ID=$(az ad sp show --id bc313c14-388c-4e7d-a58e-70017303ee3b --query id --output tsv)
echo "ARC_OBJECT_ID=\"$ARC_OBJECT_ID\"" >> aio-settings.txt

# Create a resource group
echo "--- Creating Resource Group..."
AZ_RG=$(az group create --location "$LOCATION" --resource-group "$RESOURCE_GROUP" --subscription "$SUBSCRIPTION_ID")

# Create a service principal to manage Azure resources from the Edge cluster running Azure IoT Operations
echo "--- Creating Service Principal to manage Azure from Edge cluster..."
SP=$(az ad sp create-for-rbac --name "$SP_MANAGE_AZURE" --role Contributor --scopes /subscriptions/"$SUBSCRIPTION_ID"/resourceGroups/"$RESOURCE_GROUP")
APP_ID=$(echo "$SP" | jq -r .appId)
echo "APP_ID=\"$APP_ID\"" >> aio-settings.txt
APP_SECRET=$(echo "$SP" | jq -r .password)
echo "APP_SECRET=\"$APP_SECRET\"" >> aio-settings.txt
TENANT=$(echo "$SP" | jq -r .tenant)
echo "TENANT=\"$TENANT\"" >> aio-settings.txt

# Create a service principal for the GenAI Factory Assistant
echo "--- Creating Service Principal for GenAI Factory Assistant..."
SP2=$(az ad sp create-for-rbac --name "$SP_GENAI_ASSISTANT")
ASSISTANT_APP_ID=$(echo "$SP2" | jq -r .appId)
echo "ASSISTANT_APP_ID=\"$ASSISTANT_APP_ID\"" >> aio-settings.txt
ASSISTANT_APP_SECRET=$(echo "$SP2" | jq -r .password)
echo "ASSISTANT_APP_SECRET=\"$ASSISTANT_APP_SECRET\"" >> aio-settings.txt

# Create user assigned managed identity for secrets management in Azure IoT Operations
echo "--- Creating user assigned managed identity for secrets management in Azure IoT Operations..."
AZ_UMI1=$(az identity create --resource-group "$RESOURCE_GROUP" --name "$AIO_MANAGED_IDENTITY_SECRETS")
AIO_MANAGED_IDENTITY_SECRETS_ID=$(echo "$AZ_UMI1" | jq -r .id)
echo "AIO_MANAGED_IDENTITY_SECRETS_ID=\"$AIO_MANAGED_IDENTITY_SECRETS_ID\"" >> aio-settings.txt
AIO_MANAGED_IDENTITY_SECRETS_PRINCIPAL_ID=$(echo "$AZ_UMI1" | jq -r .principalId)
echo "AIO_MANAGED_IDENTITY_SECRETS_PRINCIPAL_ID=\"$AIO_MANAGED_IDENTITY_SECRETS_PRINCIPAL_ID\"" >> aio-settings.txt

# Create user assigned managed identity for Azure IoT Operations components
echo "--- Creating user assigned managed identity for Azure IoT Operations components..."
AZ_UMI2=$(az identity create --resource-group "$RESOURCE_GROUP" --name "$AIO_MANAGED_IDENTITY_COMPONENTS")
AIO_MANAGED_IDENTITY_COMPONENTS_ID=$(echo "$AZ_UMI2" | jq -r .id)
echo "AIO_MANAGED_IDENTITY_COMPONENTS_ID=\"$AIO_MANAGED_IDENTITY_COMPONENTS_ID\"" >> aio-settings.txt

# Create a key vault
echo "--- Creating key vault..."
AZ_KV=$(az keyvault create --enable-rbac-authorization false --name "$KEYVAULT_NAME" --resource-group "$RESOURCE_GROUP")
KEYVAULT_ID=$(echo "$AZ_KV" | jq -r .id)
echo "KEYVAULT_ID=\"$KEYVAULT_ID\"" >> aio-settings.txt

# Create a storage account
echo "--- Creating storage account..."
AZ_ST=$(az storage account create --name "$STORAGE_ACCOUNT_NAME" --resource-group "$RESOURCE_GROUP" --enable-hierarchical-namespace)
STORAGE_ACCOUNT_ID=$(echo "$AZ_ST" | jq -r .id)
echo "STORAGE_ACCOUNT_ID=\"$STORAGE_ACCOUNT_ID\"" >> aio-settings.txt

# Create an Event Hub name space
echo "--- Creating event hub namespace..."
AZ_EVHNS=$(az eventhubs namespace create --name "$EVENTHUB_NAMESPACE" --resource-group "$RESOURCE_GROUP" --location "$LOCATION")

# Create an Event Hub
echo "--- Creating event hub..."
AZ_EVH=$(az eventhubs eventhub create --name "$EVENTHUB_NAME" --resource-group "$RESOURCE_GROUP" --namespace-name "$EVENTHUB_NAMESPACE")
EVENTHUB_ID=$(echo "$AZ_EVH" | jq -r .id)
echo "EVENTHUB_ID=\"$EVENTHUB_ID\"" >> aio-settings.txt

# Create Event Hub key
echo "--- Creating event hub authorization rule..."
AZ_EVH_RULE=$(az eventhubs eventhub authorization-rule create --resource-group "$RESOURCE_GROUP" --namespace-name "$EVENTHUB_NAMESPACE" --eventhub-name "$EVENTHUB_NAME" --name Listen --rights Listen)
EVENTHUB_AUTH_RULE=$(az eventhubs eventhub authorization-rule keys list --resource-group "$RESOURCE_GROUP" --namespace-name "$EVENTHUB_NAMESPACE" --eventhub-name "$EVENTHUB_NAME" --name Listen)
EVENTHUB_KEY_NAME=$(echo "$EVENTHUB_AUTH_RULE" | jq -r .keyName)
echo "EVENTHUB_KEY_NAME=\"$EVENTHUB_KEY_NAME\"" >> aio-settings.txt
EVENTHUB_KEY=$(echo "$EVENTHUB_AUTH_RULE" | jq -r .primaryKey)
echo "EVENTHUB_KEY=\"$EVENTHUB_KEY\"" >> aio-settings.txt

# Install Azure IoT Operations extension for Azure CLI
echo "--- Installing Azure IoT Operations extension..."
AZ_CLI_EXT=$(az extension add --upgrade --name azure-iot-ops)

# Create Azure IoT Operations schema registry
echo "--- Creating schema registry..."
AZ_AIO_SR=$(az iot ops schema registry create --name "$SCHEMA_REGISTRY_NAME" --resource-group "$RESOURCE_GROUP" --registry-namespace "$SCHEMA_REGISTRY_NAMESPACE" --sa-resource-id "$STORAGE_ACCOUNT_ID")
SCHEMA_REGISTRY_ID=$(echo "$AZ_AIO_SR" | jq -r .id)
echo "SCHEMA_REGISTRY_ID=\"$SCHEMA_REGISTRY_ID\"" >> aio-settings.txt

# Create Azure Open AI service
AZ_AOAI=$(az cognitiveservices account create --name "$AZURE_OPENAI_NAME" --resource-group "$RESOURCE_GROUP" --location "eastus" --kind OpenAI --sku s0 --subscription $SUBSCRIPTION_ID)
AZURE_OPENAI_KEY=$(az cognitiveservices account keys list --name "$AZURE_OPENAI_NAME" --resource-group "$RESOURCE_GROUP" --query key1 --output tsv)
echo "AZURE_OPENAI_KEY=\"$AZURE_OPENAI_KEY\"" >> aio-settings.txt

# Deploy gpt4-o model
AZ_AOAI_MODEL=$(az cognitiveservices account deployment create --resource-group "$RESOURCE_GROUP" --name "$AZURE_OPENAI_NAME" --deployment-name "gpt-4o" --model-name "gpt-4o" --model-version "2024-08-06" --model-format OpenAI --sku-capacity 1 --sku-name "Standard")

# Add Role Assignments
AZ_ROLE_RBAC_ADMIN=$(az role assignment create --assignee "$APP_ID" --role "Role Based Access Control Administrator" --scope subscriptions/"$SUBSCRIPTION_ID"/resourceGroups/"$RESOURCE_GROUP")
AZ_ROLE_KV_SECRETS_OFFICER=$(az role assignment create --assignee "$AIO_MANAGED_IDENTITY_SECRETS_PRINCIPAL_ID" --role "Key Vault Secrets Officer" --scope "$KEYVAULT_ID")

echo "--- Ready for Part 2: Prepare Edge."