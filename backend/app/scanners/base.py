from abc import ABC, abstractmethod


class BaseScanner(ABC):
    """
    Base interface for every scanner.
    """

    @abstractmethod
    def scan(self, target: str):
        pass
