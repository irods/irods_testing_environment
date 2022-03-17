# iRODS Testing Environment

This repository provides a series of [Docker Compose](https://docs.docker.com/compose/) files which are intended for use in a test framework - which may or may not exist at the time of writing - for [iRODS](https://irods.org). 

For each combination of supported OS platform/version and database type/version, there is a Compose project on which to run an iRODS deployment (*for testing*). The following OS platform Docker image tags are currently supported:
 - ubuntu:16.04
 - ubuntu:18.04
 - centos:7

The following database Docker image tags are currently supported:
 - postgres:10.12
 - mysql:5.7

To add support for a new OS platform/version or database type/version, simply add a new Compose project like those under `projects` and point the scripts at it.

## Quick Start

A recent-ish version of docker, python, and git are required to run this project.

It is *highly recommended* to use a `virtualenv` python virtual environment. You can set one up which installs the Minimum Requirements (see above) like this:
```bash
virtualenv -p python3 ~/irods_testing_environment
source ~/irods_testing_environment/bin/activate
pip install docker-compose GitPython
pip freeze
```
Compare the output to `requirements.txt`.

To stand up the latest released version of iRODS in a Zone running on Ubuntu 18.04 using a Postgres 10.12 database to host the catalog, run the following:

```bash
# --project-directory defaults to `pwd`
cd projects/ubuntu-18.04/ubuntu-18.04-postgres-10.12
# build images and create and run the docker-compose project
docker-compose up -d
# install iRODS packages on the appropriate containers
python ../../../install.py
# setup iRODS zone with default settings (tempZone)
python ../../../setup.py
```
Try this to make sure iRODS is running:
```bash
# expected output: "/tempZone/home/rods:"
docker exec -u irods ubuntu-1804-postgres-1012_irods-catalog-consumer_1 ils
```
To stop and remove the containers:
```bash
# remember to cd to the correct project directory or use --project-directory
docker-compose down
```
Note: Compose project names default to the name of the directory which contains the `docker-compose.yml` project file. You may wish to specify a project name using `--project-name` in order to give your images and running containers a more recognizable name.

## Run iRODS Tests

There are 3 main ways to run the iRODS test suite:
 - Core tests: assumes CSP is the only server
 - Topology tests: assumes 1 CSP and 3 CSCs
 - Federation tests: assumes 2 federated CSPs

In order to run the test suite against, for instance, Ubuntu 18.04 using a Postgres 10.12 database to host the catalog, run the following:
```bash
# --project-directory defaults to `pwd`
cd projects/ubuntu-18.04/ubuntu-18.04-postgres-10.12
# run tests using latest officially released packages
python run_core_tests.py
```

To run a specific test, use the `--tests` option. If none is provided (as shown above), the entire python test suite will be run. Note: The python test suite can take 8-10 hours to run.
```bash
python run_core_tests.py --tests test_resource_types.Test_Resource_Compound
```

For topology tests:
```bash
python run_topology_tests.py provider
```
The `provider` option means that the test script will be running on the CSP. To run tests from the CSC, use `consumer` instead. The same options available to `run_core_tests.py` apply here as well.

Running the federation test suite is very similar. Note: The federation test suite is a separate python `unittest` file, so any `--tests` option used should be a subset of `test_federation`.
```bash
# With no `--tests` option provided, it is equivalent to just running test_federation
python run_federation_tests.py --tests test_federation.Test_ICommands.test_iquest__3466
```

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

Your provided built packages should be in an identical directory or symlink following the naming convention above.

In the future, these requirements will be relaxed so that creating a build-and-test workflow will not be as difficult.

### How to run a test hook

We will use the curl microservice plugin as an example. The curl microservice plugin package is assumed to have been built for the target platform. The last argument provided to the script is the name of the git repository from which the test hook will be fetched.

```bash
# --project-directory defaults to `pwd`
cd projects/ubuntu-18.04/ubuntu-18.04-postgres-10.12
# the built packages should be in a directory as described above
python run_plugin_tests.py --plugin-package-directory /path/to/curl-microservice-plugin irods_microservice_plugins_curl
```

## Using an ODBC driver

To use the MySQL database plugin, a MySQL ODBC driver file must be provided for use in the server. The scripts have the `--odbc-driver-path` option to specify an existing ODBC driver on the host machine.

If no `--odbc-driver-path` is provided, the appropriate ODBC driver for the given database version and OS will be downloaded to a temporary location on the host machine's local filesystem.
