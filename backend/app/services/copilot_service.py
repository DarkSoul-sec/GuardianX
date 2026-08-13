from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.copilot import (
    CopilotIntent,
    detect_intent,
    get_copilot_provider,
)
from app.copilot import context as copilot_context
from app.copilot import memory as copilot_memory
from app.copilot import prompts as copilot_prompts
from app.copilot import sanitize as copilot_sanitize
from app.logger import logger
from app.models.user import User
from app.schemas.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotResolvedContext,
)


def _extract_results(data: dict) -> list[dict] | None:
    """
    Convert a natural-language search context into structured result rows
    for the UI. Returns None for every other intent.
    """

    if data.get("intent") != CopilotIntent.NATURAL_LANGUAGE_SEARCH:
        return None

    results: list[dict] = []

    for finding in data.get("findings", [])[:10]:
        results.append(
            {
                "kind": "finding",
                "id": finding.get("id"),
                "title": finding.get("cve") or finding.get("title", ""),
                "detail": finding.get("title", ""),
                "severity": finding.get("severity"),
                "status": finding.get("status"),
                "score": (
                    str(finding["cvss"])
                    if finding.get("cvss") is not None
                    else None
                ),
            }
        )

    for asset in data.get("assets", [])[:10]:
        results.append(
            {
                "kind": "asset",
                "id": asset.get("id"),
                "title": asset.get("name", ""),
                "detail": asset.get("asset_type"),
                "severity": None,
                "status": None,
                "score": None,
            }
        )

    for service in data.get("services", [])[:10]:
        results.append(
            {
                "kind": "service",
                "id": None,
                "title": service.get("service", ""),
                "detail": (
                    f"{service.get('asset', '')} "
                    f"({service.get('port')}/{service.get('protocol', 'tcp')})"
                ),
                "severity": None,
                "status": None,
                "score": None,
            }
        )

    return results or None


def _build_prompts(
    request: CopilotChatRequest,
    intent: CopilotIntent,
    data: dict,
    current_user: User,
) -> tuple[str, str]:
    """
    Construct the system and user prompts, embedding any recent conversation
    memory and applying secret sanitization to free text.
    """

    message = copilot_sanitize.sanitize_prompt(request.message or "")

    recap = copilot_memory.build_recap(current_user.id)

    system_prompt = copilot_prompts.build_system_prompt(intent, data)
    user_prompt = copilot_prompts.build_user_prompt(
        intent,
        message,
        data,
    )

    if recap:
        user_prompt = f"{recap}\n\n{user_prompt}"

    return system_prompt, user_prompt


def _resolve_intent(
    request: CopilotChatRequest,
) -> CopilotIntent:
    return request.type or detect_intent(
        request.message,
        asset_id=request.asset_id,
        finding_id=request.finding_id,
    )


def chat(
    request: CopilotChatRequest,
    db: Session,
    current_user: User,
) -> CopilotChatResponse:
    """
    Orchestrate a Copilot request: resolve intent, gather context, prompt
    the active provider, and return a structured answer.
    """

    intent = _resolve_intent(request)

    built = copilot_context.build_context(
        db,
        current_user,
        request,
        intent,
    )

    if built["data"] is None:
        reason = built["reason"] or (
            "I couldn't gather the context needed to answer that."
        )
        provider = get_copilot_provider()

        return CopilotChatResponse(
            answer=reason,
            intent=intent,
            provider=provider.name,
            model=provider.model,
            context=CopilotResolvedContext(**built["resolved"]),
        )

    data = built["data"]
    provider = get_copilot_provider()

    system_prompt, user_prompt = _build_prompts(
        request,
        intent,
        data,
        current_user,
    )

    logger.info(
        "Copilot chat: user=%s intent=%s provider=%s",
        current_user.id,
        intent.value,
        provider.name,
    )

    answer = provider.complete(
        system_prompt,
        user_prompt,
        data,
    )

    copilot_memory.push(
        current_user.id,
        "user",
        copilot_sanitize.sanitize_prompt(request.message),
        intent=intent,
        resolved=built["resolved"],
    )
    copilot_memory.push(
        current_user.id,
        "assistant",
        answer,
        intent=intent,
        resolved=built["resolved"],
    )

    return CopilotChatResponse(
        answer=answer,
        intent=intent,
        provider=provider.name,
        model=provider.model,
        context=CopilotResolvedContext(**built["resolved"]),
        results=_extract_results(data),
    )


def stream_chat(
    request: CopilotChatRequest,
    db: Session,
    current_user: User,
) -> Iterator[dict]:
    """
    Stream a Copilot answer as discrete events.

    Yields ``{"type": "meta", ...}`` first, then one ``{"type": "token",
    "content": ...}`` per chunk, and finally ``{"type": "done", ...}`` with
    the resolved context and structured results.
    """

    intent = _resolve_intent(request)

    built = copilot_context.build_context(
        db,
        current_user,
        request,
        intent,
    )

    provider = get_copilot_provider()

    if built["data"] is None:
        reason = built["reason"] or (
            "I couldn't gather the context needed to answer that."
        )
        yield {
            "type": "meta",
            "intent": intent.value,
            "provider": provider.name,
            "model": provider.model,
            "context": built["resolved"],
        }
        yield {
            "type": "done",
            "content": reason,
            "context": built["resolved"],
            "results": None,
        }
        return

    data = built["data"]

    system_prompt, user_prompt = _build_prompts(
        request,
        intent,
        data,
        current_user,
    )

    logger.info(
        "Copilot stream: user=%s intent=%s provider=%s",
        current_user.id,
        intent.value,
        provider.name,
    )

    yield {
        "type": "meta",
        "intent": intent.value,
        "provider": provider.name,
        "model": provider.model,
        "context": built["resolved"],
    }

    answer_parts: list[str] = []

    for token in provider.stream(
        system_prompt,
        user_prompt,
        data,
    ):
        answer_parts.append(token)
        yield {
            "type": "token",
            "content": token,
        }

    answer = "".join(answer_parts).strip()

    copilot_memory.push(
        current_user.id,
        "user",
        copilot_sanitize.sanitize_prompt(request.message),
        intent=intent,
        resolved=built["resolved"],
    )
    copilot_memory.push(
        current_user.id,
        "assistant",
        answer,
        intent=intent,
        resolved=built["resolved"],
    )

    yield {
        "type": "done",
        "content": answer,
        "context": built["resolved"],
        "results": _extract_results(data),
    }
