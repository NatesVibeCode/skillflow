"""Skillflow: a minimal SQLite-backed DAG runner."""

from .dag import Flow, FlowError

__all__ = ["Flow", "FlowError"]
__version__ = "0.2.0"
