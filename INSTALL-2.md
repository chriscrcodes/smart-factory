### Part 2 - Connect your Edge platform to Cloud platform
   - Login and execute the following commands on your Ubuntu Machine
   - Retrieve the environment following variables you defined in [Part 1 - Provision resources (Edge and Cloud)](./INSTALL-1.md) ==> **Note(2)**:
     ```bash
     $APP_ID
     $APP_SECRET
     $TENANT
     $OBJECT_ID
     $SUBSCRIPTION_ID
     $LOCATION
     $RESOURCE_GROUP
     $SCHEMA_REGISTRY_NAME
     $EVENTHUB_NAMESPACE
     $EVENTHUB_NAME
     ```
   - Create 1 environment variable to define the name of the cluster to connect to Azure Arc:
     ```bash
     export CLUSTER_NAME="<YOUR_CLUSTER_NAME>"
     ```
   - Connect to Azure (using the service principal created in [Part 1 - Provision resources (Edge and Cloud)](./INSTALL-1.md))
     ```bash
     az login --service-principal --username $APP_ID --password $APP_SECRET --tenant $TENANT
     ```
   - Set Azure Subscription context:
     ```bash
     az account set --subscription $SUBSCRIPTION_ID
     ```
   - Connect Kubernetes Cluster to Azure:
     ```bash
     az connectedk8s connect --name $CLUSTER_NAME --location $LOCATION --resource-group $RESOURCE_GROUP --subscription $SUBSCRIPTION_ID --enable-oidc-issuer --enable-workload-identity
     ```
   - Get the cluster's issuer URL
      ```bash
      az connectedk8s show --resource-group $RESOURCE_GROUP --name $CLUSTER_NAME --query oidcIssuerProfile.issuerUrl --output tsv
      ```  
      Save the output of this command to use in the next steps.
   - Create a K3s configuration file
      ```bash
      sudo nano /etc/rancher/k3s/config.yaml
      ```
   - Add the following content to the config.yaml file, replacing the <SERVICE_ACCOUNT_ISSUER> placeholder with your cluster's issuer URL.
      ```bash
      kube-apiserver-arg:
        - service-account-issuer=<SERVICE_ACCOUNT_ISSUER>
        - service-account-max-token-expiration=24h
      ```
   - Save the file and exit the text editor
   - Enable Custom Location support:
     ```bash
     az connectedk8s enable-features --name $CLUSTER_NAME --resource-group $RESOURCE_GROUP --custom-locations-oid $OBJECT_ID --features cluster-connect custom-locations
     ```
   - Restart K3s
      ```bash
      sudo systemctl restart k3s
      ```

#### Deploy and configure Azure IoT Operations

- Deploy Azure IoT Operations
   - Prepare your cluster with the dependencies that Azure IoT Operations requires:
     ```bash
     az iot ops init --cluster $CLUSTER_NAME --resource-group $RESOURCE_GROUP --sr-resource-id /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.DeviceRegistry/schemaRegistries/$SCHEMA_REGISTRY_NAME
     ```
   - Deploy Azure IoT Operations:
      ```bash
      az iot ops create --add-insecure-listener --name $CLUSTER_NAME-ops-instance --cluster $CLUSTER_NAME --resource-group $RESOURCE_GROUP
      ```

- Confirm Azure IoT Operations installation  
    - After the deployment is complete, use `az iot ops check` to evaluate IoT Operations service deployment for health, configuration, and usability. The check command can help you find problems in your deployment and configuration.  
    **Confirm post deployment checks are green.**
      ```bash
      az iot ops check
      ```

      ![az-iot-ops-check-post](./artifacts/media/az-iot-ops-check-post.png "az-iot-ops-check-post")

- Azure IoT Operations - Create Data flows
    - Download the Distributed State Store tool
    ```bash
    curl -O https://raw.githubusercontent.com/chriscrcodes/smart-factory/main/artifacts/templates/azure-iot-operations/dataflows/dss/dss_set
    ``` 
    - Set the file as executable
    ```bash
    chmod +x ./dss_set
    ```
    - Download the Operators Dataset
    ```bash
    curl -O https://raw.githubusercontent.com/chriscrcodes/smart-factory/main/artifacts/templates/azure-iot-operations/dataflows/dss/operators.json
    ``` 
    - Download the Products Dataset
    ```bash
    curl -O https://raw.githubusercontent.com/chriscrcodes/smart-factory/main/artifacts/templates/azure-iot-operations/dataflows/dss/products.json
    ``` 
    - ./dss_set --key operators --file "operators.json" --address localhost
    - ./dss_set --key products --file "products.json" --address localhost

