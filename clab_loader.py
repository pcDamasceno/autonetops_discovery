import yaml
from classes import Site, Device
from slugify import slugify

with open(
    "/home/pdamasceno/GIT/autonetops-GIT/autonetops_free_labs/autonetops_bgp_fundamentals/bgp-med/clab/lab.clab.yaml",
    "r",
) as f:
    clab_yaml = yaml.safe_load(f)


def get_device_list(clab_yaml) -> list:
    device_list = []
    if clab_yaml["topology"].get("defaults", False):
        default_kind = clab_yaml["topology"]["defaults"].get("kind", False)

    for device_name, device_data in clab_yaml["topology"]["nodes"].items():
        device_list.append(
            {
                "name": device_name,
                "kind": device_data.get("kind", default_kind),
                "driver": map_device_kind(device_data.get("kind", default_kind)),
                "ip": device_data["mgmt-ipv4"],
            }
        )

    return device_list


def map_device_kind(kind: str) -> str:
    KIND_MAPPING = {
        "linux": "linux",
        "host": "host",
        "container": "container",
        "cisco_iol": "cisco_ios",
        "arista_eos": "arista_eos",
    }
    return KIND_MAPPING.get(kind, kind)


device_list = get_device_list(clab_yaml)

site = Site(name=clab_yaml["name"], slug=slugify(clab_yaml["name"]))
for device in device_list:
    new_device = Device(name=device["name"])
    new_device.device_type = device["kind"]
    new_device.mgmt_ip = device["ip"]
    new_device.join_site(site)
