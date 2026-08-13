from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.report import (
    AssetReport,
    ExecutiveReport,
    TechnicalReport,
)
from app.services.report_service import (
    build_asset_report,
    build_executive_report,
    build_scan_report,
)

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.get(
    "/executive",
    response_model=ExecutiveReport,
)
def get_executive_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return build_executive_report(
        db=db,
        current_user=current_user,
    )


@router.get(
    "/assets/{asset_id}",
    response_model=AssetReport,
)
def get_asset_report(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return build_asset_report(
        db=db,
        asset_id=asset_id,
        current_user=current_user,
    )


@router.get(
    "/scans/{scan_id}",
    response_model=TechnicalReport,
)
def get_scan_report(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return build_scan_report(
        db=db,
        scan_id=scan_id,
        current_user=current_user,
    )
