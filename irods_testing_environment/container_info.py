def python(container):
    """Return command to run python appropriately per detected iRODS version in `container`."""
    from . import irods_config

    major, minor, patch = irods_config.get_irods_version(container)

    return 'python' if minor < 3 else 'python3'
