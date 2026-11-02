"""Structured results returned by iterative numerical methods."""
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class IterationResult(Generic[T]):
    approximation: T
    iteration_count: int
    residual: float
    converged: bool
    history: list

    def __iter__(self):
        """Keep the original ``value, history = result`` calling convention."""
        yield self.approximation
        yield self.history

    def __len__(self):
        return 2

    def __getitem__(self, index):
        return (self.approximation, self.history)[index]
