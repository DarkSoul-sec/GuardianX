from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.detection.phishing.schemas import (
    PhishingAnalysisRequest,
    PhishingAnalysisResponse,
)
from app.detection.phishing.service import analyze_url
from app.integrations.virustotal.service import get_optional_api_key
from app.models.user import User

router = APIRouter(
    prefix="/phishing",
    tags=["Phishing Detection"],
)


@router.post(
    "/analyze",
    response_model=PhishingAnalysisResponse,
    summary="Analyze a URL for phishing indicators",
)
def analyze_phishing(
    request: PhishingAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return analyze_url(
        request.url,
        virustotal_api_key=get_optional_api_key(db, current_user.id),
    )
