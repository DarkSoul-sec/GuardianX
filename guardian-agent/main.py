"""Guardian Agent entry point.

Loads configuration, wires the agent, and runs it until SIGTERM/SIGINT.
"""

from __future__ import annotations

import argparse
import signal
import sys
import threading

from agent.bootstrap import build_agent
from agent.config.loader import load_config
from agent.logging.structured import configure_logging, get_logger

log = get_logger("agent.main")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guardian Agent")
    parser.add_argument(
        "-c",
        "--config",
        default="agent.yaml",
        help="Path to the agent.yaml configuration file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    config = load_config(args.config)
    configure_logging(config.log_level, config.log_format, config.log_dir)

    runner = build_agent(config)
    shutdown = threading.Event()

    def _handle_signal(signum: int, _frame: object) -> None:
        log.info("signal received, shutting down: %s", signum)
        runner.stop()
        shutdown.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    runner.run()
    shutdown.wait()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))