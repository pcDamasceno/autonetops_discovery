import logging
from typing import Optional, List, Dict, Any
from pynetbox import api
from slugify import slugify
from abc import ABC, abstractmethod
import napalm
import netmiko

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NetworkDriver(ABC):
    """Abstract base class for network LIBRARY."""

    @abstractmethod
    def connect(
        self, host: str, username: str, password: str, device_type: str
    ) -> None:
        """Establish a connection to the device."""
        pass

    @abstractmethod
    def get_facts(self) -> Dict[str, Any]:
        """Retrieve device facts (e.g., hostname, model, OS version)."""
        pass

    @abstractmethod
    def get_interfaces(self) -> List[Dict[str, Any]]:
        """Retrieve interface information."""
        pass

    @abstractmethod
    def get_config(self) -> str:
        """Retrieve the device configuration."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the connection."""
        pass


class NapalmDriver(NetworkDriver):
    """NAPALM driver for network data collection."""

    def __init__(self):
        self.driver = None
        self.device = None

    def _netmiko_device_type_to_driver(self, device_type: str) -> str:
        """Map Netmiko device type to a more generic driver name."""
        device_type_mapping = {
            "cisco_ios": "ios",
            "cisco_nxos": "nxos_ssh",
            "arista_eos": "eos",
            "juniper": "junos",
            "juniper_junos": "junos",
            # Add more mappings as needed
        }
        return device_type_mapping.get(device_type, device_type)

    def connect(
        self, host: str, username: str, password: str, device_type: str
    ) -> None:
        napalm_driver = self._netmiko_device_type_to_driver(device_type)
        try:
            driver = napalm.get_network_driver(napalm_driver)
            self.device = driver(hostname=host, username=username, password=password)
            self.device.open()
            logger.info(f"Connected to {host} via NAPALM")
        except Exception as e:
            logger.error(f"NAPALM connection error: {e}")
            raise

    def get_facts(self) -> Dict[str, Any]:
        try:
            return self.device.get_facts()
        except Exception as e:
            logger.error(f"NAPALM get_facts error: {e}")
            return {}

    def get_interfaces(self) -> List[Dict[str, Any]]:
        try:
            interfaces = self.device.get_interfaces()
            return [{"name": k, **v} for k, v in interfaces.items()]
        except Exception as e:
            logger.error(f"NAPALM get_interfaces error: {e}")
            return []

    def get_config(self) -> str:
        try:
            config = self.device.get_config()
            return config.get("running", "")
        except Exception as e:
            logger.error(f"NAPALM get_config error: {e}")
            return ""

    def close(self) -> None:
        if self.device:
            self.device.close()
            logger.info("NAPALM connection closed")


class NetmikoDriver(NetworkDriver):
    """Netmiko driver for network data collection."""

    def __init__(self):
        self.conn = None

    def connect(
        self, host: str, username: str, password: str, device_type: str
    ) -> None:        
        try:
            self.conn = netmiko.ConnectHandler(
                device_type=device_type, host=host, username=username, password=password
            )
            logger.info(f"Connected to {host} via Netmiko")
        except Exception as e:
            logger.error(f"Netmiko connection error: {e}")
            raise

    def get_facts(self) -> Dict[str, Any]:
        try:
            output = self.conn.send_command("show version", use_textfsm=True)
            return output[0] if isinstance(output, list) and output else {}
        except Exception as e:
            logger.error(f"Netmiko get_facts error: {e}")
            return {}

    def get_interfaces(self) -> List[Dict[str, Any]]:
        try:
            output = self.conn.send_command("show interfaces", use_textfsm=True)
            return output if isinstance(output, list) else []
        except Exception as e:
            logger.error(f"Netmiko get_interfaces error: {e}")
            return []

    def get_config(self) -> str:
        try:
            return self.conn.send_command("show running-config")
        except Exception as e:
            logger.error(f"Netmiko get_config error: {e}")
            return ""

    def close(self) -> None:
        if self.conn:
            self.conn.disconnect()
            logger.info("Netmiko connection closed")


class NetworkCollector:
    """Class to collect network data using a specified driver."""

    LIBRARY = {
        "napalm": NapalmDriver,
        "netmiko": NetmikoDriver,
        # SCRAPLI
        # SNMP
        # NETCONF
        # RESTCONF
    }

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        device_type: str,
        library: str = "netmiko"  # Default to Netmiko, can be overridden
    ):
        """
        Initialize the NetworkCollector.

        Args:
            host (str): The device hostname or IP.
            username (str): The username for authentication.
            password (str): The password for authentication.
            device_type (str): The device type (e.g., "cisco_ios", "juniper").
            library (str): The name of the driver (e.g., "napalm", "netmiko").
        """
        if library not in self.LIBRARY:
            raise ValueError(
                f"Unsupported driver: {library}. Supported: {list(self.LIBRARY.keys())}"
            )
        self.driver = self.LIBRARY[library]()
        self.host = host
        self.username = username
        self.password = password
        self.device_type = device_type

    def __enter__(self):
        """Context manager entry point to establish connection."""
        self.connect()
        return self

    def __exit__(self):
        """Context manager exit point to close connection."""
        self.close()

    def connect(self) -> None:
        """Establish a connection to the device."""
        self.driver.connect(self.host, self.username, self.password, self.device_type)

    def get_facts(self) -> Dict[str, Any]:
        """Retrieve device facts."""
        return self.driver.get_facts()

    def get_interfaces_ip(self) -> List[Dict[str, Any]]:
        """Retrieve interface information."""
        return self.driver.get_interfaces()

    def get_lldp_neighbors(self) -> str:
        """Retrieve the device configuration."""
        return self.driver.get_config()

    def close(self) -> None:
        """Close the connection."""
        self.driver.close()
