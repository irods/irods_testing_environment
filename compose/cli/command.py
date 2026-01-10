"""Shim for compose.cli.command.get_project used by this repo."""

from ..project import Project


def get_project(project_dir, project_name=None, **kwargs):
    """
    Return a Project compatible with the legacy docker-compose API.

    Arguments:
        project_dir: Path to the Compose project directory.
        project_name: Name of the Compose project. Optional. Default is basename of the project directory.
        **kwargs: Keyword arguments used in Project initialization.

    Returns:
        Instance of a Project using provided `project_dir` and `project_name`.
    """
    return Project(project_dir, project_name=project_name, **kwargs)
