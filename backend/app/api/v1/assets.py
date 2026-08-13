from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.logger import logger
from app.schemas.asset import (
    AssetCreate,
    AssetDetailResponse,
    AssetResponse,
    AssetUpdate,
)
from app.services.asset_service import (
    create_asset,
    delete_asset,
    get_all_assets,
    get_asset_by_id,
    get_asset_details,
    update_asset,
)
from app.services.activity_service import record_activity

router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
)


@router.post(
    "",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_asset(
    asset: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_asset = create_asset(
        db=db,
        asset=asset,
        created_by=current_user.id,
    )

    record_activity(
        db,
        user_id=current_user.id,
        action="asset_created",
        entity_type="asset",
        entity_id=db_asset.id,
        detail=f"Created asset {db_asset.name}",
    )
    db.commit()

    return db_asset


@router.get(
    "",
    response_model=List[AssetResponse],
)
def list_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_all_assets(db, current_user)


@router.get(
    "/{asset_id}",
    response_model=AssetDetailResponse,
)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Asset details requested: %s", asset_id)

    asset = get_asset_details(db, asset_id, current_user)

    if asset is None:
        logger.warning("Asset not found: %s", asset_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found.",
        )

    logger.info("Asset found: %s", asset_id)
    return asset


@router.patch(
    "/{asset_id}",
    response_model=AssetResponse,
)
def edit_asset(
    asset_id: int,
    data: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    asset = get_asset_by_id(
        db,
        asset_id,
        current_user,
    )

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found.",
        )

    db_asset = update_asset(
        db,
        asset,
        data,
    )

    record_activity(
        db,
        user_id=current_user.id,
        action="asset_updated",
        entity_type="asset",
        entity_id=db_asset.id,
        detail=f"Updated asset {db_asset.name}",
    )
    db.commit()

    return db_asset


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    asset = get_asset_by_id(
        db,
        asset_id,
        current_user,
    )

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found.",
        )

    record_activity(
        db,
        user_id=current_user.id,
        action="asset_deleted",
        entity_type="asset",
        entity_id=asset.id,
        detail=f"Deleted asset {asset.name}",
    )

    delete_asset(
        db,
        asset,
    )

    return None
