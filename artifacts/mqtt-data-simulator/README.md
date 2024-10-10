# MQTT Data Simulator

## Overview

The MQTT Data Simulator is a tool for generating simulated data to be sent to an MQTT broker. It allows for customizable configurations, enabling users to define various metrics, their ranges, and how they change over time. 

## Configuration Parameters

### 1. MQTT Broker Configuration
- **address**: The address of the MQTT broker (e.g., `broker.hivemq.com`).
- **port**: The port number to connect to the MQTT broker (e.g., `1883`).
- **username**: (Optional) Username for authenticating with the MQTT broker.
- **password**: (Optional) Password for authenticating with the MQTT broker.

### 2. Tags Configuration

#### Tag Parameters
Each tag represents a data point in the simulation and can have the following parameters:

- **tag**: The name of the metric (e.g., `Temperature`, `Pressure`, `Speed`).

- **min_value**: 
  - **Description**: The minimum allowable value for the metric.
  - **Usage**: Defines the lower boundary for generated values.
  - **Example**: If set to `0`, simulated values will not be lower than `0`.

- **max_value**: 
  - **Description**: The maximum allowable value for the metric.
  - **Usage**: Defines the upper boundary for generated values.
  - **Example**: If set to `100`, simulated values will not exceed `100`.

- **increment_step**: 
  - **Description**: The step by which the value increases or decreases during simulation.
  - **Usage**: Controls how much the value changes over time.
  - **Example**: If set to `5`, values could change in increments of `5` (e.g., `10`, `15`, `20`).

- **reset**: 
  - **Description**: A boolean parameter that determines whether to reset the value of the metric.
  - **Usage**: If `true`, resets the value to its initial state.
  - **Example**: If current value is `60` and `reset` is `true`, the next reading may revert to a baseline (e.g., `25`).

- **constant**: 
  - **Description**: A fixed value for the metric throughout the simulation.
  - **Usage**: Outputs a specific value that does not change.
  - **Example**: If set to `30`, the simulated temperature will always report as `30`.

### Example Configuration
Here’s an example of how you might configure these parameters in a JSON file for the MQTT Data Simulator:

```json
{
  "mqtt_broker": {
    "address": "broker.hivemq.com",
    "port": 1883
  },
  "tags": [
    {
      "tag": "Temperature",
      "min_value": 0,
      "max_value": 100,
      "increment_step": 1,
      "reset": false,
      "constant": null
    },
    {
      "tag": "Pressure",
      "min_value": 10,
      "max_value": 150,
      "increment_step": 5,
      "reset": true,
      "constant": null
    },
    {
      "tag": "Speed",
      "min_value": 0,
      "max_value": 80,
      "increment_step": 10,
      "reset": false,
      "constant": 50
    }
  ]
}
```

## Authentication

If your MQTT broker requires authentication, provide the username and password in the configuration:

- **username**: The username for authenticating with the MQTT broker.
- **password**: The password for authenticating with the MQTT broker.

### Example Authentication Configuration
```json
{
  "mqtt_broker": {
    "address": "broker.hivemq.com",
    "port": 1883,
    "username": "your_username",
    "password": "your_password"
  }
}
```

### Using Authentication in the Simulator
When establishing a connection to the MQTT broker, ensure to utilize the provided username and password. Most MQTT libraries support authentication, so consult your library’s documentation for implementation details.

## Conclusion

This simulator allows for detailed customization of simulated data output. By effectively using parameters like `min_value`, `max_value`, `increment_step`, `reset`, and `constant`, users can create realistic scenarios for testing or development purposes. Authentication ensures secure communication with the MQTT broker, allowing for safe data transmission.