### Part 3 - Configure the solution (Cloud part)

#### Start a new Microsoft Fabric trial

- Open the [Fabric homepage](https://app.fabric.microsoft.com/home) and select the Account manager.
- In the Account manager, select Free trial. If you don't see Free trial or Start trial or a Trial status, trials aren't allowed for your tenant.

#### Create database
- Select 'Real-Time Intelligence' from the [Fabric homepage](https://app.powerbi.com/home?experience=kusto).  
![fabric-home](./artifacts/media/fabric-home.png "fabric-home")
- Click on `Workspaces` > `New workspace` > type `Smart Factory` and click `Apply`
- Click `New` > `Eventhouse` > type `AIO` and click `Create`

#### Create tables with reference data
- Click on `Workspaces` > `Smart Factory`
- Select the database `AIO` (type: `KQL Database`)
- Create the table for `operators` dataset
1. Click on `Get data` > `Local file` > `New table` > type `operators`
2. Upload the file [operators.csv](./artifacts/templates/fabric/reference-datasets/operators.csv) > `Next`  
![fabric-upload](./artifacts/media/fabric_operators-1.png "fabric-upload")
3. Click on `First row is column header` > `Finish`, wait for the ingestion (status "Successfully ingested") and click `Close`
![fabric-columns](./artifacts/media/fabric_operators-2.png "fabric-columns")
- Create the table for `assets` dataset
1. Click on `Get data` > `Local file` > `New table` > type `assets`
2. Upload the file [assets.csv](./artifacts/templates/fabric/reference-datasets/assets.csv) > `Next`  
![fabric-upload2](./artifacts/media/fabric_assets-1.png "fabric-upload2")
3. Click on `First row is column header` > `Finish`, wait for the ingestion (status "Successfully ingested") and click `Close`
![fabric-columns2](./artifacts/media/fabric_assets-2.png "fabric-columns2")
- Create the table for `products` dataset
1. Click on `Get data` > `Local file` > `New table` > type `products`
2. Upload the file [products.csv](./artifacts/templates/fabric/reference-datasets/products.csv) > `Next`  
![fabric-upload3](./artifacts/media/fabric_products-1.png "fabric-upload3")
3. Click on `First row is column header` > `Finish`, wait for the ingestion (status "Successfully ingested") and click `Close`
![fabric-columns3](./artifacts/media/fabric_products-2.png "fabric-columns3")
**Note**: the reference datasets will enable data enrichment in the Cloud with datasets in the Cloud (operators, assets and products manufactured).  

#### Create table for silver data coming from Azure IoT Operations
- Select the query set `AIO_queryset`
- Add the following query:
    ```
    .create table aio_silver (
        Area: string,
        Cell: string,
        Downtime: double,
        EmployeeId: string,
        EnergyConsumption: double,
        Enterprise: string,
        GoodPartsCount: int64,
        IdealCycleTime: int64,
        Latitude: double,
        Line: string,
        Longitude: double,
        OperatingTime: int64,
        PlannedProductionTime: int64,
        ProductId: string,
        Shift: int64,
        ShiftHours: string,
        Site: string,
        Temperature: double,
        Timestamp: datetime,
        TotalPartsCount: int64,
        UNS: string,
        EventProcessedUtcTime: datetime,
        PartitionId: int64,
        EventEnqueuedUtcTime: datetime
    )
    ```
- Select the query portion and click `Run` to create the table `aio_silver`

#### Create update function to enrich data stream with reference datasets
- Add the following query:
    ```
    .create function with(folder = 'UpdatePolicyFunctions') EnrichWithReferenceData() {
        ["aio_silver"]
        | join kind=inner ['assets'] on Cell
        | join kind=inner ['products'] on Cell
        | join kind=inner ['operators'] on EmployeeId
        | project Timestamp, Enterprise, Site, Area, Line, Cell, SerialNumber, MaintenanceStatus, MaintenanceDate, ProductId, ProductName, EmployeeId, Operator, OperatorPhone, OperatorEmail, PlannedProductionTime, OperatingTime, TotalPartsCount, GoodPartsCount, IdealCycleTime, Downtime, EnergyConsumption, Temperature, Shift, ShiftHours, UNS, Latitude, Longitude
    }
    ```
- Select the query portion and click `Run` to create the function

#### Create table for gold data enriched with cloud reference datasets (directory and maintenance)
- Add the following query:
    ```
    .set aio_gold <| 
    EnrichWithReferenceData()
    ```
- Select the query portion and click `Run` to create the table `aio_gold`
- You should now see 5 tables:  
![fabric-tables](./artifacts/media/fabric-tables.png "fabric-tables")

#### Disable streaming ingestion
- Select the query set `AIO_queryset`
- Add the following query:
    ```
    .alter table aio_silver policy streamingingestion disable
    ```
- Select the query portion and click `Run`

#### Activate the update policy
- Add the following query:
    ```
    .alter table aio_gold policy update 
    @'[{ "IsEnabled": true, "Source": "aio_silver", "Query": "EnrichWithReferenceData()", "IsTransactional": false, "PropagateIngestionProperties": false}]'
    ```
- Select the query portion and click `Run`

#### Authorize the Factory Assistant to query the database
   - Retrieve the environment following variables you defined in [Part 1 - Provision resources (Edge and Cloud)](./INSTALL-1.md) ==> **Note(2)**:
     ```bash
     $ASSISTANT_APP_ID
     $TENANT
     ```
- Add the following query:
    ```
    .add database AIO viewers ('aadapp=<ASSISTANT_APP_ID>;<TENANT>') "Gen AI Factory Assistant"
    ```
- Select the query portion and click `Run`

#### Authorize the Factory Assistant to query the table
   - Retrieve the environment following variables you defined in [Part 1 - Provision resources (Edge and Cloud)](./INSTALL-1.md) ==> **Note(2)**:
     ```bash
     $ASSISTANT_APP_ID
     $TENANT
     ```
- Add the following query:
    ```
    .add table aio_gold admins ('aadapp=<ASSISTANT_APP_ID>;<TENANT>') "Gen AI Factory Assistant"
    ```
- Select the query portion and click `Run`

#### Create the event stream to ingest data from Azure Event Hub to a database in Microsoft Fabric
1. Configure event stream source
    - Click on `Workspaces` > `Smart Factory`
    - `New` > `Eventstream` > choose the name `aio_silver` and click `Create`
    - Click on `Add source` > `External sources` > `Azure Event Hubs` > `Connect`
    - Create new connection
    - Retrieve variables created in [Part 1 - Provision resources (Edge and Cloud)](./INSTALL-1.md) ==> **Note(1)**
    - `Event Hub namespace` > `$EVENTHUB_NAMESPACE` variable
    - `Event Hub` > `$EVENTHUB_NAME` variable
    - Choose a connection name
    - `Shared Access Key Name` > `$EVENTHUB_KEYNAME` variable
    - `Shared Access Key` > `$EVENTHUB_KEY` variable
    - Check that the connection name is correct
    - Tick the box `Test connection` and click `Connect`
    - `Consumer group` > type `fabric`
    - `Data format` > select `Json`
    - `Next` > `Add`

2. Configure event stream destination
    - Click on `New destination` > `KQL Database`
    - Tick the box `Event processing before ingestion`
    - Choose a `Destination name`
    - `Workspace` > select `Smart Factory`
    - `KQL Database` > select the database `AIO`
    - `Destination table` > select `aio_silver`
    - `Input data format` > `Json`
    - Tick the box `Activate streaming after adding data source`

3. Configure fields mapping
    - You may see 3 authoring errors
    - Click `Open event processor`
    - Set the field `EmployeeId` to `String` (click on the three dots)  
     ![fabric-eventstream-1-1](./artifacts/media/fabric_eventstream-1-1.png "fabric-eventstream-1-1")  
    - Set the field `ProductId` to `String` (same as above for `EmployeeId`)   
    - Set the field `Timestamp` to `DateTime` (click on the three dots)  
     ![fabric-eventstream-1-2](./artifacts/media/fabric_eventstream-1-2.png "fabric-eventstream-1-2")  
    - Ensure the fields are correctly configured as the picture below:  
     ![fabric-eventstream-1](./artifacts/media/fabric_eventstream-1.png "fabric-eventstream-1")
    - Click `Done`
    - Click `Add`    

        ![fabric-eventstream-2](./artifacts/media/fabric_eventstream-2.png "fabric-eventstream-2")

- ✅ **You can now continue to** > [Part 4 - Deploy and use the Generative AI Factory Assistant](./INSTALL-4.md)