from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.core.network import validate_scan_target
from app.core.scan_profile import ScanProfile
from app.services.query_helpers import apply_asset_scope
from app.core.scan_status import ScanStatus

from app.database.session import SessionLocal

from app.logger import logger

from app.tasks.scan_worker import scan_executor

from app.models.asset import Asset
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.models.user import User

from app.schemas.scan import (
    ExecutorStatus,
    ScanOperationsResponse,
    ScanResponse,
)

from app.scanners.manager import ScannerManager
from app.scanners.nmap import (
    NmapParser,
    ScanResultMapper,
)
from app.scanners.nmap.scanner import (
    build_nmap_args,
    clear_scan_cancelled,
    is_scan_cancelled,
    mark_scan_cancelled,
    nmap_available,
    nmap_unavailable_message,
    terminate_scan_process,
)

from app.services.finding_service import create_findings
from app.services.intelligence_service import enrich_service
from app.services.notification_service import notify_scan_critical_findings
from app.services.activity_service import record_activity
from app.services.alert_service import evaluate_finding_alert, notify_scan_outcome_alert
from app.ws.hub import scan_event_hub


scanner_manager = ScannerManager()
parser = NmapParser()


def create_scan(
    db: Session,
    asset: Asset,
    scan_profile: ScanProfile = ScanProfile.STANDARD,
) -> Scan:

    if validate_scan_target(asset.ip_address) is None and validate_scan_target(
        asset.domain
    ) is None:
        raise ValidationError(
            "Asset has no scannable IP address or domain."
        )

    if not nmap_available():
        raise ValidationError(nmap_unavailable_message())

    scan = Scan(
        asset_id=asset.id,
        scanner="nmap",
        scan_profile=scan_profile.value,
        status=ScanStatus.PENDING,
    )

    db.add(scan)
    db.commit()
    db.refresh(scan)

    scan_executor.submit(scan.id)

    _publish_scan_event(scan, asset.created_by)

    record_activity(
        db,
        user_id=asset.created_by,
        action="scan_started",
        entity_type="scan",
        entity_id=scan.id,
        detail=f"Started scan #{scan.id} on {asset.name}",
        meta={"profile": scan.scan_profile},
    )

    db.commit()

    return scan


def _publish_scan_event(
    scan: Scan,
    owner_user_id: int,
) -> None:
    """
    Broadcast a scan lifecycle event to any connected WebSocket clients.

    ``owner_user_id`` scopes delivery to the user who owns the scanned asset,
    so clients never observe another tenant's scans.
    """

    scan_event_hub.publish(
        {
            "type": "scan.updated",
            "scan_id": scan.id,
            "status": (
                scan.status.value
                if hasattr(scan.status, "value")
                else str(scan.status)
            ),
            "asset_id": scan.asset_id,
            "user_id": owner_user_id,
        }
    )


def run_scan_in_background(scan_id: int) -> None:
    """
    Execute a scan outside the HTTP request cycle.

    A scan can take up to the nmap host-timeout, so it must never block
    the request thread. Each background scan uses its own DB session.
    """

    db = SessionLocal()

    try:
        execute_scan(
            scan_id,
            db,
        )
    except Exception:
        logger.exception(
            "Background scan %s failed.",
            scan_id,
        )
    finally:
        clear_scan_cancelled(scan_id)
        db.close()


