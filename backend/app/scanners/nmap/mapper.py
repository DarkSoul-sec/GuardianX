from app.models.scan_result import ScanResult


class ScanResultMapper:

    @staticmethod
    def to_model(
        scan_id: int,
        service: dict,
    ) -> ScanResult:

        return ScanResult(

            scan_id=scan_id,

            port=service["port"],

            protocol=service["protocol"],

            state=service["state"],

            service=service["service"],

            product=service["product"],

            version=service["version"],

            cpe=service["cpe"],

            is_ssl=service["is_ssl"],

        )