#### Deploy Factory Simulator

- Login and execute the following commands on your Ubuntu Machine
- Factory Simulator
  ```bash
  kubectl apply -f https://raw.githubusercontent.com/chriscrcodes/smart-factory/main/artifacts/templates/k3s/pods/simulator/configuration.yaml
  kubectl apply -f https://raw.githubusercontent.com/chriscrcodes/smart-factory/main/artifacts/templates/k3s/pods/simulator/deployment.yaml
  ```
- Deploy the data flow (enrichment: bronze to silver)
  ```bash
  kubectl apply -f https://raw.githubusercontent.com/chriscrcodes/smart-factory/main/artifacts/templates/azure-iot-operations/dataflows/bronze-to-silver.yaml
  ```
- MQTT Client
  ```bash
  kubectl apply -f https://raw.githubusercontent.com/chriscrcodes/smart-factory/main/artifacts/templates/k3s/pods/mqtt-client/pod.yaml
  ```

#### Confirm factory simulator is running

  - Connect to the container running the MQTT client
    ```bash
    kubectl exec --stdin --tty mqtt-client -n azure-iot-operations -- sh
    ```
  - From within the container, launch the MQTT client:
    ```bash
    mqttui --broker mqtts://aio-mq-dmqtt-frontend:8883 --username '$sat' --password $(cat /var/run/secrets/tokens/mq-sat) --insecure
    ```
  - Confirm if the 2 following topics are present:
    - `LightningCars` (data coming from the Factory Simulator)
    - `Silver` (data coming from Azure IoT Operations Data Flows)  
    ![MQTT Broker Client](./artifacts/media/mqttui.png "MQTT Broker Client")
  - If the topics aren't shown, restart the Factory Simulator container:
    - Exit the MQTT client interface (type q)
    - Exit the MQTT client container (type exit and press Enter)
    - Identify the name of the Factory Simulator container:
      ```bash
      kubectl get pods -n azure-iot-operations
      ```
    - Restart the container
      ```bash
      kubectl delete pod -n azure-iot-operations iiot-simulator-factory-<suffix>
      ```

#### Deploy Cloud connector

  - Download the data flow
    ```bash
    curl -O https://raw.githubusercontent.com/chriscrcodes/smart-factory/main/artifacts/templates/azure-iot-operations/dataflows/bronze-to-silver.yaml
    ```
  - Modify file with the name of the event hub name space created in [Step 1](#step-1---provision-azure-resources) (`$EVENTHUB_NAMESPACE` variable):
    - ```bash
      sed -i 's/<EVENTHUB_NAMESPACE>/'"${EVENTHUB_NAMESPACE}"'/' bronze-to-silver.yaml
      ```

  - Modify file with the name of the event hub name created in [Step 1](#step-1---provision-azure-resources) (`$EVENTHUB` variable):
    - ```bash
      sed -i 's/<EVENTHUB>/'"${EVENTHUB}"'/' bronze-to-silver.yaml
      ```

  - Deploy the cloud connector
    - ```bash
      kubectl apply -f bronze-to-silver.yaml
      ```

  - Authorize the cluster to connect to the event hub
    - Locate the Azure Event Hub name space you created in [Azure Portal](https://portal.azure.com/)
    - `Access Control (IAM)` > `Add` > `Add role assignment`
    - `Azure Event Hubs Data Sender` > `Next`
    - Assign access to `User, group, or service principal`
    - `Select Members` > type `mq` to locate the `MQTT` extension used by Azure IoT Operations  
      (For example: `/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.Kubernetes/connectedClusters/xxx/providers/Microsoft.KubernetesConfiguration/extensions/mq-xxx`)
    - Repeat the same steps for the role `Azure Event Hubs Data Receiver`

  - Confirm data flowing from Edge to Cloud
    - Locate the Azure Event Hub name space you created in [Azure Portal](https://portal.azure.com/)
    - Data Explorer (preview) > select the event hub you created in [Step 1](#step-1---provision-azure-resources) (`$EVENTHUB_NAME` variable)
    - Click on `View events` > and select an event on the right to confirm data flow is operational  
    ![evh-messages](./artifacts/media/evh-messages.png "evh-messages")

  - ✅ **You can now continue to** > [Part 3 - Configure the solution (Cloud part)](./INSTALL-3.md)