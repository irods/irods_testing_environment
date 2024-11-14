# grown-up modules
import textwrap


def add_compose_args(parser):
    """Add argparse options related to Docker Compose project.

    Arguments:
    parser -- argparse.ArgumentParser to augment
    """
    parser.add_argument(
        "--project-directory",
        metavar="PATH_TO_PROJECT_DIRECTORY",
        dest="project_directory",
        default=".",
        help="Path to Compose project on which packages will be installed.",
    )

    parser.add_argument(
        "--project-name",
        metavar="PROJECT_NAME",
        dest="project_name",
        help="Name of Compose project on which to install packages.",
    )


def add_irods_package_args(parser):
    """Add argparse options related to to-be-installed iRODS packages.

    Arguments:
    parser -- argparse.ArgumentParser to augment
    """
    parser.add_argument(
        "--irods-package-directory",
        metavar="PATH_TO_DIRECTORY_WITH_PACKAGES",
        dest="package_directory",
        help="Path to local directory which contains iRODS packages.",
    )

    parser.add_argument(
        "--irods-package-version",
        metavar="PACKAGE_VERSION_TO_DOWNLOAD",
        dest="package_version",
        help=textwrap.dedent(
            """\
                            Version of official iRODS packages to download and install. \
                            If neither this or --irods-package-directory are specified, \
                            the latest available version will be installed. Can be used \
                            with --use-static-image to avoid downloading packages."""
        ),
    )

    parser.add_argument(
        "--irods-externals-package-directory",
        metavar="PATH_TO_DIRECTORY_WITH_IRODS_EXTERNALS_PACKAGES",
        dest="irods_externals_package_directory",
        help="Path to local directory which contains iRODS externals packages.",
    )

    parser.add_argument(
        "--use-static-image",
        dest="install_packages",
        default=True,
        action="store_false",
        help=textwrap.dedent(
            """\
                            If specified, a Docker image which has pre-installed iRODS \
                            packages will be used instead of installing the packages at \
                            runtime. This is incompatible with --irods-package-directory. \
                            --irods-package-version must be specified to use this option."""
        ),
    )


def add_irods_plugin_args(parser):
    """Add argparse options related to iRODS plugin test hooks.

    Arguments:
    parser -- argparse.ArgumentParser to augment
    """
    parser.add_argument(
        "plugin_name",
        metavar="PLUGIN_GIT_REPOSITORY_NAME",
        help="Repository name for the plugin being installed.",
    )

    parser.add_argument(
        "--plugin-package-directory",
        metavar="PATH_TO_DIRECTORY_WITH_PACKAGES",
        dest="plugin_package_directory",
        help="Path to local directory which contains iRODS plugin packages.",
    )

    # TODO: implement support
    # parser.add_argument('--plugin-package-version',
    # metavar='PACKAGE_VERSION_TO_DOWNLOAD',
    # dest='plugin_package_version',
    # help=textwrap.dedent('''\
    # Version of official iRODS plugin packages to download and install. \
    # If neither this or --plugin-package-directory are specified, \
    # the latest available version will be installed.'''))


def add_irods_test_args(parser):
    """Add argparse options related to iRODS tests and the test environment.

    Arguments:
    parser -- argparse.ArgumentParser to augment
    """
    parser.add_argument(
        "--tests",
        metavar="TESTS",
        nargs="+",
        help=textwrap.dedent(
            """\
                            Space-delimited list of tests to be run. If not provided, \
                            ALL tests will be run (--run_python-suite)."""
        ),
    )

    parser.add_argument(
        "--output-directory",
        "-o",
        metavar="FULLPATH_TO_DIRECTORY_FOR_OUTPUT",
        dest="output_directory",
        help="Full path to local directory for output from execution. \
                              Individual job runs will appear as subdirectories in this \
                              directory. Defaults to temporary directory.",
    )

    parser.add_argument(
        "--job-name",
        "-j",
        metavar="JOB_NAME",
        dest="job_name",
        help="Name of the directory where output from a specific job will \
                              appear within the output directory. Defaults to a UUID.",
    )

    parser.add_argument(
        "--fail-fast",
        dest="fail_fast",
        action="store_true",
        help=textwrap.dedent(
            """\
                            If indicated, exits on the first test that returns a non-zero exit \
                            code."""
        ),
    )

    parser.add_argument(
        "--concurrent-test-executor-count",
        dest="executor_count",
        type=int,
        default=1,
        help=textwrap.dedent(
            """\
                            Number of concurrent executors to run tests at the same time."""
        ),
    )

    parser.add_argument(
        "--discard-logs",
        dest="save_logs",
        default=True,
        action="store_false",
        help=textwrap.dedent(
            """\
                            Indicates that the logs should not be collected from the \
                            containers."""
        ),
    )

    parser.add_argument(
        "--leak-containers",
        action="store_false",
        dest="cleanup_containers",
        help="If indicated, the containers will not be torn down.",
    )

    parser.add_argument(
        "--skip-setup",
        action="store_false",
        dest="do_setup",
        help="If indicated, the iRODS servers will not be set up.",
    )


def add_database_config_args(parser):
    """Add argparse options related to setting up and configuring iRODS.

    Arguments:
    parser -- argparse.ArgumentParser to augment
    """
    parser.add_argument(
        "--odbc-driver-path",
        metavar="PATH_TO_ODBC_DRIVER_ARCHIVE",
        dest="odbc_driver",
        help=textwrap.dedent(
            """\
                            Path to the ODBC driver archive file on the local machine. \
                            If not provided, the driver will be downloaded."""
        ),
    )


def add_common_args(parser):
    """Add argparse options common to irods_testing_environment scripts.

    Arguments:
    parser -- argparse.ArgumentParser to augment
    """
    parser.add_argument(
        "--verbose",
        "-v",
        dest="verbosity",
        action="count",
        default=1,
        help=textwrap.dedent(
            """\
                            Increase the level of output to stdout. \
                            CRITICAL and ERROR messages will always be printed. \
                            Add more to see more log messages (e.g. -vvv displays DEBUG)."""
        ),
    )


def log_irods_version_and_commit_id(container):
    """Prints the version and commit_id found in the JSON version file.

    Arguments:
    container -- Container which has the version file
    """
    import logging
    from irods_testing_environment import irods_config

    version = ".".join([str(i) for i in irods_config.get_irods_version(container)])
    sha = irods_config.get_irods_commit_id(container)
    logging.error(f"version:[{version}]")
    logging.error(f"sha:[{sha}]")
