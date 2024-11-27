#!/bin/bash

source aio-settings.txt

# Download the Distributed State Store tool
curl -O https://raw.githubusercontent.com/chriscrcodes/talk-to-your-factory/main/artifacts/templates/azure-iot-operations/dataflows/dss/dss_set

# Set the file as executable
chmod +x ./dss_set

# Download the Operators Dataset
curl -O https://raw.githubusercontent.com/chriscrcodes/talk-to-your-factory/main/artifacts/templates/azure-iot-operations/dataflows/dss/operators.json

# Download the Products Dataset
curl -O https://raw.githubusercontent.com/chriscrcodes/talk-to-your-factory/main/artifacts/templates/azure-iot-operations/dataflows/dss/products.json

# Download the data flow  
curl -O https://raw.githubusercontent.com/chriscrcodes/talk-to-your-factory/main/artifacts/templates/azure-iot-operations/dataflows/silver-to-cloud.yaml

# Modify file with the name of the event hub namespace :
sed -i 's/<EVENTHUB_NAMESPACE>/'"${EVENTHUB_NAMESPACE}"'/' silver-to-cloud.yaml

# Modify file with the name of the event hub name:
sed -i 's/<EVENTHUB>/'"${EVENTHUB_NAME}"'/' silver-to-cloud.yaml

# Import the operators dataset in the Distributed State Store
./dss_set --key operators --file "operators.json" --address localhost

# Import the products dataset in the Distributed State Store
./dss_set --key products --file "products.json" --address localhost

# Deploy Factory Simulator
kubectl apply -f https://raw.githubusercontent.com/chriscrcodes/talk-to-your-factory/main/artifacts/templates/k3s/pods/simulator/configuration.yaml
kubectl apply -f https://raw.githubusercontent.com/chriscrcodes/talk-to-your-factory/main/artifacts/templates/k3s/pods/simulator/deployment.yaml
kubectl apply -f https://raw.githubusercontent.com/chriscrcodes/talk-to-your-factory/main/artifacts/templates/azure-iot-operations/dataflows/bronze-to-silver.yaml

# Deploy the cloud connector
kubectl apply -f silver-to-cloud.yaml