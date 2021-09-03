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

It is *highly recommended* to use a `virtualenv` python virtual environment. You can set one up which installs the Minimum Requirements (see above) like this:
```bash
virtualenv -p python3 ~/irods_testing_environment
source ~/irods_testing_environment/bin/activate
pip install docker-compose
pip freeze
```
Compare the output to `requirements.txt`.

To stand up the latest released version of iRODS in a Zone running on Ubuntu 18.04 using a Postgres 10.12 database to host the catalog, run the following:

```bash
# --project-directory defaults to `pwd`
cd projects/ubuntu-18.04/postgres-10.12
# build images and create and run the docker-compose project
docker-compose up -d
# install iRODS packages on the appropriate containers
python ../../../install.py -p ubuntu:18.04 -d postgres:10.12
# setup iRODS zone with default settings (tempZone)
python ../../../setup.py -p ubuntu:18.04 -d postgres:10.12
```
Try this to make sure iRODS is running:
```bash
# expected output: "/tempZone/home/rods:"
docker exec -u irods postgres-1012_irods-catalog-consumer_1 ils
```
To stop and remove the containers:
```bash
# remember to cd to the correct project directory or use --project-directory
docker-compose down
```
Note: Compose project names default to the name of the directory which contains the `docker-compose.yml` project file. You may wish to specify a project name using `--project-name` in order to give your images and running containers a more recognizable name.
