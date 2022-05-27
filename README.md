# iRODS Testing Environment

This repository provides a series of [Docker Compose](https://docs.docker.com/compose/) files which are intended for use in a test framework - which may or may not exist at the time of writing - for [iRODS](https://irods.org). 

For each combination of supported OS platform/version and database type/version, there is a Compose project on which to run an iRODS deployment (*for testing*). The following OS platform Docker image tags are currently supported:
 - almalinux:8
 - centos:7
 - debian:11
 - ubuntu:16.04
 - ubuntu:18.04
 - ubuntu:20.04

The following database Docker image tags are currently supported:
 - postgres:10.12
 - mysql:5.7

## Requirements

A recent-ish version of docker, python, and git are required to run this project.

It is *highly recommended* to use a `virtualenv` python virtual environment. You can set one up which installs the Minimum Requirements (see above) like this:
```bash
virtualenv -p python3 ~/irods_testing_environment
source ~/irods_testing_environment/bin/activate
pip install docker-compose GitPython
pip freeze
```
Compare the output to `requirements.txt`.

## Run iRODS Tests

There are 3 main ways to run the iRODS test suite:
 - Core tests: assumes catalog service provider is the only server
 - Topology tests: assumes 1 catalog service provider and 3 catalog service consumers
 - Federation tests: assumes 2 federated catalog service providers

For the following examples, we will use ubuntu:18.04 for the platform and postgres:10.12 for the database.

To run the full iRODS python test suite as defined in [core_tests_list.json](https://github.com/irods/irods/blob/2e82164055d1e6c2a3c64eedc534b45c9449df07/scripts/core_tests_list.json) against locally built iRODS packages, run this:
```bash
python run_core_tests.py --project-directory ./projects/ubuntu-18.04/ubuntu-18.04-postgres-10.12 \
                         --irods-package-directory /path/to/irods/package/directory
```
This will run the entire python test suite on a single zone, serially. `--irods-package-directory` takes a path to a directory on the local host which contains packages for the target platform. This can be a full or relative path.

In order to speed this up, `--concurrent-test-executor-count` can be used to run the tests in parallel:
```bash
python run_core_tests.py --project-directory ./projects/ubuntu-18.04/ubuntu-18.04-postgres-10.12 \
                         --irods-package-directory /path/to/irods/package/directory \
                         --concurrent-test-executor-count 4
```
The above line will stand up 4 identical zones and divide up the full list of tests in the iRODS python test suite as evenly as possible to run amongst the executors in parallel.

To run specific tests, use the `--tests` option. If no tests are provided via the `--tests` option (as shown above), the full iRODS python test suite will be run. Note: The python test suite can take 8-10 hours to run.
```bash
python run_core_tests.py --project-directory projects/ubuntu-18.04/ubuntu-18.04-postgres-10.12 \
                         --irods-package-directory /path/to/irods/package/directory \
                         --tests test_resource_types.Test_Resource_Compound test_rulebase test_iadmin
```
The `--tests` option is compatible with `--concurrent-test-executor-count` as well. This will distribute the provided list of tests as evenly as possible amongst the concurrent executors to be run in parallel.

For topology tests:
```bash
python run_topology_tests.py provider \
                         --project-directory ./projects/ubuntu-18.04/ubuntu-18.04-postgres-10.12 \
                         --irods-package-directory /path/to/irods/package/directory
```
The `provider` positional argument means that the test script will be running on the Catalog Service Provider. To run tests from the Catalog Service Consumer, use `consumer` instead.

Running the federation test suite is very similar. Note: The federation test suite is a separate python `unittest` file, so any `--tests` option used should be a subset of `test_federation`, although any tests can still run in this environment.
```bash
python run_federation_tests.py --project-directory ./projects/ubuntu-18.04/ubuntu-18.04-postgres-10.12 \
                               --irods-package-directory /path/to/irods/package/directory \
                               --tests test_federation.Test_ICommands.test_iquest__3466
```

There is also a script to run the iRODS unit test suite. As with the others, the usual options apply. In order to run the full unit test suite as defined in [unit_tests_list.json](https://github.com/irods/irods/blob/2e82164055d1e6c2a3c64eedc534b45c9449df07/unit_tests/unit_tests_list.json) against locally built iRODS packages, run this:
```bash
python run_unit_tests.py --project-directory ./projects/ubuntu-18.04/ubuntu-18.04-postgres-10.12 \
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
       - ubuntu:16.04  ->  `Ubuntu_16`
       - ubuntu:18.04  ->  `Ubuntu_18`
       - centos:7      ->  `Centos linux_7`
 - iRODS server is already installed and setup

Your provided built packages should be in an identical directory or symlink following the naming convention above. The directory for your plugin packages might look something like this, where each platform has a directory which contains built packages for the target plugin:
```bash
$ ls -l /path/to/plugin/packages
total 8
drwxr-xr-x 2 user user 4096 Apr 11 17:17 centos-7
drwxr-xr-x 3 user user 4096 Apr 11 17:15 ubuntu-18.04
```

The path for plugin packages used should be `/path/to/plugin/packages`. The test hook will be looking for a directory called by one of the names referenced above. You can create symlinks to the existing directories to satisfy the test hook, like this:
```bash
$ ls -l /path/to/plugin/packages
total 8
drwxr-xr-x 2 user user 4096 Apr 11 17:17  centos-7
lrwxrwxrwx 1 user user    8 May 27 14:54 'Centos linux_7' -> centos-7
lrwxrwxrwx 1 user user   12 May 27 14:54  Ubuntu_18 -> ubuntu-18.04
drwxr-xr-x 3 user user 4096 Apr 11 17:15  ubuntu-18.04
```

In the future, these requirements will be relaxed so that creating a build-and-test workflow will not be as difficult.

### How to run a test hook

We will use the curl microservice plugin as an example. The curl microservice plugin package is assumed to have been built for the target platform. The last argument provided to the script is the name of the git repository from which the test hook will be fetched.

```bash
python run_plugin_tests.py irods_microservice_plugins_curl \
                           --project-directory ./projects/ubuntu-18.04/ubuntu-18.04-postgres-10.12 \
                           --irods-package-directory /path/to/irods/packages/directory \
                           --plugin-package-directory /path/to/plugin/package/directories
```
Again, `/path/to/plugin/package/directories` should be the path to the directory on the local host which contains directories for the target platform(s) following the naming convention outlined above. *Do not directly target the directory with the packages because the test hook is looking for the platform-specific directory itself.* This is not like `--irods-package-directory`, which is meant to point to a directory with the built packages directly inside.

If all else fails, this script includes a `--help` option which explains what each of the options do and how they are supposed to be used.

## Stand up a Single Zone

To stand up the latest released version of iRODS in a Zone running on ubuntu:18.04 using a postgres:10.12 database to host the catalog, run the following:

```bash
python stand_it_up.py --project-directory ./projects/ubuntu-18.04/ubuntu-18.04-postgres-10.12
```
`--project-directory` can be a full or relative path to a directory in this repository with a `docker-compose.yml` file.

Try this to make sure iRODS is running:
```bash
# expected output: "/tempZone/home/rods:"
docker exec -u irods ubuntu-1804-postgres-1012_irods-catalog-provider_1 ils
```
To stop and remove the containers:
```bash
docker-compose --project-directory ./projects/ubuntu-18.04/ubuntu-18.04-postgres-10.12 down
```
Note: Compose project names default to the name of the directory which contains the `docker-compose.yml` project file. You may wish to specify a project name using `--project-name` in order to give your images and running containers a more recognizable name.

If all else fails, this script includes a `--help` option which explains what each of the options do and how they are supposed to be used.

## Using an ODBC driver

To use the MySQL database plugin, a MySQL ODBC driver file must be provided for use in the server. The scripts have the `--odbc-driver-path` option to specify an existing ODBC driver on the host machine.

If no `--odbc-driver-path` is provided, the appropriate ODBC driver for the given database version and OS will be downloaded to a temporary location on the host machine's local filesystem.
