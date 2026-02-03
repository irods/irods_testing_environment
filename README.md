# iRODS Testing Environment

This repository provides a series of [Docker Compose](https://docs.docker.com/compose/) files which are intended for use in a test framework - which may or may not exist at the time of writing - for [iRODS](https://irods.org). 

For each combination of supported OS platform/version and database type/version, there is a Compose project on which to run an iRODS deployment (*for testing*). The following OS platform Docker image tags are currently supported:
 - almalinux:8
 - almalinux:9
 - almalinux:10
 - rockylinux/rockylinux:8
 - rockylinux/rockylinux:9
 - rockylinux/rockylinux:10
 - debian:11
 - debian:12
 - debian:13
 - ubuntu:20.04
 - ubuntu:22.04
 - ubuntu:24.04

The following database Docker image tags are currently supported (although not for all platforms):
 - postgres:14
 - postgres:16
 - postgres:17
 - mariadb:10.6
 - mariadb:10.11
 - mariadb:11.4
 - mariadb:11.8
 - mysql:8.0
 - mysql:8.4

## Requirements

Python 3.9 or later, and recent versions of Git and pip are required to run this project.

It is *highly recommended* to use a `virtualenv` python virtual environment. You can set one up which installs the Minimum Requirements (see above) like this:
```bash
python3 -m virtualenv /path/to/new/virtualenv
source /path/to/new/virtualenv/bin/activate
python3 -m pip install docker GitPython cryptography
python3 -m pip freeze
```

## Run iRODS Tests

There are 3 main ways to run the iRODS test suite:
 - Core tests: assumes catalog service provider is the only server
 - Topology tests: assumes 1 catalog service provider and 3 catalog service consumers
 - Federation tests: assumes 2 federated catalog service providers

For the following examples, we will use ubuntu:22.04 for the platform and postgres:14 for the database.

To run the full iRODS python test suite as defined in [core_tests_list.json](https://github.com/irods/irods/blob/2e82164055d1e6c2a3c64eedc534b45c9449df07/scripts/core_tests_list.json) against locally built iRODS packages, run this:
```bash
python run_core_tests.py --project-directory ./projects/ubuntu-22.04/ubuntu-22.04-postgres-14 \
                         --irods-package-directory /path/to/irods/package/directory
```
This will run the entire python test suite on a single zone, serially. `--irods-package-directory` takes a path to a directory on the local host which contains packages for the target platform. This can be a full or relative path.

In order to speed this up, `--concurrent-test-executor-count` can be used to run the tests in parallel:
```bash
python run_core_tests.py --project-directory ./projects/ubuntu-22.04/ubuntu-22.04-postgres-14 \
                         --irods-package-directory /path/to/irods/package/directory \
                         --concurrent-test-executor-count 4
```
The above line will stand up 4 identical zones and divide up the full list of tests in the iRODS python test suite as evenly as possible to run amongst the executors in parallel.

To run specific tests, use the `--tests` option. If no tests are provided via the `--tests` option (as shown above), the full iRODS python test suite will be run. Note: The python test suite can take 8-10 hours to run.
```bash
python run_core_tests.py --project-directory projects/ubuntu-22.04/ubuntu-22.04-postgres-14 \
                         --irods-package-directory /path/to/irods/package/directory \
                         --tests test_resource_types.Test_Resource_Compound test_rulebase test_iadmin
```
The `--tests` option is compatible with `--concurrent-test-executor-count` as well. This will distribute the provided list of tests as evenly as possible amongst the concurrent executors to be run in parallel.

For topology tests:
```bash
python run_topology_tests.py provider \
                         --project-directory ./projects/ubuntu-22.04/ubuntu-22.04-postgres-14 \
                         --irods-package-directory /path/to/irods/package/directory
```
The `provider` positional argument means that the test script will be running on the Catalog Service Provider. To run tests from the Catalog Service Consumer, use `consumer` instead.

Running the federation test suite is very similar. Note: The federation test suite is a separate python `unittest` file, so any `--tests` option used should be a subset of `test_federation`, although any tests can still run in this environment.
```bash
python run_federation_tests.py --project-directory ./projects/ubuntu-22.04/ubuntu-22.04-postgres-14 \
                               --irods-package-directory /path/to/irods/package/directory \
                               --tests test_federation.Test_ICommands.test_iquest__3466
```

There is also a script to run the iRODS unit test suite. As with the others, the usual options apply. In order to run the full unit test suite as defined in [unit_tests_list.json](https://github.com/irods/irods/blob/2e82164055d1e6c2a3c64eedc534b45c9449df07/unit_tests/unit_tests_list.json) against locally built iRODS packages, run this:
```bash
python run_unit_tests.py --project-directory ./projects/ubuntu-22.04/ubuntu-22.04-postgres-14 \
                         --irods-package-directory /path/to/irods/package/directory
```
If using the `--tests` option, please note that the unit tests use the Catch2 framework and the tests should match the names of the compiled executables.

If all else fails, each of these scripts includes a `--help` option which explains what each of the options do and how they are supposed to be used.

## Run iRODS Plugin Tests

For purposes of CI, official iRODS Plugins have followed a convention of providing a "test hook" which will install the appropriate packages and run the appropriate test suite. If a test hook is provided in the prescribed way, any iRODS plugin test suite can be run in the testing environment.

The test hooks generally have the following requirements:

 - `irods_python_ci_utilities` is installed as a pip package
 - Path to local directory with built plugin packages (passed by `--built_packages_root_directory`)
   - Inside the root directory, the `os_specific_directory` must exist and contain the appropriate packages
     - The `os_specific_directory` must be named like this (image tag -> directory name):
       - ubuntu:20.04  ->  `Ubuntu_20`
       - ubuntu:22.04  ->  `Ubuntu_22`
       - rockylinux/rockylinux:9  ->  `Rocky linux_9`
       - debian:11     ->  `Debian gnu_linux_11`
 - iRODS server is already installed and setup

Your provided built packages should be in an identical directory or symlink following the naming convention above. The directory for your plugin packages might look something like this, where each platform has a directory which contains built packages for the target plugin:
```bash
$ ls -l /path/to/plugin/packages
total 8
drwxr-xr-x 2 user user 4096 Apr 11 17:17 rocky-9
drwxr-xr-x 3 user user 4096 Apr 11 17:15 ubuntu-22.04
```

The path for plugin packages used should be `/path/to/plugin/packages`. The test hook will be looking for a directory called by one of the names referenced above. You can create symlinks to the existing directories to satisfy the test hook, like this:
```bash
$ ls -l /path/to/plugin/packages
total 8
drwxr-xr-x 2 user user 4096 Apr 11 17:17  rocky-9
lrwxrwxrwx 1 user user    8 May 27 14:54 'Rocky linux_9' -> rocky-9
lrwxrwxrwx 1 user user   12 May 27 14:54  Ubuntu_22 -> ubuntu-22.04
drwxr-xr-x 3 user user 4096 Apr 11 17:15  ubuntu-22.04
```

In the future, these requirements will be relaxed so that creating a build-and-test workflow will not be as difficult.

### How to run a test hook

We will use the curl microservice plugin as an example. The curl microservice plugin package is assumed to have been built for the target platform. The last argument provided to the script is the name of the git repository from which the test hook will be fetched.

```bash
python run_plugin_tests.py irods_microservice_plugins_curl \
                           --project-directory ./projects/ubuntu-22.04/ubuntu-22.04-postgres-14 \
                           --irods-package-directory /path/to/irods/packages/directory \
                           --plugin-package-directory /path/to/plugin/package/directories
```
Again, `/path/to/plugin/package/directories` should be the path to the directory on the local host which contains directories for the target platform(s) following the naming convention outlined above. *Do not directly target the directory with the packages because the test hook is looking for the platform-specific directory itself.* This is not like `--irods-package-directory`, which is meant to point to a directory with the built packages directly inside.

If all else fails, this script includes a `--help` option which explains what each of the options do and how they are supposed to be used.

## Stand up a Single Zone

To stand up the latest released version of iRODS in a Zone running on ubuntu:22.04 using a postgres:14 database to host the catalog, run the following:

```bash
python stand_it_up.py --project-directory ./projects/ubuntu-22.04/ubuntu-22.04-postgres-14
```
`--project-directory` can be a full or relative path to a directory in this repository with a `docker-compose.yml` file.

Try this to make sure iRODS is running:
```bash
# expected output: "/tempZone/home/rods:"
docker exec -u irods ubuntu-2204-postgres-14_irods-catalog-provider_1 ils
```
To stop and remove the containers:
```bash
docker-compose --project-directory ./projects/ubuntu-22.04/ubuntu-22.04-postgres-14 down
```
Note: Compose project names default to the name of the directory which contains the `docker-compose.yml` project file. You may wish to specify a project name using `--project-name` in order to give your images and running containers a more recognizable name.

If all else fails, this script includes a `--help` option which explains what each of the options do and how they are supposed to be used.

## Using static images with released iRODS versions

`--use-static-images` enables building and running a Docker image with iRODS packages installed rather than downloading and installing the packages at runtime. This is useful for testing plugins against released versions of iRODS or for quickly reproducing issues on past versions.

This operates by using a couple of environment variables:

 - `dockerfile` - Selects the Dockerfile to build. Valid values are "release.Dockerfile", the default Dockerfile ("Dockerfile"), or an empty string (uses the default).
 - `irods_package_version` - Build argument used by the `release.Dockerfile` specifying the package version string for the iRODS package to download and install when building the image. Defaults to the latest released iRODS version on the target platform OS.

The reader is encouraged to use the provided scripts for standing up iRODS in containers when using this option because they will take care of these environment variables for you when used with the appropriate CLI options. Caution: If `dockerfile` and `irods_package_version` are defined in your environment, unexpected results could occur. Please unset these before running anything.

## Using an ODBC driver

To use the MySQL database plugin, a MySQL ODBC driver file must be provided for use in the server. The scripts have the `--odbc-driver-path` option to specify an existing ODBC driver on the host machine.

If no `--odbc-driver-path` is provided, the appropriate ODBC driver for the given database version and OS will be downloaded to a temporary location on the host machine's local filesystem.

## Execute Remotely

Any of the above-mentioned scripts can be run on a remote Docker daemon using the ssh client. There are a few prerequisites:

 1. The remote host must be running a Docker service which accepts remote requests
 2. The remote host must use private key authentication
 3. The local client must have `ssh-agent` running with the required keys added (see below for instructions)

To run the scripts above on a remote host, the `DOCKER_HOST` environment variable must be set to the remote IP address or hostname. The simplest way to do this is to set it before running the script like this:
```bash
DOCKER_HOST="remote-host-1.example.org" python stand_it_up.py --project-directory ./projects/ubuntu-22.04/ubuntu-22.04-postgres-14
```

### Setting up the ssh client

In order to use the remote execution features of Docker, we need to set up an `ssh-agent` and add our authentication keys to the session.

To start an `ssh-agent` session, run the following (note: only tested with bash):
```bash
eval $(ssh-agent -s)
```

To add our private keys to the session, run `ssh-add` like this:
```bash
ssh-add -k <path to private keys>
```

See `ssh-agent` and `ssh-add` man pages for more details.

For more information about remote execution on Docker, read this: [https://www.docker.com/blog/how-to-deploy-on-remote-docker-hosts-with-docker-compose/](https://www.docker.com/blog/how-to-deploy-on-remote-docker-hosts-with-docker-compose/)

## Specify an alternative Compose project name

By default, Docker Compose uses the directory housing the target Compose file as the "project name". The project name appears at the beginning of the container and network names created by Compose when a project is brought up. The Docker Compose CLI includes an option to specify an alternative project name: `--project-name`. The scripts used for running tests and standing up iRODS zones all include a `--project-name` option as well. This functions identically to the `--project-name` option used with the Docker Compose CLI.

For more information about Compose project names, read this: [https://docs.docker.com/compose/how-tos/project-name](https://docs.docker.com/compose/how-tos/project-name/).

## View results with `xunit-viewer`

An `xunit-viewer` (https://github.com/lukejpreston/xunit-viewer) Dockerfile was added so that the JUnit XML reports can be viewed a little more easily.

To view test results, build the Docker image and run the container. Build the image like this:
```bash
docker build -t xunit-viewer -f xunit_viewer.Dockerfile .
```

Run the viewer like this:
```bash
docker run --rm -d \
    -v /path/to/test-results/logs:/results:ro \
    -p 3000:3000 \
    xunit-viewer -r /results -s
```

This does the following:
 1. Runs the `xunit-viewer1` container with the specified test results as a server on the default port.
 2. Provides `/results` as a volume mount in the container. `/path/to/test-results` is the location of the test results as specified by the `--output-directory`/`-o` option for the test-running scripts.
 3. Exposes port 3000 in the container as 3000 on the host. This is the default port for the `xunit-viewer` server.

