from enum import Enum


class ScanProfile(str, Enum):
    """Port coverage profile used for an nmap scan.

    STANDARD scans nmap's default top-1000 most common TCP ports (fast).
    FULL scans the entire TCP port range 1-65535 (slow but thorough).
    """

    STANDARD = "standard"
    FULL = "full"
