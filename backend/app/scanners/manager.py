from app.core.exceptions import ValidationError
from app.scanners.nmap.scanner import NmapScanner


class ScannerManager:

    def __init__(self):
        self.nmap = NmapScanner()

    def run(
        self,
        scanner: str,
        target: str,
        scan_id: int | None = None,
        arguments: str | None = None,
    ):

        scanner = scanner.lower()

        if scanner == "nmap":
            return self.nmap.scan(
                target,
                scan_id=scan_id,
                arguments=arguments,
            )

        raise ValidationError(
            f"Unknown scanner: {scanner}"
        )