def execute_scan(
    scan_id: int,
    db: Session,
):

    scan = db.query(Scan).filter(
        Scan.id == scan_id,
    ).first()

    if scan is None:
        raise ResourceNotFoundError("Scan not found")

    if scan.status == ScanStatus.CANCELLED or is_scan_cancelled(
        scan.id
    ):
        return scan

    asset = db.query(Asset).filter(
        Asset.id == scan.asset_id,
    ).first()

    if asset is None:
        raise ResourceNotFoundError("Asset not found")

    try:

        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.now(UTC)

        db.commit()

        _publish_scan_event(scan, asset.created_by)

        target = asset.ip_address or asset.domain

        if target is None:
            raise RuntimeError(
                f"Asset {asset.id} has no IP address or domain to scan"
            )

        logger.info(
            "Running Nmap against %s",
            target,
        )

        if not nmap_available():
            raise RuntimeError(nmap_unavailable_message())

        xml = scanner_manager.run(
            scanner="nmap",
            target=target,
            scan_id=scan.id,
            arguments=build_nmap_args(scan.scan_profile),
        )

        logger.info(
            "Nmap scan completed.",
            extra={"scan_id": scan.id},
        )

        services = parser.parse(xml)

        timed_out = parser.count_timed_out_hosts(xml)

        if timed_out > 0:

            logger.warning(
                "%d host(s) timed out during scan; results may be incomplete",
                timed_out,
                extra={"scan_id": scan.id},
            )

        logger.info(
            "%d services discovered",
            len(services),
        )

        for service in services:

            result = ScanResultMapper.to_model(
                scan.id,
                service,
            )

            db.add(result)
            db.flush()

            try:

                intel = enrich_service(
                    product=result.product,
                    version=result.version,
                )

                create_findings(
                    db=db,
                    scan_result=result,
                    cves=intel.get(
                        "cves",
                        [],
                    ),
                )

            except Exception as exc:

                logger.warning(
                    "Intelligence failed: %s",
                    exc,
                )

        db.commit()

        critical_findings = (
            db.query(Finding)
            .join(
                ScanResult,
                Finding.scan_result_id == ScanResult.id,
            )
            .filter(
                ScanResult.scan_id == scan.id,
                Finding.severity.in_(["CRITICAL", "HIGH"]),
            )
            .order_by(
                Finding.id.asc(),
            )
            .all()
        )

        notify_scan_critical_findings(
            db,
            scan,
            asset.created_by,
            critical_findings,
        )

        for finding in critical_findings:
            if finding.severity == "CRITICAL":
                evaluate_finding_alert(
                    db,
                    finding,
                    user_id=asset.created_by,
                )

        scan.status = ScanStatus.COMPLETED
        scan.finished_at = datetime.now(UTC)

        db.commit()
        db.refresh(scan)

        _publish_scan_event(scan, asset.created_by)

        record_activity(
            db,
            user_id=asset.created_by,
            action="scan_completed",
            entity_type="scan",
            entity_id=scan.id,
            detail=f"Scan #{scan.id} completed on {asset.name}",
            meta={
                "critical": len([f for f in critical_findings if f.severity == "CRITICAL"]),
                "high": len([f for f in critical_findings if f.severity == "HIGH"]),
            },
        )

        db.commit()

        logger.info(
            "Scan completed successfully.",
            extra={"scan_id": scan.id},
        )

        return scan

    except Exception:

        db.rollback()

        if is_scan_cancelled(scan.id):

            scan.status = ScanStatus.CANCELLED
            scan.finished_at = datetime.now(UTC)

            db.commit()

            _publish_scan_event(scan, asset.created_by)

            record_activity(
                db,
                user_id=asset.created_by,
                action="scan_cancelled",
                entity_type="scan",
                entity_id=scan.id,
                detail=f"Scan #{scan.id} cancelled on {asset.name}",
            )

            db.commit()

            logger.info(
                "Scan %d cancelled.",
                scan.id,
            )

            return scan

        scan.status = ScanStatus.FAILED
        scan.finished_at = datetime.now(UTC)

        db.commit()

        notify_scan_outcome_alert(
            db,
            scan,
            asset,
            success=False,
        )

        db.commit()

        _publish_scan_event(scan, asset.created_by)

        record_activity(
            db,
            user_id=asset.created_by,
            action="scan_failed",
            entity_type="scan",
            entity_id=scan.id,
            detail=f"Scan #{scan.id} failed on {asset.name}",
        )

        db.commit()

        logger.exception(
            "Scan failed.",
            extra={"scan_id": scan.id},
        )

        raise


def get_asset_for_scan(
    db: Session,
    asset_id: int,
    current_user: User,
):

    query = db.query(Asset).filter(
        Asset.id == asset_id,
    )

    query = apply_asset_scope(query, current_user)

    return query.first()


def _get_finding_counts(
    db: Session,
    scan_ids: list[int],
) -> dict[int, int]:
    """
    Return the number of findings recorded for each scan id.
    """

    if not scan_ids:
        return {}

    rows = (
        db.query(
            ScanResult.scan_id,
            func.count(Finding.id),
        )
        .join(
            Finding,
            Finding.scan_result_id == ScanResult.id,
            isouter=True,
        )
        .filter(
            ScanResult.scan_id.in_(scan_ids),
        )
        .group_by(
            ScanResult.scan_id,
        )
        .all()
    )

    return {
        scan_id: count
        for scan_id, count in rows
    }


