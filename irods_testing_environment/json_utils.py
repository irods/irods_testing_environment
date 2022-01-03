# grown-up modules
import json
import os

def get_json_from_file(container, target_file):
    """Return a JSON structure read out from a JSON file on the specified container.

    Arguments:
    container -- docker.Container where the target_file is hosted
    target_file -- the path inside the container with the JSON contents to modify
    """
    import archive
    import shutil
    json_file = os.path.join(archive.copy_from_container(container, target_file),
                             os.path.basename(target_file))

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
    import execute
    # TODO: Should we make a local file and copy it in?
    put_json = 'bash -c \'echo "{}" > {}\''.format(json.dumps(json_contents).replace('"', '\\"'),
                                                   target_file)
    if execute.execute_command(container, put_json) is not 0:
        raise RuntimeError('failed to put json to file [{}] [{}}'.format(target_file,
                                                                         container.name))
