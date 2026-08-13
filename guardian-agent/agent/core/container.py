"""A minimal, dependency-injection container.

The container keeps the agent's wiring in one place. Services register either
as ready instances (singletons) or lazy factories, and depend on each other
only through their registered interfaces — not by importing concrete classes.
This satisfies Dependency Injection and makes the whole graph trivially
replaceable in tests.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class Container:
    """Registers and resolves services by their interface type."""

    def __init__(self) -> None:
        self._instances: dict[type, Any] = {}
        self._factories: dict[type, Callable[[Container], Any]] = {}

    def register(self, interface: type[T], instance: T) -> None:
        if interface in self._instances or interface in self._factories:
            raise ValueError(f"service '{interface.__name__}' is already registered")
        self._instances[interface] = instance

    def register_factory(self, interface: type[T], factory: Callable[[Container], T]) -> None:
        if interface in self._instances or interface in self._factories:
            raise ValueError(f"service '{interface.__name__}' is already registered")
        self._factories[interface] = factory

    def resolve(self, interface: type[T]) -> T:
        instance = self._instances.get(interface)
        if instance is not None:
            return instance

        factory = self._factories.get(interface)
        if factory is None:
            raise KeyError(f"no service registered for '{interface.__name__}'")

        resolved = factory(self)
        self._instances[interface] = resolved
        return resolved

    def __contains__(self, interface: type) -> bool:
        return interface in self._instances or interface in self._factories