def _serialize_scan(
    scan: Scan,
    asset_name: str | None,
    finding_count: int,
) -> ScanResponse:
    """
    Build the scan response payload with asset and findings context.
    """

    return ScanResponse(
        id=scan.id,
        asset_id=scan.asset_id,
        asset_name=asset_name,
        status=scan.status,
        scanner=scan.scanner,
        scan_profile=ScanProfile(scan.scan_profile),
        started_at=scan.started_at,
        finished_at=scan.finished_at,
        created_at=scan.created_at,
        finding_count=finding_count,
    )


def get_scans(
    db: Session,
    current_user: User,
):

    query = (
        db.query(
            Scan,
            Asset.name.label("asset_name"),
        )
        .join(
            Asset,
            Scan.asset_id == Asset.id,
        )
    )

    query = apply_asset_scope(query, current_user)

    rows = query.order_by(
        Scan.created_at.desc(),
    ).all()

    counts = _get_finding_counts(
        db,
        [scan.id for scan, _ in rows],
    )

    return [
        _serialize_scan(
            scan,
            asset_name,
            counts.get(scan.id, 0),
        )
        for scan, asset_name in rows
    ]


def get_scan(
    db: Session,
    scan_id: int,
    current_user: User,
):

    query = (
        db.query(
            Scan,
            Asset.name.label("asset_name"),
        )
        .join(
            Asset,
            Scan.asset_id == Asset.id,
        )
        .filter(
            Scan.id == scan_id,
        )
    )

    query = apply_asset_scope(query, current_user)

    row = query.first()

    if row is None:
        return None

    scan, asset_name = row

    counts = _get_finding_counts(
        db,
        [scan.id],
    )

    return _serialize_scan(
        scan,
        asset_name,
        counts.get(scan.id, 0),
    )


def get_scan_results(
    db: Session,
    scan_id: int,
    current_user: User,
):

    query = (
        db.query(ScanResult)
        .join(
            Scan,
            ScanResult.scan_id == Scan.id,
        )
        .join(
            Asset,
            Scan.asset_id == Asset.id,
        )
        .filter(
            Scan.id == scan_id,
        )
    )

    query = apply_asset_scope(query, current_user)

    return query.order_by(
        ScanResult.port.asc(),
    ).all()


def cancel_scan(
    db: Session,
    scan_id: int,
    current_user: User,
) -> Scan | None:
    """
    Cancel a running or pending scan.

    Returns the scan model, or None when the scan does not exist
    or is not visible to the user.
    """

    query = (
        db.query(Scan, Asset.created_by)
        .join(
            Asset,
            Scan.asset_id == Asset.id,
        )
        .filter(
            Scan.id == scan_id,
        )
    )

    query = apply_asset_scope(query, current_user)

    row = query.first()

    if row is None:
        return None

    scan, owner_user_id = row

    if scan.status not in (
        ScanStatus.PENDING,
        ScanStatus.RUNNING,
    ):
        raise ValidationError("Scan is not running.")

    mark_scan_cancelled(scan.id)

    scan.status = ScanStatus.CANCELLED
    scan.finished_at = datetime.now(UTC)

    db.commit()

    _publish_scan_event(scan, owner_user_id)

    terminate_scan_process(scan.id)

    return scan


def get_scan_operations(
    db: Session,
    current_user: User,
) -> ScanOperationsResponse:
    """
    Return executor status and scan status counts scoped to the user.
    """

    query = (
        db.query(
            Scan.status,
            func.count(Scan.id),
        )
        .join(
            Asset,
            Scan.asset_id == Asset.id,
        )
    )

    query = apply_asset_scope(query, current_user)

    counts: dict[str, int] = {}
    total = 0

    for status, count in query.group_by(Scan.status).all():
        key = status.value if hasattr(status, "value") else str(status)
        counts[key] = count
        total += count

    executor_status = scan_executor.status()

    return ScanOperationsResponse(
        executor=ExecutorStatus(
            **executor_status,
        ),
        counts=counts,
        total=total,
    )
