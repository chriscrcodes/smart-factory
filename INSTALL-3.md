### Part 3 - Configure the solution (Cloud part)

#### Start a new Microsoft Fabric trial

- Open the [Fabric homepage](https://app.fabric.microsoft.com/home) and select the Account manager.
- In the Account manager, select Free trial. If you don't see Free trial or Start trial or a Trial status, trials aren't allowed for your tenant.

#### Create database
- Select 'Real-Time Intelligence' from the [Fabric homepage](https://app.fabric.microsoft.com/home).  
![fabric-home](./artifacts/media/fabric-home.png "fabric-home")
- Click on `Workspaces` > `My workspace`
- `New` > `Eventhouse` > choose a name and click `Create`
- It will create a new Database

#### Create tables with reference data
- Click on `Workspaces` > `My workspace`
- Select the database created (type: `KQL Database`)
- Create the table for directory dataset
1. Click on `Get data` > `Local file` > `New table` > type `directory`
2. Upload the file [directory-data.csv](./artifacts/templates/fabric/reference-datasets/directory-data.csv) > `Next`  
![fabric-upload](./artifacts/media/fabric1.png "fabric-upload")
3. Click on `First row is column header` > `Finish` and `Close`
![fabric-columns](./artifacts/media/fabric2.png "fabric-columns")
- Repeat the same steps for maintenance dataset
1. Click on `Get data` > `Local file` > `New table` > type `maintenance`
2. Upload the file [maintenance-data.csv](./artifacts/templates/fabric/reference-datasets/maintenance-data.csv) > `Next`  
![fabric-upload2](./artifacts/media/fabric3.png "fabric-upload2")
3. Click on `First row is column header` > `Finish` and `Close`
![fabric-columns2](./artifacts/media/fabric4.png "fabric-columns2")
**Note**: the reference datasets will enable data enrichment in the Cloud with datasets in the Cloud (ERP Cloud scenario with Company Directory Information in the Cloud).  

#### Create table for silver data coming from Azure IoT Operations
- Click on `Workspaces` > `My workspace`
- Select the query set (type: `KQL Queryset`)
- Clear the text in the query set and replace by the following query:
```
.create table aio_silver (
Timestamp: datetime,
Enterprise: string,
Site: string,
Area:string,
Line: string,
Cell:string,
LastCycleTime: real,
TotalOperatingTime: real,
PlannedProductionTime: real,
Temperature: real,
Humidity: real,
Pressure: real,
Speed: real,
Vibration: real,
Energy: real,
Product: string,
Operator: string,
Shift: real,
UnitsProduced: real,
GoodUnitsProduced: real)
```
- Click `Run` to create the table `aio_silver`

#### Create update function to enrich data stream with reference datasets
- Clear the text in the query set and replace by the following query:
```
.create function with(folder = 'UpdatePolicyFunctions') EnrichWithReferenceData() {
    ["aio_silver"]
    | join kind=innerunique ['maintenance'] on Cell
    | join kind=innerunique ['directory'] on Operator
    | project Timestamp, Enterprise, Site, Area, Line, Cell, SerialNumber, MaintenanceStatus, MaintenanceDate, Operator, OperatorPhone, OperatorEmail, Shift, Product, LastCycleTime, TotalOperatingTime, PlannedProductionTime, UnitsProduced, GoodUnitsProduced, Energy, Temperature, Humidity, Pressure, Vibration, Speed
}
```
- Click `Run` to create the function

#### Create table for gold data enriched with cloud reference datasets (directory and maintenance)
- Clear the text in the query set and replace by the following query:
```
.set aio_gold <| 
   EnrichWithReferenceData()
   | limit 0
```
- Click `Run` to create the table `aio_gold`
- You should now see 4 tables:  
![fabric-tables](./artifacts/media/fabric5.png "fabric-tables")

#### Activate the update policy
- Clear the text in the query set and replace by the following query:
```
.alter table aio_silver policy streamingingestion disable

.alter table aio_gold policy update 
@'[{ "IsEnabled": true, "Source": "aio_silver", "Query": "EnrichWithReferenceData()", "IsTransactional": false, "PropagateIngestionProperties": false}]'

.alter table aio_silver policy streamingingestion enable
```
- Click `Run`

#### Authorize the Factory Assistant to query the database
- Clear the text in the query set and replace by the following query:
```
.add database <YOUR_DATABASE> readers ('aadapp=8c6bfbc1-031a-44bb-b944-b5ae1d870f0a;67bce274-9726-4089-965b-c4e6ee267113') "Gen AI Factory Assistant"
.add table aio_gold readers ('aadapp=8c6bfbc1-031a-44bb-b944-b5ae1d870f0a;67bce274-9726-4089-965b-c4e6ee267113') "Gen AI Factory Assistant"
```
- Click `Run`

#### Create the event stream to ingest data from event hub to a database
- Click on `Workspaces` > `My workspace`
- `New` > `Eventstream` > choose a name and click `Create`
- Click on `New source` > `Azure Event Hubs`
- Choose a `Source name`
- `Cloud connection` > `Create new`
- Retrieve variables created in [Part 1 - Provision resources (Edge and Cloud)](./INSTALL-1.md) ==> **Note(1)**
- `Event Hub namespace` > `$EVENTHUB_NAMESPACE` variable
- `Event Hub` > `$EVENTHUB_NAME` variable
- `Shared Access Key Name` > `$EVENTHUB_KEYNAME` variable
- `Shared Access Key` > `$EVENTHUB_KEY` variable
- Click `Create`
- `Consumer group` > `Create new` > type `Fabric` and click `Done`
- `Data format` > select `Json`
- Tick the box `Activate streaming after adding data source` and click `Add`
- Click on `New destination` > `KQL Database`
- Select `Direct ingestion`
- Choose a `Destination name`
- `Workspace` > select `My workspace`
- `KQL Database` > select your database

- **You can now continue to** > [Part 4 - Deploy and use the Generative AI Factory Assistant](./INSTALL-4.md)