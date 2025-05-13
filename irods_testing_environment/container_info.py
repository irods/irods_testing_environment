def python(container):
    """Return command to run python appropriately per detected iRODS version in `container`."""
    # Just return python3 because all supported platforms use this... for now...
    return "python3"
