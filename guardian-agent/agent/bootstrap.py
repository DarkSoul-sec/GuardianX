"""Composition root for the agent.

All object construction happens here (within the :class:`Container`) so the
rest of the codebase is wired, not hard-coded. Swapping the HTTP transport,
store backend, log directory or a collector for a test double is a one-line
change.
"""

from __future__ import annotations

from agent.collectors.linux import linux_collectors
from agent.collectors.registry import CollectorRegistry
from agent.communication.client import ApiClient
from agent.config.loader import AgentConfig
from agent.core.clock import Clock, SystemClock
from agent.core.container import Container
from agent.core.normalizer import Normalizer
from agent.database.queue import DurableEventStore
from agent.logging.structured import configure_logging, get_logger
from agent.scheduler.runner import AgentRunner
from agent.security.manager import CredentialManager
from agent.security.state import StateStore

log = get_logger("agent.bootstrap")


def build_agent(
    config: AgentConfig,
    *,
    clock: Clock | None = None,
) -> AgentRunner:
    """Construct a fully wired :class:`AgentRunner` from ``config``."""
    configure_logging(config.log_level, config.log_format, config.log_dir)

    container = Container()
    effective_clock = clock or SystemClock()

    store = StateStore(config.state_path)
    credentials = CredentialManager(
        store=store,
        clock=effective_clock,
        config_agent_name=config.agent_name,
        registration_token=config.registration_token,
    )

    # The transport needs the manager (for tokens) and the manager needs the
    # transport (to register/refresh); wire them together once after building.
    client = ApiClient(config, credentials)
    credentials.provider = client

    registry = CollectorRegistry.from_config(config, linux_collectors())
    queue = DurableEventStore(config.queue_path)
    normalizer = Normalizer()

    container.register(Clock, effective_clock)
    container.register(StateStore, store)
    container.register(CredentialManager, credentials)
    container.register(ApiClient, client)
    container.register(CollectorRegistry, registry)
    container.register(DurableEventStore, queue)
    container.register(Normalizer, normalizer)

    runner = AgentRunner(
        config=config,
        registry=registry,
        queue=queue,
        client=client,
        credentials=credentials,
        clock=effective_clock,
        normalizer=normalizer,
    )
    container.register(AgentRunner, runner)
    return runner