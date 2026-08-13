import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.copilot import CopilotProviderError, get_copilot_provider_info
from app.core.exceptions import ExternalServiceError
from app.logger import logger
from app.database.dependencies import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotMemoryClearResponse,
    CopilotMemoryStatus,
    CopilotProviderInfo,
)
from app.services.copilot_service import chat as copilot_chat
from app.services.copilot_service import stream_chat as copilot_stream_chat
from app.copilot import memory as copilot_memory

router = APIRouter(
    prefix="/copilot",
    tags=["AI Copilot"],
)


@router.post(
    "/chat",
    response_model=CopilotChatResponse,
)
def chat(
    request: CopilotChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return copilot_chat(request, db, current_user)
    except CopilotProviderError as error:
        logger.warning(
            "Copilot provider error for user %s: %s",
            current_user.id,
            error,
        )
        raise ExternalServiceError() from error


@router.post(
    "/chat/stream",
    summary="Stream a Copilot answer over SSE",
)
def chat_stream(
    request: CopilotChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Server-sent events: ``meta``, then ``token`` events, then ``done``.
    """

    def event_stream():
        try:
            for event in copilot_stream_chat(request, db, current_user):
                yield f"event: {event['type']}\ndata: {json.dumps(event, default=str)}\n\n"
        except CopilotProviderError as error:
            logger.warning(
                "Copilot stream error for user %s: %s",
                current_user.id,
                error,
            )
            yield (
                f"event: error\ndata: {json.dumps({'message': str(error)}, default=str)}\n\n"
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/provider",
    response_model=CopilotProviderInfo,
)
def provider_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_copilot_provider_info()


@router.get(
    "/memory",
    response_model=CopilotMemoryStatus,
    summary="Conversation memory status",
)
def memory_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return copilot_memory.status(current_user.id)


@router.delete(
    "/memory",
    response_model=CopilotMemoryClearResponse,
    summary="Clear conversation memory",
)
def memory_clear(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cleared = copilot_memory.clear(current_user.id)
    return CopilotMemoryClearResponse(cleared=cleared)
