Sure! Here's the documentation in **Markdown** format for the MQTT Data Simulator:

---

# MQTT Data Simulator

This project simulates publishing data to an MQTT broker using Python. It reads a configuration file that defines the topics, tags, and other settings, generates simulated data, and publishes it to MQTT topics at regular intervals.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
  - [Key Components](#key-components)
  - [Data Generation](#data-generation)
  - [Publishing Data](#publishing-data)
- [Running the Simulator](#running-the-simulator)
- [Customizing the Simulator](#customizing-the-simulator)
- [License](#license)

---

## Overview

The **MQTT Data Simulator** is designed to simulate data publishing to an MQTT broker. It generates random or predefined data based on a JSON configuration file, then sends the data to MQTT topics at a specified interval.

This simulator can be useful for testing IoT applications, MQTT brokers, or any system that relies on MQTT messaging.

---

## Features

- **MQTT Protocol v5** support.
- Simulated data generation based on mean and deviation or constant values.
- TLS support for secure connections.
- Supports multiple data types, including `int`, `float`, `boolean`, `datetime`, `string`, and `guid`.
- Customizable through a JSON configuration file.
- Real-time data publishing with timestamps in UTC.

---

## Prerequisites

Before you can run the simulator, make sure you have the following installed:

- **Python 3.x** (Tested with Python 3.7+)
- **Paho MQTT Python Client** (`paho-mqtt`)
- **Colorama** (for terminal colors)
- **PyFiglet** (for the ASCII banner)

Install the necessary Python dependencies:

```bash
pip install paho-mqtt colorama pyfiglet
```

---

## Installation

1. **Clone the repository** or copy the script to your local machine:

   ```bash
   git clone https://github.com/your-repository/mqtt-data-simulator.git
   cd mqtt-data-simulator
   ```

2. **Install the dependencies** as mentioned in the [Prerequisites](#prerequisites) section.

3. Place your configuration file (`mqtt_config.json`) in the same directory as the script.

---

## Configuration

The MQTT Data Simulator reads its configuration from a JSON file. Below is a sample configuration structure:

```json
{
    "mqtt_broker": {
        "address": "broker.hivemq.com",
        "port": 1883,
        "username": "your_username",
        "password": "your_password",
        "use_tls": false
    },
    "root_topic": "LightningCars",
    "topics": [
        {
            "topics": [
                "LightningCars/Berlin/Stamping/Line1/1A2B3C"
            ],
            "tags": [
                { "tag": "GoodPartsCount", "type": "int", "mean": 95, "deviation": 5 },
                { "tag": "ScrapPartsCount", "type": "int", "mean": 5, "deviation": 1 },
                { "tag": "PlannedProductionTime", "type": "float", "mean": 2400, "deviation": 0 },
                { "tag": "MachineStatus", "type": "boolean" },
                { "tag": "QualityStatus", "type": "boolean" },
                { "tag": "Timestamp", "type": "datetime" }
            ]
        }
    ],
    "publish_interval": 5
}
```

### Configuration Fields

- **mqtt_broker**: Contains information to connect to the MQTT broker.
  - `address`: The MQTT broker address (e.g., `broker.hivemq.com`).
  - `port`: Port for MQTT (default: `1883`).
  - `username` & `password`: Optional credentials for authentication.
  - `use_tls`: Boolean to indicate if TLS should be used.
  
- **root_topic**: The base topic to which subtopics will be appended.
  
- **topics**: A list of topics and corresponding data tags to publish.
  - `topics`: The list of subtopics to append to the root topic.
  - `tags`: A list of data tags to generate for each topic. Each tag specifies:
    - `tag`: The name of the data field.
    - `type`: The data type (`int`, `float`, `boolean`, `datetime`, `string`, `guid`).
    - `mean` & `deviation`: The mean and deviation (for numerical data).
    - `constant`: A constant value if no randomness is needed.

- **publish_interval**: Time in seconds between data publications (default: `5` seconds).

---

## How It Works

The simulator reads the configuration file, connects to the MQTT broker, and repeatedly generates and publishes data to the specified MQTT topics.

### Key Components

- **load_config**: Loads the configuration from the JSON file.
- **generate_data**: Generates random or predefined data for each tag based on its type and mean/deviation.
- **publish_data**: Publishes the generated data to the MQTT topics.
- **connect_mqtt**: Connects to the specified MQTT broker using the provided settings (TLS, credentials, etc.).

### Data Generation

Data is generated based on the tag configuration:
- If a **constant** value is defined, it is used directly.
- For numerical data (`int`, `float`, `double`), a value is randomly generated within a range defined by `mean ± deviation`.
- **Boolean** data is randomly chosen as either `True` or `False`.
- **Datetime** data is generated as the current UTC timestamp.
- **String** data is generated randomly (e.g., `SampleString_45`).
- **GUID** data is generated as a unique UUID.

### Publishing Data

The simulator constructs the full MQTT topic by appending subtopics to the `root_topic` and adds a **Timestamp** and **Location** to the data payload. The payload is then published as a JSON object to the MQTT broker.

---

## Running the Simulator

1. Place the `mqtt_config.json` configuration file in the same directory as the Python script.
2. Run the script:

   ```bash
   python mqtt_data_simulator.py
   ```

3. The simulator will start publishing data based on the configuration, and you will see output like this:

   ```
   2024-10-09T13:00:00Z - Published data to topic 'LightningCars/Berlin/Stamping/Line1/1A2B3C': {'GoodPartsCount': 95, 'ScrapPartsCount': 5, 'PlannedProductionTime': 2400, 'MachineStatus': True, 'QualityStatus': True, 'Timestamp': '2024-10-09T13:00:00Z', 'Location': 'LightningCars/Berlin/Stamping/Line1/1A2B3C'}
   ```

---

## Customizing the Simulator

You can customize the simulator by modifying the **mqtt_config.json** file to suit your specific requirements. Key areas for customization include:
- **Adding new topics**: Add more topics under the `topics` section.
- **Adjusting tag values**: Modify the `mean` and `deviation` values to control data randomness.
- **Using TLS**: Enable `use_tls` and provide the necessary certificate files for secure connections.
- **Authentication**: Set `username` and `password` for brokers that require authentication.

---

## License

This project is open source and licensed under the MIT License.

---

This documentation provides an overview of the MQTT Data Simulator, details about the configuration file, and instructions for running and customizing the tool.

Feel free to update the documentation to fit your specific project details (e.g., repository links, contact information). Let me know if you need further clarification or edits!