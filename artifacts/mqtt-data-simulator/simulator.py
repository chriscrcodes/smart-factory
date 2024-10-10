import json
import paho.mqtt.client as mqtt
import random
import time
from datetime import datetime, timezone
import uuid
import ssl
import colorama
from colorama import Fore, Style
import pyfiglet

# Initialize Colorama for colored terminal output
colorama.init(autoreset=True)

# Constants
CONFIG_FILE_PATH = '/app/config.json'  # Path to the configuration file
DEFAULT_PUBLISH_INTERVAL = 5  # Default interval is 5 seconds
MQTT_PROTOCOL = mqtt.MQTTv5  # MQTT protocol version

# Function to display an ASCII banner and author information
def display_banner():
    banner = pyfiglet.figlet_format("MQTT Data Simulator")  # Generate ASCII art
    author_info = f"{Fore.CYAN}Author: Christophe Crémon\n"
    website_info = f"{Fore.CYAN}Website: https://github.com/chriscrcodes"
    print(f"{Fore.YELLOW}{banner}{Style.RESET_ALL}{author_info}{website_info}")

# Load configuration from a JSON file
def load_config(file_path):
    with open(file_path, 'r') as file:  # Open the configuration file
        return json.load(file)  # Load and return the JSON data

# Generate data based on the provided tag configuration
def generate_data(tag_config):
    # Handle constant values
    if 'constant' in tag_config:
        return tag_config['constant']

    # Handle boolean values (random True/False)
    if tag_config.get('type') == 'boolean':
        return random.choice([True, False])  # Always random

    # Randomized data generation for numeric types
    if 'mean' in tag_config and 'deviation' in tag_config:
        value_range = (tag_config['mean'] - tag_config['deviation'], 
                       tag_config['mean'] + tag_config['deviation'])
        if tag_config['type'] in ['int', 'float', 'double']:
            return round(random.uniform(*value_range), 2)

    # Handling for min_value, max_value, increment_step with reset
    if 'min_value' in tag_config and 'max_value' in tag_config:
        value = tag_config.setdefault('current_value', tag_config['min_value'])
        value += tag_config.get('increment_step', 1)
        if value >= tag_config['max_value']:
            value = 0  # Reset to 0 after max_value is reached
        tag_config['current_value'] = value
        return value

    # Generate datetime, string, and UUID types
    if tag_config['type'] == 'datetime':
        return datetime.now(timezone.utc).isoformat()  # Current UTC time
    if tag_config['type'] == 'string':
        return f"SampleString_{random.randint(1, 100)}"  # Random string
    if tag_config['type'] == 'guid':
        return str(uuid.uuid4())  # Generate a UUID

    # Return a default value if none of the conditions are met
    return tag_config.get('value')

# Publish data to the specified MQTT topics
def publish_data(client, root_topic, topics, data):
    try:
        # Add a UTC timestamp to the data
        data['Timestamp'] = datetime.now(timezone.utc).isoformat()
        for topic in topics:
            full_topic = f"{root_topic}/{topic}"  # Construct the full topic name
            data['UNS'] = full_topic  # Set UNS to the full topic name
            client.publish(full_topic, json.dumps(data))  # Publish the data as a JSON string
            print(f"{Fore.GREEN}{datetime.now(timezone.utc).isoformat()} - Published data to topic '{full_topic}': {data}")
    except Exception as e:
        print(f"{Fore.RED}Error publishing data: {str(e)}")  # Error handling

# Connect to the MQTT broker
def connect_mqtt(config):
    client = mqtt.Client(protocol=MQTT_PROTOCOL)  # Create an MQTT client instance

    # Set username and password if provided
    if 'username' in config['mqtt_broker'] and 'password' in config['mqtt_broker']:
        client.username_pw_set(config['mqtt_broker']['username'], config['mqtt_broker']['password'])

    # Handle TLS settings if enabled in configuration
    if config['mqtt_broker'].get('use_tls', False):
        client.tls_set(certfile=config['mqtt_broker'].get('certfile'), 
                       keyfile=config['mqtt_broker'].get('keyfile'), 
                       cert_reqs=ssl.CERT_REQUIRED, 
                       tls_version=ssl.PROTOCOL_TLSv1_2)

    # Attempt to connect to the MQTT broker
    try:
        client.connect(config['mqtt_broker']['address'], config['mqtt_broker']['port'])
        print(f"{Fore.GREEN}Connected to MQTT broker at {config['mqtt_broker']['address']}:{config['mqtt_broker']['port']}")
        return client  # Return the connected client
    except Exception as e:
        print(f"{Fore.RED}Connection error: {str(e)}")  # Error handling
        return None

# Main function to handle the publishing loop
def start_publishing(config):
    client = connect_mqtt(config)  # Connect to the MQTT broker
    if client is None:
        return  # Exit if connection failed

    # Start the MQTT client loop to handle network events
    client.loop_start()
    
    try:
        while True:
            for topic_config in config['topics']:  # Iterate over each topic in the config
                topics = topic_config['topics']  # Extract the list of topics
                # Generate data for each tag in the configuration
                data = {tag['tag']: generate_data(tag) for tag in topic_config.get('tags', [])}
                
                # Publish generated data to all specified topics
                publish_data(client, config['root_topic'], topics, data)

            time.sleep(config['publish_interval'])  # Sleep for the configured interval
    except KeyboardInterrupt:
        print(f"{Fore.YELLOW}Stopping the publisher...")  # Graceful exit on interrupt
    finally:
        client.loop_stop()  # Stop the MQTT client loop
        client.disconnect()  # Disconnect from the MQTT broker

if __name__ == "__main__":
    display_banner()  # Display the banner

    # Load the configuration from the JSON file
    config = load_config(CONFIG_FILE_PATH)

    # Set a default publish interval if not specified in the config
    config.setdefault('publish_interval', DEFAULT_PUBLISH_INTERVAL)

    # Start the publishing process
    start_publishing(config)