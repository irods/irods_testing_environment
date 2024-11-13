# grown-up modules
import json
import os

# local modules
from . import archive


def get_json_from_file(container, target_file):
    """Return a JSON structure read out from a JSON file on the specified container.

    Arguments:
    container -- docker.Container where the target_file is hosted
    target_file -- the path inside the container with the JSON contents to modify
    """
    import shutil
    from . import archive

    json_file = os.path.join(
        archive.copy_from_container(container, target_file),
        os.path.basename(target_file),
    )

    try:
        with open(json_file) as f:
            return json.load(f)

    finally:
        shutil.rmtree(os.path.dirname(json_file), ignore_errors=True)


def put_json_to_file(container, target_file, json_contents):
    """Put the json_contents to the target_file in container.

    Arguments:
    container -- docker.Container where the target_file is hosted
    target_file -- the path inside the container with the JSON contents to modify
    json_contents -- JSON contents to write to the target file in the container
    """
    json_str = json.dumps(json_contents, sort_keys=True, indent=4).replace('"', '\\"')
    archive.put_string_to_file(container, target_file, json_str)
