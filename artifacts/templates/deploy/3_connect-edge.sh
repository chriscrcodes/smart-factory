#!/bin/bash

source aio-settings.txt

# Connect to Azure subscription
echo "--- Connecting to Azure subscription..."
az logout
AZ_CONNECT=$(az login --service-principal --username $APP_ID --password $APP_SECRET --tenant $TENANT)
az account set --subscription $SUBSCRIPTION_ID

# Connect Edge cluster to Azure Arc
echo "--- Connecting Edge cluster to Azure Arc..."
az connectedk8s connect --name $AIO_CLUSTER_NAME --location $LOCATION --resource-group $RESOURCE_GROUP --subscription $SUBSCRIPTION_ID --enable-oidc-issuer --enable-workload-identity --disable-auto-upgrade

# Configure Arc custom location
echo "--- Configuring Arc custom location..."
AZ_ARC_ENABLE_CL=$(az connectedk8s enable-features --name $AIO_CLUSTER_NAME --resource-group $RESOURCE_GROUP --custom-locations-oid $ARC_OBJECT_ID --features cluster-connect custom-locations)

# Configure K3s
echo "--- Configuring K3s..."
OIDCISSUERPROFILE=$(az connectedk8s show --resource-group $RESOURCE_GROUP --name $AIO_CLUSTER_NAME --query oidcIssuerProfile.issuerUrl --output tsv)
sudo touch /etc/rancher/k3s/config.yaml
sudo bash -c 'cat <<EOL > /etc/rancher/k3s/config.yaml
kube-apiserver-arg:
 - service-account-issuer=<SERVICE_ACCOUNT_ISSUER>
 - service-account-max-token-expiration=24h
EOL'
sudo sed -i 's|<SERVICE_ACCOUNT_ISSUER>|'"${OIDCISSUERPROFILE}"'|g' /etc/rancher/k3s/config.yaml
sudo systemctl restart k3s

# Initialize Azure IoT Operations
echo "--- Initializing Azure IoT Operations foundations installation..."
az iot ops init --subscription $SUBSCRIPTION_ID --cluster $AIO_CLUSTER_NAME --resource-group $RESOURCE_GROUP

# Install Azure IoT Operations
echo "--- Installing Azure IoT Operations..."
az iot ops create --add-insecure-listener --kubernetes-distro K3s --name $AIO_CLUSTER_NAME-ops-instance --cluster $AIO_CLUSTER_NAME --resource-group $RESOURCE_GROUP --sr-resource-id $SCHEMA_REGISTRY_ID --broker-frontend-replicas 1 --broker-frontend-workers 1 --broker-backend-part 1 --broker-backend-workers 1 --broker-backend-rf 2 --broker-mem-profile Low

# Enable secret sync
echo "--- Enabling secret sync..."
$AZ_AIO_SYNC_SECRETS=$(az iot ops secretsync enable --instance $AIO_CLUSTER_NAME-ops-instance --resource-group $RESOURCE_GROUP --mi-user-assigned $AIO_MANAGED_IDENTITY_SECRETS_ID --kv-resource-id $KEYVAULT_ID)

# Enable cloud connections sync
echo "--- Enabling cloud connections sync..."
$AZ_AIO_SYNC_COMPONENTS=$(az iot ops identity assign --name $AIO_CLUSTER_NAME-ops-instance --resource-group $RESOURCE_GROUP --mi-user-assigned $AIO_MANAGED_IDENTITY_COMPONENTS_ID)

# Authorize Azure IoT Operations to send messages to Event Hub
echo "--- Authorizing Azure IoT Operations to send messages to Event Hub..."
AZ_AIO_EXT=$(az k8s-extension list --cluster-name $AIO_CLUSTER_NAME --resource-group $RESOURCE_GROUP --cluster-type connectedClusters --query "[?extensionType=='microsoft.iotoperations'].identity.principalId" --output tsv)
AZ_ROLE_EVH_DATA_SENDER=$(az role assignment create --assignee $AZ_AIO_EXT --role "Azure Event Hubs Data Sender" --scope $EVENTHUB_ID)

echo "--- Ready for Part 4: Configure Edge."