# grown-up imports
import logging
import os
import tarfile
import tempfile

# local modules
from . import execute


def create_archive(members, filename="foo", extension="tar"):
    """Create a local archive file with the files in `members` and return a path to the file.

    Arguments:
    members -- local files to be placed in the archive
    """
    # TODO: allow for path to be specified
    # TODO: allow for type of archive to be specified
    # Create a tarfile with the packages
    tarfile_name = ".".join([filename, extension])
    tarfile_path = os.path.join(tempfile.mkdtemp(), tarfile_name)

    logging.debug("creating tarfile [{}]".format(tarfile_path))

    with tarfile.open(tarfile_path, "w") as f:
        for m in members:
            logging.debug("adding member [{0}] to tarfile".format(m))
            f.add(m)

    return tarfile_path


def extract_archive(path_to_archive, path_to_extraction=None):
    """Extract the contents of an archive to a directory and return the path to the directory.

    Arguments:
    path_to_archive -- path to the archive file which is to be extracted
    path_to_extraction -- path to the directory into which the contents will be extracted
                          (if None is provided, a temporary directory is created)
    """
    if path_to_extraction:
        dest = os.path.abspath(path_to_extraction)
    else:
        dest = os.path.join(tempfile.mkdtemp())

    p = os.path.abspath(path_to_archive)

    logging.debug("extracting archive [{}] [{}]".format(p, dest))

    with tarfile.open(p, "r") as f:

        def is_within_directory(directory, target):

            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)

            prefix = os.path.commonprefix([abs_directory, abs_target])

            return prefix == abs_directory

        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):

            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")

            tar.extractall(path, members, numeric_owner=numeric_owner)

        safe_extract(f, path=dest)

    return dest


def path_to_archive_in_container(archive_file_path_on_host, extension="tar"):
    """Return path to directory containing extracted archive when copied to container."""
    return (
        "/"
        + os.path.basename(os.path.abspath(archive_file_path_on_host))[
            : (len(extension) + 1) * -1
        ]
    )


def copy_archive_to_container(container, archive_file_path_on_host, extension="tar"):
    """Copy local archive file into the specified container in extracted form.

    Returns the absolute path inside the container where the archive file was extracted.

    Arguments:
    container -- the docker container into which the archive is being copied
    archive_file_path_on_host -- local path to the archive being copied
    """
    dir_path = path_to_archive_in_container(archive_file_path_on_host, extension)

    logging.debug(
        "putting archive [{0}] in container [{1}] at [{2}]".format(
            archive_file_path_on_host, container.name, dir_path
        )
    )

    with open(archive_file_path_on_host, "rb") as tf:
        if not container.put_archive("/", tf):
            raise RuntimeError(
                "failed to put archive in container [{}]".format(container.name)
            )

    return dir_path


def copy_from_container(
    container,
    path_to_source_on_container,
    path_to_destination_directory_on_host=None,
    cleanup=True,
    extract=True,
):
    """Copies a file or directory from a path inside the specified container to the local host.

    This functions just like `docker cp` on the CLI if the default options are used except
    `path_to_destination_directory_on_host` will put its contents in a temporary directory if
    NOne is provided.

    `cleanup` and `extract` can lead to unexpected results if used in certain ways, so the
    possibilities will be described here:

    cleanup     extract     return                          result
    --------------------------------------------------------------
    False       False       path to archive file            no extracted contents, archive file
    False       True        path to extracted contents      extracted contents, archive file
    True        False       path to extracted contents      no extracted contents, no archive
    True        True        path to extracted contents      extracted contents, no archive

    The cleanup == True and extract == False case results in no files and a path to something
    which does not exist because the archive file is copied out, not extracted, and then
    deleted. Therefore, a ValueError is raised if this combination is used. The other option
    combinations are valid use cases.

    Arguments:
    container -- the Docker container from which the file or directory is to be copied
    path_to_source_on_container -- path to the source file or directory inside the container
                                   (this should be an absolute path)
    path_to_destination_directory_on_host -- the directory into which the file or directory
                                             will be copied on the host machine (if None is
                                             provided, a temporary directory is created)
    cleanup -- if True, removes the archive file after it has been extracted
    extract -- if True, extracts the contents of the archive file after it has been copied
    """
    if cleanup and not extract:
        raise ValueError(
            "cleanup without extraction is a no-op so these are considered incompatible options"
        )

    if path_to_destination_directory_on_host:
        dest = os.path.abspath(path_to_destination_directory_on_host)
    else:
        dest = os.path.join(tempfile.mkdtemp())

    logging.debug(
        "copying file [{}] in container [{}] to [{}]".format(
            path_to_source_on_container, container.name, dest
        )
    )

    archive_path = os.path.join(dest, container.name + ".tar")

    try:
        bits, _ = container.get_archive(path_to_source_on_container)

        with open(archive_path, "wb") as f:
            for chunk in bits:
                f.write(chunk)

        if extract:
            return extract_archive(archive_path, dest)

    except Exception as e:
        logging.error(e)
        raise

    finally:
        if cleanup and os.path.exists(archive_path):
            os.unlink(archive_path)

    return dest if cleanup else archive_path


def copy_files_in_container(container, sources_and_destinations):
    """Copy files in container from source to destination.

    Arguments:
    container -- the docker.Container in which files will be copied
    sources_and_destinations -- a list of tuples of source paths and destination paths
    """
    tarfile = create_archive([s for s, d in sources_and_destinations], "ssl")
    _ = copy_archive_to_container(container, tarfile)

    for s, d in sources_and_destinations:
        logging.debug(
            "copying source [{}] in container to destination in container [{}] [{}]".format(
                s, d, container.name
            )
        )

        if execute.execute_command(container, "cp {} {}".format(s, d)) != 0:
            raise RuntimeError(
                "failed to copy file src [{}] dest [{}] [{}]".format(
                    s, d, container.name
                )
            )


def collect_files_from_containers(
    docker_client, containers, paths_to_copy_from_containers, output_directory_on_host
):
    """Collect files from containers into a single output directory on the host.

    Arguments:
    docker_client -- the Docker client for communicating with the daemon
    containers -- list of Containers from which paths will be copied
    paths_to_copy_from_containers -- list of path-likes which will be copied from the containers
    output_directory_on_host -- the output directory on the host where files will be copied
    """
    for c in containers:
        od = os.path.join(output_directory_on_host, "logs", c.name)
        if not os.path.exists(od):
            os.makedirs(od)

        logging.info(
            f"saving files in [{paths_to_copy_from_containers}] to [{od}] [{c.name}]"
        )

        source_container = docker_client.containers.get(c.name)

        for p in paths_to_copy_from_containers:
            copy_from_container(source_container, p, od)


def put_string_to_file(container, target_file, string):
    """Echo `string` into `target_file` in `container`, overwriting existing contents.

    Arguments:
    container -- docker.Container where the target_file is hosted
    target_file -- the path inside the container with the contents to overwrite
    string -- contents to echo into the target file
    """
    if (
        execute.execute_command(
            container, f"bash -c 'echo \"{string}\" > {target_file}'"
        )
        != 0
    ):
        raise RuntimeError(
            f"[{container.name}] failed to put string to file [{target_file}]"
        )
