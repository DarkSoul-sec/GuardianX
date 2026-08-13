"""Normalization of raw collector observations.

The normalizer is the single choke point where collector output is wrapped
into the canonical :class:`EndpointEvent` wire format. Adding a new collector
never requires touching this module; each observation already declares its
own ``event_type`` and payload.
"""

from __future__ import annotations

from datetime import datetime

from agent.core.types import EndpointEvent, RawObservation


class Normalizer:
    """Wraps raw observations in the canonical event envelope."""

    def __init__(self, agent_id: str = "") -> None:
        self.agent_id = agent_id

    def normalize(
        self,
        source: str,
        observations: list[RawObservation],
        now: datetime,
    ) -> list[EndpointEvent]:
        return [
            EndpointEvent(
                agent_id=self.agent_id,
                source=source,
                event_type=o.event_type,
                severity=o.severity,
                timestamp=now,
                data=o.data,
            )
            for o in observations
        ]

    def normalize_one(
        self,
        source: str,
        observation: RawObservation,
        now: datetime,
    ) -> EndpointEvent:
        events = self.normalize(source, [observation], now)
        return events[0]