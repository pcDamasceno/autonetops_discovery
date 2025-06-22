from napalm import get_network_driver
from scrapli import Scrapli
from dataclasses import dataclass
from slugify import slugify
from netbox_classes import *
from connector import NetworkCollector
from typing import Optional, List, Enum


class Site(NbSiteMixin):
    def __init__(self, name: str, slug=None, status="active"):
        self.name = name
        self.slug = slugify(name) if slug is None else slug
        self.status = status
        self.id = None

        ## Optional attributes
        self.description = f"Autonetops site {name}"
        self.tenant = None
        self.tenant_group = None

        self.devices = []

    def __str__(self):
        return f"{self.name} - {self.slug} - {self.status}"

    def __repr__(self):
        return f"{self.name} - {self.slug} - {self.status}"

    def device_add(self, device) -> None:
        if isinstance(device, Device):
            self.devices.append(device)
        else:
            raise TypeError("device must be an instance of NbDevice")

    def device_remove(self, device) -> None:
        if isinstance(device, Device):
            self.devices.remove(device)
        else:
            raise TypeError("device must be an instance of NbDevice")


class Device(NbDeviceMixin):
    VALID_STATUSES = {
        "active",
        "offline",
        "planned",
        "staged",
        "failed",
        "inventory",
        "decommissioned",
    }

    def __init__(self, name):
        self.name = name
        self.device_type: DeviceType
        self.device_role: DeviceRole
        self.site: str = None
        self.status = "active"  # Default status, can be changed later

        ## Optional attributes
        self.serial = None
        self.platform: Platform = None
        self.status = None
        self.mgmt_ip = None
        self.version = None

        self.interfaces = List[Interface]

    def __str__(self):
        return f"{self.name} - {self.mgmt_ip} - {self.device_type}"

    def __repr__(self):
        return f"{self.name} - {self.mgmt_ip} - {self.device_type}"

    def get_network_info(
        self,
        host: str,
        username: str,
        password: str,
        device_type: str,
        library: Optional[str] = None,
    ) -> None:

        connect_info = {
            "host": host,
            "username": username,
            "password": password,
            "device_type": device_type,
            "library": library,
        }

        with NetworkCollector(**connect_info) as conn:
            self.device_type = conn.get_facts()

    def join_site(self, site):
        if isinstance(site, Site):
            self.site = site
            site.add_device(self)
        else:
            raise TypeError("site must be an instance of Site")


class DeviceRole:
    def __init__(self, name, slug=None, color="Grey"):
        self.name = name
        self.slug = slugify(name) if slug is None else slug
        self.color = color


class DeviceType:
    def __init__(self, model, manufacturer, slug=None, part_number=None):
        self.model = model
        self.manufacturer = manufacturer
        self.slug = slugify(model) if slug is None else slug
        self.part_number = part_number

        ## Optional attributes
        self.u_height = None


class Platform:
    def __init__(self, name, slug=None):
        self.name = name
        self.slug = slugify(name) if slug is None else slug

        ## Optional attributes
        self.description = None


class Interface:
    def __init__(self, name, type):
        self.name = name
        self.type = type

        ## Optional attributes
        self.speed = None  # Kbps
        self.mac_address = None
        self.mtu = None
        self.description = None
        self.enabled = True
        self.mode = None  # e.g., access, trunk, routed
        self.vlan = None  # e.g., VLAN ID for access mode
        self.vrf = None  # e.g., VRF for routing interfaces
        self.ip_addresses = []
        self.primary_ip = None
