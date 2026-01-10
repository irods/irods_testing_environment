"""
Minimal docker-compose shim for this project.

This module provides the subset of the legacy docker-compose Python API used by
the project, backed by the Docker Compose CLI and Docker SDK.
"""

from . import project

__all__ = ["project"]
