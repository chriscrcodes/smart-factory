# 🗣️ Talk to your factory - implementation guide

## Introduction
🤖 Smart Factory demo, enhanced by Generative AI.  
🏭 See how the Smart Factory leverages Generative AI to optimize its operations!  
🔍 Real-time ingestion and processing of operations data (OT): operators, manufactured products, and machine maintenance schedules.  
🗣️ Data processing: Edge and Cloud, with a Semantic Kernel to power the Factory Assistant, for smarter interactions.  

[Video on the IoT Show](https://youtu.be/-AxWwJU_G_U?feature=shared) (demo starts at [19:54](https://youtu.be/-AxWwJU_G_U?feature=shared&t=1194)).

### Key features and benefits

- **Data Processing**: Data structure following a **Medallion Architecture**, with the goal of incrementally and progressively improving the structure and quality of data as it flows through each layer of the architecture.  
From `Bronze` (Edge: MQTT Data Simulator) ⇒ `Silver` (Edge: Azure IoT Operations) ⇒ `Gold` (Cloud: Microsoft Fabric) layer tables.

- **Natural Language Processing (NLP)**: a Smart Assistant, enhanced by Generative AI, empowers operators, so they can ask complex questions about machine operations, staff, production quality, as if they were speaking to a human expert in the Factory.

## Architecture

### Solution architecture overview

![Architecture Diagram](./artifacts/media/architecture-overview.png "Solution Overview")

### Factory simulation

![Factory Simulation](./artifacts/media/simulation.png "Factory Simulation")

### Key components

![Data Diagram](./artifacts/media/key-components.png "Data Diagram")

1. **Factory Simulator**  
    Simulates data coming from several factories: Berlin, Austin, Buffalo, Shanghai.  
    Factory simulator is publishing data to an Message Queuing Telemetry Transport (MQTT) broker topic based on the international standard from the International Society of Automation known as 'ISA-95' with the following format: Enterprise/Site/Area/Line/Cell.  
    Industrial machines involved in the process are 'Cells.'  

2. **Azure IoT Operations**  
    Processes data at Edge: normalize, contextualize, enrich with Edge reference datasets (Operators and Products).

3. **Azure Event Hub**  
    Data ingestion in Azure.     
    
4. **Microsoft Fabric**  
    Processes data in Azure: materialize data as a Table, enrich with Cloud reference datasets (Operators, Assets and Products).

5. **Generative AI Factory Assistant**  
    Introducing a custom Large Language Model (LLM) Factory Assistant, based on OpenAI model 'GPT-4o', that enables natural language communication with the factory. This assistant simplifies the process of retrieving information from various systems and databases.

### Communication flow

![Factory Assistant Communication Flow](./artifacts/media/factory-assistant-communication-flow.png "Factory Assistant Communication Flow")

1. **User Prompt**: user asks a question to the Factory Assistant.  
    The graphical user interface is based on the open-source framework `Streamlit`.
2. **Custom Large Language Model (LLM)**: analyzes the prompt and generate the corresponding query to be executed to the database in Microsoft Fabric.  
3. **Semantic Kernel**: execute query and return results (Python application).

#### Creating complex queries from natural language prompt - Example
![Factory Assistant Prompt](./artifacts/media/factory-assistant-prompt.png "Factory Assistant Prompt")

1. **Prompt**: _"I want to calculate the yield for each site this month, based on the total units produced and the good units produced. Display good units, total units and sort the results by yield percentage and site."_
2. **Generative AI Model**: analyzes the prompt and generate the corresponding query to be executed to the database.  

    > **IMPORTANT**: No actual data from the database is transmitted to the Large Language Model; only the prompt and the database schema are shared. The LLM will generate the query to be executed against the database, but it won't execute the query itself.  

    Example query generated in `KQL (Kusto Query Language)`:  
    ```
    aio_gold
    | where Timestamp >= startofmonth(now())
    | summarize GoodUnits = sum(GoodPartsCount), TotalUnits = sum(TotalPartsCount) by Site
    | extend YieldPercentage = (GoodUnits / TotalUnits) * 100
    | project Site, GoodUnits, TotalUnits, YieldPercentage
    | order by YieldPercentage desc, Site
    | top 100 by YieldPercentage desc
    ```  

3. **Back-end application `(Python)`**: queries the database to retrieve results.  

4. **Front-end application `(Streamlit)`**: provides the user interface.

## Prerequisites
Microsoft Documentation: [Azure IoT Operations prerequisites](https://learn.microsoft.com/en-us/azure/iot-operations/deploy-iot-ops/howto-prepare-cluster?tabs=ubuntu)

> **WARNING**: Azure IoT Operations is currently in preview.  
You shouldn't use this preview software in production environments.

### Hardware requirements

- **Resources**: 
    - CPU: `4 vCPU`
    - Memory: `16GB`
    - Storage: `30GB`

- **Operating System**: the solution requires a Linux-based system, specifically a VM or physical machine running `Linux Ubuntu 22.04`. This system will perform as an Edge server, handling queries directly from the production line and interfacing with other operational systems.

### Software requirements

 - [`K3s`](https://k3s.io/) Lightweight Kubernetes. Easy to install, half the memory, all in a binary of less than 100 MB.
 - [`python >=v3.10`](https://www.python.org/) Programming Language
 - [`curl`](https://curl.se/) command line tool that developers use to transfer data to and from a server.
 - [`nano`](https://www.nano-editor.org/) text editor.
 - [`jq`](https://github.com/jqlang/jq) command-line JSON processor.
 - [`Azure CLI`](https://learn.microsoft.com/en-us/cli/azure/) the Azure command-line interface.

### Cloud services requirements

 - Azure Subscription (with Contributor rights)
    - Resource Group
    - Storage Account
    - Event Hub
    - Azure Open AI Service
    - _Optional_: Virtual Machine (if you want to test everything in Azure Cloud)
 - Microsoft Fabric Tenant (you can try it for free [here](https://www.microsoft.com/en-us/microsoft-fabric/getting-started?msockid=27cd43526f4e6b2a1fa857d06e486a3c))

## Demo

![Factory Assistant User Interface](./artifacts/media/demo-video.gif "Factory Assistant User Interface")

## Solution build steps

### 1. [Provision resources (Edge and Cloud)](./INSTALL-1.md)
### 2. [Connect your Edge platform to Cloud platform](./INSTALL-2.md)
### 3. [Configure the solution (Cloud part)](./INSTALL-3.md)
### 4. [Deploy and use the Generative AI Factory Assistant](./INSTALL-4.md)