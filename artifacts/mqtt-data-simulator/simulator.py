import json
import paho.mqtt.client as mqtt
import random
import time
from datetime import datetime, timezone
import uuid
import ssl
import colorama
import logging
from colorama import Fore, Style
import pyfiglet
from typing import Any, Dict, List, Optional, Callable

# Initialize Colorama for colored terminal output
colorama.init(autoreset=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
DEFAULT_PUBLISH_INTERVAL = 1  # Default publish interval in seconds

def handle_exception(func: Callable) -> Callable:
    """Decorator to handle exceptions and log them."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"{Fore.RED}Error in {func.__name__}: {str(e)}")
            raise
    return wrapper

class MqttDataSimulator:
    """Simulate MQTT data publishing based on a configuration."""
    
    def __init__(self, config_file_path: str = 'config.json'):
        self.config_file_path = config_file_path
        self.client: Optional[mqtt.Client] = None
        self.config = self.load_config()
        self.configure_mqtt()

    def display_banner(self) -> None:
        """Display the ASCII banner and author information."""
        banner = pyfiglet.figlet_format("MQTT Data Simulator")
        author_info = f"{Fore.CYAN}Author: Christophe Crémon\n"
        website_info = f"{Fore.CYAN}Website: https://github.com/chriscrcodes"
        print(f"{Fore.YELLOW}{banner}{Style.RESET_ALL}{author_info}{website_info}")

    @handle_exception
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from a JSON file."""
        with open(self.config_file_path, 'r') as file:
            config = json.load(file)
        self.validate_config(config)
        return config

    @handle_exception
    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate the configuration settings."""
        if 'mqtt_broker' not in config:
            raise ValueError("MQTT broker configuration is missing.")
        config.setdefault('publish_interval', DEFAULT_PUBLISH_INTERVAL)

    @handle_exception
    def configure_mqtt(self) -> None:
        """Configure MQTT client settings."""
        self.client = mqtt.Client(protocol=mqtt.MQTTv5)
        mqtt_broker = self.config['mqtt_broker']
        self.client.username_pw_set(mqtt_broker.get('username'), mqtt_broker.get('password'))

        # Setup TLS if required
        if mqtt_broker.get('use_tls', False):
            self.client.tls_set(
                certfile=mqtt_broker.get('certfile'),
                keyfile=mqtt_broker.get('keyfile'),
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )

    @handle_exception
    def connect_mqtt(self) -> None:
        """Connect to the MQTT broker."""
        mqtt_broker = self.config['mqtt_broker']
        self.client.connect(mqtt_broker['address'], mqtt_broker['port'])
        logging.info(f"{Fore.GREEN}Connected to MQTT broker at {mqtt_broker['address']}:{mqtt_broker['port']} 🚀")

    def handle_increment_step(self, tag_config: Dict[str, Any]) -> Any:
        """Handle increment and decrement logic for the tag value."""
        current_value = tag_config.get('current_value', tag_config['min_value'])
        now = datetime.now(timezone.utc)

        # Initialize last_update if not already set
        tag_config.setdefault('last_update', now)

        elapsed_time = (now - tag_config['last_update']).total_seconds()
        if elapsed_time >= tag_config.get('update_interval', 0):
            step = tag_config.get('increment_step', 0) - tag_config.get('decrement_step', 0)
            current_value = max(tag_config['min_value'], min(current_value + step, tag_config['max_value']))

            # Reset to min_value if necessary
            if current_value > tag_config['max_value']:
                current_value = tag_config['min_value'] if tag_config.get('reset', False) else tag_config['max_value']

            tag_config['current_value'] = current_value
            tag_config['last_update'] = now
            logging.debug(f"Updated current value to {current_value} (step: {step})")

        return current_value

    @handle_exception
    def generate_data(self, tag_config: Dict[str, Any]) -> Any:
        """Generate data based on the tag configuration."""
        tag_type = tag_config.get('type')

        if 'constant' in tag_config:
            logging.debug(f"Generating constant value: {tag_config['constant']}")
            return tag_config['constant']

        if tag_type == 'boolean':
            value = random.choice([True, False])
            logging.debug(f"Generated boolean value: {value}")
            return value

        if tag_config.get('mean') is not None and tag_config.get('deviation') is not None:
            value = round(random.uniform(tag_config['mean'] - tag_config['deviation'], 
                                          tag_config['mean'] + tag_config['deviation']), 2)
            logging.debug(f"Generated value in range ({tag_config['mean'] - tag_config['deviation']}, "
                          f"{tag_config['mean'] + tag_config['deviation']}): {value}")
            return value

        if 'min_value' in tag_config and 'max_value' in tag_config:
            return self.handle_increment_step(tag_config)

        return self.handle_other_data_types(tag_config)

    @handle_exception
    def handle_other_data_types(self, tag_config: Dict[str, Any]) -> Any:
        """Handle other data types such as datetime, string, and UUID."""
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
        """Publish generated data to specified MQTT topics."""
        data['Timestamp'] = datetime.now(timezone.utc).isoformat()
        
        for topic in topics:
            full_topic = f"{root_topic}/{topic}"
            data['UNS'] = full_topic  # Keep the UNS value updated

            # Split UNS and check the number of components
            uns_components = data['UNS'].split('/')
            if len(uns_components) != 5:
                logging.warning(f"{Fore.YELLOW}UNS '{data['UNS']}' does not have exactly 5 components. Data will be skipped.")
                continue
            
            data.update(dict(zip(['Enterprise', 'Site', 'Area', 'Line', 'Cell'], uns_components)))

            self.client.publish(full_topic, json.dumps(data))
            logging.info(f"{Fore.BLUE}{data['Timestamp']} - Published data to topic '{full_topic}': {data} 📡")

    def start_publishing(self) -> None:
        """Start the main publishing loop."""
        try:
            self.connect_mqtt()
            self.client.loop_start()

            while True:
                for topic_config in self.config['topics']:
                    topics = topic_config['topics']
                    data = {tag['tag']: self.generate_data(tag) for tag in topic_config.get('tags', [])}
                    self.publish_data(self.config['root_topic'], topics, data)
                time.sleep(self.config['publish_interval'])  # Publish interval from config
        except KeyboardInterrupt:
            logging.info(f"{Fore.YELLOW}Stopping the publisher... 🛑")
        except Exception as e:
            logging.error(f"{Fore.RED}An error occurred during publishing: {str(e)}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    try:
        simulator = MqttDataSimulator()
        simulator.display_banner()
        simulator.start_publishing()
    except Exception as e:
        logging.error(f"{Fore.RED}Fatal error in the simulator: {str(e)}")