from enum import Enum


class AssetType(str, Enum):
    SERVER = "SERVER"
    WORKSTATION = "WORKSTATION"
    WEBSITE = "WEBSITE"
    DOMAIN = "DOMAIN"
    IP_ADDRESS = "IP_ADDRESS"
    API = "API"
    CLOUD = "CLOUD"
    MOBILE = "MOBILE"
    OTHER = "OTHER"
