import pynetbox
from dataclasses import dataclass
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NbConnection:
    url: str = ""
    token: str = ""

    def connect(self):
        """
        Connect to NetBox using the provided URL and token.
        """
        if not self.url or not self.token:
            raise ValueError("URL and token must be provided for NetBox connection.")
        self.nb = pynetbox.api(self.url, token=self.token, strict_filters=True)

    def get_nb(self):
        return self.nb


class NbSiteMixin(NbConnection):
    ### NETBOX METHODS ###
    def nb_create(self):
        """
        Create the site in NetBox if does not exist, else return info
        """
        try:
            nb_site = nb.dcim.sites.get(name=self.name)
            # Create a new site if it doesn't exist
            if not nb_site:
                nb_site = nb.dcim.sites.create(
                    name=self.name,
                    slug=self.slug,
                    status=self.status,
                    description=self.description,
                    tenant=self.tenant,
                    tenant_group=self.tenant_group,
                )
            # Update the existing site if it exists
            else:
                self.slug = nb_site.slug if nb_site.slug else self.slug
                self.status = nb_site.status if nb_site.status else self.status
                self.tenant = nb_site.tenant
                self.id = nb_site.id

            return nb_site
        except Exception as e:
            print(f"Error creating/updating site: {e}")
            return None


class NbDeviceMixin(NbConnection):
    """Mixin for NetBox device integration."""

    def nb_create(self, site_id: int = None) -> Optional["pynetbox.models.dcim.Device"]:
        """
        Create or update the device in NetBox.

        Args:
            nb (pynetbox.api): The NetBox API client.
            site_id (int, optional): The ID of the site to associate with the device.

        Returns:
            pynetbox.models.dcim.Device: The created or existing device object, or None on error.
        """
        try:
            nb_device = nb.dcim.devices.get(
                name=self.name, site=self.site.name if self.site else None
            )
            if not nb_device:
                device_data = {
                    "name": self.name,
                    "device_type": self.device_type["id"] if self.device_type else None,
                    "role": self.device_role["id"] if self.device_role else None,
                    "site": site_id or (self.site.id if self.site else None),
                    "status": self.status,
                    "serial": self.serial,
                    "platform": self.platform["id"] if self.platform else None,
                    "primary_ip": self.primary_ip["id"] if self.primary_ip else None,
                }
                nb_device = nb.dcim.devices.create(
                    **{k: v for k, v in device_data.items() if v is not None}
                )
                logger.info(f"Created device {self.name} in NetBox")
            else:
                update_data = {}
                if nb_device.status != self.status:
                    update_data["status"] = self.status
                if nb_device.serial != self.serial:
                    update_data["serial"] = self.serial
                if nb_device.platform != (self.platform or {}).get("id"):
                    update_data["platform"] = (
                        self.platform["id"] if self.platform else None
                    )
                if nb_device.primary_ip != (self.primary_ip or {}).get("id"):
                    update_data["primary_ip"] = (
                        self.primary_ip["id"] if self.primary_ip else None
                    )
                if update_data:
                    nb_device.update(update_data)
                    logger.info(f"Updated device {self.name} in NetBox")
                self.status = nb_device.status
                self.serial = nb_device.serial
                self.platform = (
                    {"id": nb_device.platform.id} if nb_device.platform else None
                )
                self.primary_ip = (
                    {"id": nb_device.primary_ip.id} if nb_device.primary_ip else None
                )
                self.id = nb_device.id
                logger.info(f"Device {self.name} already exists in NetBox")
            return nb_device
        except pynetbox.core.query.RequestError as e:
            logger.error(f"NetBox API error: {e}")
            return None
        except pynetbox.core.query.ValidationError as e:
            logger.error(f"Validation error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating/updating device: {e}")
            return None


nb = NbConnection(
    "http://localhost:8000", token="dea93b24783b6f573432d552c52d075ab79b8b60"
)
