import json
import paho.mqtt.client as mqtt
import random
import time
from datetime import datetime, timezone
import uuid
import ssl
import colorama
import logging
import pyfiglet
from typing import Any, Dict, List, Optional, Callable

# Initialize Colorama for colored terminal output
colorama.init(autoreset=True)

# Configure logging with a configurable logging level
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ConfigConstants:
    """Constants for configuration settings."""
    CONFIG_FILE_PATH = "/app/config.json"  # Path to the configuration file
    DEFAULT_PUBLISH_INTERVAL = 1  # Default publish interval in seconds
    UNS_COMPONENT_COUNT = 5  # Number of expected components in UNS
    DEFAULT_LOGGING_LEVEL = logging.INFO  # Default logging level


def handle_exception(func: Callable) -> Callable:
    """
    Decorator to handle exceptions and log them with context.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"{colorama.Fore.RED}Error in {func.__name__}: {str(e)}")
            raise
    return wrapper


class MqttDataSimulator:
    """
    Simulate MQTT data publishing based on a configuration.
    Handles MQTT client configuration, data generation, and publishing.
    """
    
    def __init__(self, config_file_path: str = ConfigConstants.CONFIG_FILE_PATH):
        self.config_file_path = config_file_path
        self.client: Optional[mqtt.Client] = None
        self.config = self.load_config()
        self.configure_mqtt()

    def display_banner(self) -> None:
        """Display an ASCII banner with author and project info."""
        banner = pyfiglet.figlet_format("MQTT Data Simulator")
        author_info = f"{colorama.Fore.CYAN}Author: Christophe Crémon\n"
        website_info = f"{colorama.Fore.CYAN}Website: https://github.com/chriscrcodes"
        print(f"{colorama.Fore.YELLOW}{banner}{colorama.Style.RESET_ALL}{author_info}{website_info}")

    @handle_exception
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from a JSON file.

        Raises:
            FileNotFoundError: If the config file is missing.
            json.JSONDecodeError: If the config file contains invalid JSON.
        """
        with open(self.config_file_path, 'r') as file:
            config = json.load(file)
        self.validate_config(config)
        return config

    @handle_exception
    def validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate the configuration settings.
        
        Ensures required fields are present and applies defaults where needed.

        Raises:
            ValueError: If required fields are missing.
        """
        if 'mqtt_broker' not in config:
            raise ValueError("MQTT broker configuration is missing.")
        config.setdefault('publish_interval', ConfigConstants.DEFAULT_PUBLISH_INTERVAL)

    @handle_exception
    def configure_mqtt(self) -> None:
        """
        Configure MQTT client settings, including authentication and TLS.
        Applies necessary settings for secure communication if required.
        """
        self.client = mqtt.Client(protocol=mqtt.MQTTv5)
        mqtt_broker = self.config['mqtt_broker']
        self.client.username_pw_set(mqtt_broker.get('username'), mqtt_broker.get('password'))

        if mqtt_broker.get('use_tls', False):
            self.setup_tls(mqtt_broker)

    def setup_tls(self, mqtt_broker: Dict[str, Any]) -> None:
        """
        Set up TLS for the MQTT client if required.

        Args:
            mqtt_broker (Dict[str, Any]): Configuration settings for the MQTT broker.
        """
        self.client.tls_set(
            certfile=mqtt_broker.get('certfile'),
            keyfile=mqtt_broker.get('keyfile'),
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )

    @handle_exception
    def connect_mqtt(self) -> None:
        """
        Connect to the MQTT broker using settings from the configuration.
        Logs the connection status.
        """
        mqtt_broker = self.config['mqtt_broker']
        self.client.connect(mqtt_broker['address'], mqtt_broker['port'])
        logging.info(f"{colorama.Fore.GREEN}Connected to MQTT broker at {mqtt_broker['address']}:{mqtt_broker['port']} 🚀")

    def handle_increment_step(self, tag_config: Dict[str, Any]) -> Any:
        """
        Handle the logic for incrementing or decrementing tag values over time.
        Ensures values stay within configured bounds and optionally resets when exceeding max_value.
        """
        current_value = tag_config.get('current_value', tag_config['min_value'])
        now = datetime.now(timezone.utc)

        tag_config.setdefault('last_update', now)
        elapsed_time = (now - tag_config['last_update']).total_seconds()

        if elapsed_time >= tag_config.get('update_interval', 0):
            current_value = self.update_value(tag_config, current_value)
            tag_config['current_value'] = current_value
            tag_config['last_update'] = now
            logging.debug(f"Updated current value to {current_value} (step: {tag_config.get('increment_step', 0)})")

        return current_value

    def update_value(self, tag_config: Dict[str, Any], current_value: float) -> float:
        """
        Update the value based on increment and decrement steps while enforcing limits.

        Args:
            tag_config (Dict[str, Any]): Configuration for the tag.
            current_value (float): The current value of the tag.

        Returns:
            float: The updated current value.
        """
        step = tag_config.get('increment_step', 0) - tag_config.get('decrement_step', 0)
        current_value = max(tag_config['min_value'], min(current_value + step, tag_config['max_value']))

        if current_value > tag_config['max_value']:
            current_value = tag_config['min_value'] if tag_config.get('reset', False) else tag_config['max_value']

        return current_value

    @handle_exception
    def generate_data(self, tag_config: Dict[str, Any]) -> Any:
        """
        Generate data based on the tag configuration.
        
        Supports various data types such as constants, booleans, numeric ranges, and more.
        """
        if 'constant' in tag_config:
            logging.debug(f"Generating constant value: {tag_config['constant']}")
            return tag_config['constant']

        tag_type = tag_config.get('type')

        if tag_type == 'boolean':
            value = random.choice([True, False])
            logging.debug(f"Generated boolean value: {value}")
            return value

        if tag_config.get('mean') is not None and tag_config.get('deviation') is not None:
            return self.generate_mean_deviation_value(tag_config)

        if 'min_value' in tag_config and 'max_value' in tag_config:
            return self.handle_increment_step(tag_config)

        return self.handle_other_data_types(tag_config)

    def generate_mean_deviation_value(self, tag_config: Dict[str, Any]) -> float:
        """
        Generate a value based on mean and deviation.

        Args:
            tag_config (Dict[str, Any]): Configuration for the tag.

        Returns:
            float: The generated value within the specified mean and deviation.
        """
        value = round(random.uniform(tag_config['mean'] - tag_config['deviation'], 
                                     tag_config['mean'] + tag_config['deviation']), 2)
        logging.debug(f"Generated value in range ({tag_config['mean'] - tag_config['deviation']}, "
                      f"{tag_config['mean'] + tag_config['deviation']}): {value}")
        return value

    @handle_exception
    def handle_other_data_types(self, tag_config: Dict[str, Any]) -> Any:
        """
        Handle non-numeric data types such as datetime, string, and UUID.
        """
        tag_type = tag_config['type']
        if tag_type == 'datetime':
            value = datetime.now(timezone.utc).isoformat()
            logging.debug(f"Generated datetime value: {value}")
            return value
        elif tag_type == 'string':
            value = f"SampleString_{random.randint(1, 100)}"
            logging.debug(f"Generated string value: {value}")
            return value
        elif tag_type == 'guid':
            value = str(uuid.uuid4())
            logging.debug(f"Generated GUID value: {value}")
            return value
        return tag_config.get('value')

    @handle_exception
    def publish_data(self, root_topic: str, topics: List[str], data: Dict[str, Any]) -> None:
        """
        Publish generated data to specified MQTT topics.
        
        Includes UNS (Unified Namespace) parsing and data enrichment.
        """
        data['Timestamp'] = datetime.now(timezone.utc).isoformat()
        
        for topic in topics:
            self.publish_to_topic(root_topic, topic, data)

    def publish_to_topic(self, root_topic: str, topic: str, data: Dict[str, Any]) -> None:
        """
        Publish data to a specific topic.

        Args:
            root_topic (str): The root topic for the MQTT message.
            topic (str): The specific topic to publish to.
            data (Dict[str, Any]): The data to publish.
        """
        full_topic = f"{root_topic}/{topic}"
        data['UNS'] = full_topic  # Update UNS with the current topic

        uns_components = data['UNS'].split('/')
        if len(uns_components) == ConfigConstants.UNS_COMPONENT_COUNT:
            data.update(dict(zip(['Enterprise', 'Site', 'Area', 'Line', 'Cell'], uns_components)))

        self.client.publish(full_topic, json.dumps(data))
        logging.info(f"{colorama.Fore.BLUE}{data['Timestamp']} - Published data to topic '{full_topic}': {data} 📡")

    def start_publishing(self) -> None:
        """
        Start the main publishing loop.
        
        Continuously generates and publishes data to configured topics at intervals.
        """
        try:
            self.connect_mqtt()
            self.client.loop_start()
            self.run_publishing_loop()
        except KeyboardInterrupt:
            logging.info(f"{colorama.Fore.YELLOW}Stopping the publisher... 🛑")
        except Exception as e:
            logging.error(f"{colorama.Fore.RED}An error occurred during publishing: {str(e)}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

    def run_publishing_loop(self) -> None:
        """Run the publishing loop to generate and send data."""
        while True:
            for topic_config in self.config['topics']:
                topics = topic_config['topics']
                data = {tag['tag']: self.generate_data(tag) for tag in topic_config.get('tags', [])}
                self.publish_data(self.config['root_topic'], topics, data)
            time.sleep(self.config['publish_interval'])

if __name__ == "__main__":
    try:
        simulator = MqttDataSimulator()
        simulator.display_banner()
        simulator.start_publishing()
    except Exception as e:
        logging.error(f"{colorama.Fore.RED}Fatal error in the simulator: {str(e)}")