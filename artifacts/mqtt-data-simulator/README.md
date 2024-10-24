# MQTT Data Simulator

This project simulates data publishing to an MQTT broker, generating dynamic data based on configuration files. The simulation supports multiple data types (numeric, boolean, datetime, string, etc.) and topics, making it ideal for testing IoT or distributed systems where data is exchanged through MQTT.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [MQTT Client Configuration](#mqtt-client-configuration)
- [Data Generation Logic](#data-generation-logic)
  - [Tag Types](#tag-types)
  - [Additional Parameters](#additional-parameters)
- [Error Handling](#error-handling)
- [Logging](#logging)
- [License](#license)

## Features

- Simulates MQTT data publishing with customizable configuration.
- Supports multiple data types: boolean, numeric, datetime, string, UUID.
- Incremental and bounded value generation for numeric tags.
- Configurable MQTT client with support for authentication and TLS encryption.
- Automatic handling of data publishing intervals.
- Provides colored terminal output for better readability.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/chriscrcodes/smart-factory.git
    cd artifacts/mqtt-data-simulator
    ```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

    Dependencies include:
    - `paho-mqtt`
    - `colorama`
    - `pyfiglet`

## Configuration

The simulator reads configuration from a `config.json` file. Below is an example configuration:

```json
{
  "mqtt_broker": {
    "address": "broker.hivemq.com",
    "port": 1883,
    "username": "your_username",
    "password": "your_password",
    "use_tls": false
  },
  "root_topic": "home/sensor",
  "publish_interval": 5,
  "topics": [
    {
      "topics": ["temperature", "humidity"],
      "tags": [
        {
          "tag": "temp_sensor",
          "type": "numeric",
          "min_value": 10,
          "max_value": 35,
          "increment_step": 0.5,
          "reset": true
        },
        {
          "tag": "humidity_sensor",
          "type": "numeric",
          "min_value": 20,
          "max_value": 80,
          "increment_step": 1
        }
      ]
    }
  ]
}
```

### Configuration Fields

- **mqtt_broker**: MQTT broker settings (address, port, username, password, TLS).
- **root_topic**: The root topic under which all sub-topics will be published.
- **publish_interval**: Time interval (in seconds) between consecutive data publications.
- **topics**: A list of topic configurations. Each entry includes:
  - `topics`: List of topic names.
  - `tags`: List of tags with their respective data type and generation parameters.

## Usage

1. Prepare your `config.json` file with the desired settings.
2. Run the simulator:
    ```bash
    python mqtt_data_simulator.py
    ```

3. The simulator will:
    - Connect to the MQTT broker using the settings in `config.json`.
    - Continuously publish data to the specified topics at intervals.

## MQTT Client Configuration

The MQTT client is configured with the following parameters:

- **Username/Password Authentication**: If provided, the simulator will authenticate with the broker using a username and password.
- **TLS Encryption**: The simulator supports secure communication using TLS, configurable through the `config.json` file. Set `use_tls` to `true` and provide the `certfile` and `keyfile` for authentication.

## Data Generation Logic

The simulator can generate different types of data for each tag in the configuration. Here's a detailed explanation of each type and the relevant configuration parameters:

### Tag Types

1. **Boolean**
   - Randomly generates either `True` or `False`.
   - Example configuration:
     ```json
     {
       "tag": "door_sensor",
       "type": "boolean"
     }
     ```

2. **Integer and Float (Numeric Ranges)**
   - Generates a number (integer or float) within a specified range, optionally increasing or decreasing by a step on each publish cycle.
   - **min_value**: The minimum value the tag can generate.
   - **max_value**: The maximum value the tag can generate.
   - **increment_step**: The value to increment or decrement by on each publish cycle.
   - **reset**: Whether to reset the value to `min_value` if it exceeds `max_value`.
   - Example configuration:
     ```json
     {
       "tag": "temp_sensor",
       "type": "numeric",
       "min_value": 10,
       "max_value": 35,
       "increment_step": 0.5,
       "reset": true
     }
     ```

3. **Constant**
   - Always generates the same predefined value for every publish cycle.
   - Example configuration:
     ```json
     {
       "tag": "static_value",
       "constant": 42
     }
     ```

4. **Datetime**
   - Generates the current UTC timestamp in ISO 8601 format.
   - Example configuration:
     ```json
     {
       "tag": "timestamp",
       "type": "datetime"
     }
     ```

5. **String**
   - Generates a random string, typically in the format `"SampleString_<random_number>"`.
   - Example configuration:
     ```json
     {
       "tag": "device_id",
       "type": "string"
     }
     ```

6. **UUID**
   - Generates a unique identifier (UUID v4) for each publish cycle.
   - Example configuration:
     ```json
     {
       "tag": "session_id",
       "type": "guid"
     }
     ```

### Additional Parameters

1. **mean** and **deviation**
   - These parameters are used to generate values that fall within a range centered around a `mean` value with a random variation defined by `deviation`. The generated value will be between `mean - deviation` and `mean + deviation`.
   - Example configuration:
     ```json
     {
       "tag": "random_temperature",
       "type": "numeric",
       "mean": 25,
       "deviation": 5
     }
     ```
   - This would generate temperatures between 20 and 30.

2. **min_value** and **max_value**
   - These define the lower and upper bounds for the values a tag can generate.
   - They are mainly used with numeric tags to set boundaries for the data.
   - Example configuration:
     ```json
     {
       "tag": "pressure_sensor",
       "type": "numeric",
       "min_value": 50,
       "max_value": 100
     }
     ```

3. **increment_step**
   - This defines how much a numeric value should increase or decrease on each cycle.
   - The value increments or decrements based on the step size and loops back to `min_value` if `reset` is `true`.
   - Example configuration:
     ```json
     {
       "tag": "flow_rate",
       "type": "numeric",
       "min_value": 1,
       "max_value": 10,
       "increment_step": 0.5,
       "reset": true
     }
     ```

### Customization and Behavior

- The **numeric** type can use either the `mean`/`deviation` approach or the `min_value`/`max_value` with `increment_step`. You can choose one depending on your use case.
- The **boolean**, **constant**, **datetime**, **string**, and **UUID** types do not support `min_value`, `max_value`, or `increment_step`.

These settings allow for flexible data generation to simulate real-world scenarios where sensor values change over time or remain constant.

## Error Handling

The code is wrapped with exception handling using a custom decorator `@handle_exception`. This decorator ensures any errors during function execution are logged, providing detailed error information. Each decorated method in the simulator catches exceptions, logs them, and re-raises the error.

## Logging

The application logs information using Python's `logging` module. By default, logs are displayed in the terminal and include timestamps and logging levels. The logging level can be configured to display different levels of verbosity.

### Log Levels

- `INFO`: General information and success messages (default).
- `DEBUG`: Detailed information about the data generation process.
- `ERROR`: Captures errors during execution, along with the function where they occurred.

### Colored Output

Terminal outputs are colorized using `colorama` to enhance readability:

- **Green**: Successful MQTT connections.
- **Red**: Errors.
- **Blue**: Published data.

## License

This project is licensed under the MIT License. See the [LICENSE](../../LICENSE) file for more details.