"""Minimal compose Project implementation backed by Docker Compose CLI."""

import pathlib
import shutil
import subprocess

import docker

from .container import Container


def _sanitize_project_name(name):
    # Match legacy usage in this repo: strip characters compose v1 rejects.
    return name.replace(".", "").replace(":", "").replace("/", "")


class Project:
    """Subset of compose.project.Project used by this codebase."""

    def __init__(self, project_dir, project_name=None, docker_client=None):
        """Initialize a Compose Project with a project_dir."""
        self.project_dir = pathlib.Path(project_dir).resolve()
        base_name = pathlib.Path(self.project_dir).name
        name = project_name or base_name
        self.name = _sanitize_project_name(name)
        self._docker_client = docker_client or docker.from_env()

    def _compose_cmd(self, args):
        if not shutil.which("docker"):
            raise RuntimeError("docker CLI not found in PATH")
        cmd = ["docker", "compose", "-p", self.name]
        cmd.extend(args)
        subprocess.run(cmd, cwd=self.project_dir, check=True)

    def build(self):
        """Build the compose project images."""
        self._compose_cmd(["build"])

    def up(self, scale_override=None):
        """
        Start services with optional scale overrides, return containers.

        Returns:
            The list of Containers which were created/started.
        """
        args = ["up", "-d"]
        if scale_override:
            for service, count in scale_override.items():
                args.extend(["--scale", f"{service}={count}"])
        self._compose_cmd(args)
        return self.containers()

    def down(self, include_volumes=False, remove_image_type=False):
        """Stop and remove compose resources."""
        args = ["down"]
        if include_volumes:
            args.append("--volumes")
        if remove_image_type:
            args.extend(["--rmi", "all"])
        self._compose_cmd(args)

    def containers(self, service_names=None):
        """
        Return containers for this compose project, optionally filtered by service names.

        Arguments:
            service_names: List of services to filter from the full list of Containers. Default is None (no filter).

        Returns:
            List of Containers associated with this Project.
        """
        label_filters = [f"com.docker.compose.project={self.name}"]

        if not service_names:
            containers = self._docker_client.containers.list(all=True, filters={"label": label_filters})
            return [Container(c.name) for c in containers]

        containers = []
        for sn in service_names:
            f = {"label": [*label_filters, f"com.docker.compose.service={sn}"]}
            for c in self._docker_client.containers.list(all=True, filters=f):
                containers.append(c)

        return [Container(c.name) for c in containers]
