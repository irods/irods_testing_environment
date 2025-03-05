#! /usr/bin/env python3

import logging
from logging.handlers import SysLogHandler
import os
import subprocess
import sys
import shutil
from pathlib import PurePath, Path
import docker
from docker.types import Mount
import re
import jsonschema
import argparse
import json


# ------------
# LOGGER STUFF
# ------------
logger = logging.getLogger('irods-test-runner')
logger.setLevel(logging.DEBUG)

# Console logging
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter('[%(asctime)s %(name)s %(levelname)s] %(message)s')
ch.setFormatter(formatter)

logger.addHandler(ch)

# -------------
# NICE GLOBALS
# -------------

IRODS_BASE_DIR = Path.home() / 'Documents' / 'iRODS'

IRODS_DEV_DIR = IRODS_BASE_DIR / 'irods_development_environment'

# Testing directories
IRODS_TEST_DIR = IRODS_BASE_DIR / 'irods_testing_environment'
IRODS_TEST_PROJECTS_DIR = IRODS_TEST_DIR / 'projects'

# Build directories
IRODS_BUILD_ARTIFACTS_DIR = IRODS_BASE_DIR / 'build-artifacts'
IRODS_BUILD_BASE = PurePath(IRODS_BUILD_ARTIFACTS_DIR) / '{os_name}' # os_name MUST be same as test names
IRODS_SERV_BUILD_DIR = IRODS_BUILD_BASE / 'irods_build'
IRODS_ICOMMANDS_BUILD_DIR = IRODS_BUILD_BASE / 'irods_icommands_build'

IRODS_LOGS_DIR = IRODS_BUILD_BASE / 'logs'

IRODS_CCACHE_DIR = IRODS_BUILD_BASE / 'ccache'

IRODS_PACKAGES_DIR = IRODS_BUILD_BASE / 'packages'

IRODS_EXTERNALS_DIR = IRODS_BUILD_BASE / 'externals'

# Plugins & plugin build dirs
IRODS_PLUGINS_DIR = IRODS_BUILD_BASE / 'plugins'
IRODS_PLUGIN_BUILD_DIR = IRODS_PLUGINS_DIR / '{short_plugin_name}_build'
IRODS_PLUGIN_PACKAGE_DIR = IRODS_PLUGINS_DIR / '{short_plugin_name}'

# Source directories
IRODS_SERV_DIR = IRODS_BASE_DIR / 'irods'
IRODS_ICOMMANDS_DIR = IRODS_BASE_DIR / 'irods_client_icommands'
IRODS_PLUGINS_SRC_DIR = IRODS_BASE_DIR # / 'plugins'
IRODS_PLUGIN_SRC_DIR = IRODS_PLUGINS_SRC_DIR / '{full_plugin_name}'

# Image names
IRODS_BUILD_IMAGE_NAME = 'irods-core-builder'
IRODS_PLUGIN_BUILDER_NAME = 'irods-plugin-builder'
IRODS_EXTERNALS_BUILDER_NAME = 'irods-externals-builder'

# RE
SHA_RE = re.compile('sha:\[(?P<sha>[a-z0-9]+)\]')

PLUGIN_PREFIXES = ('irods_capability', 'irods_microservice_plugins', 'irods_resource_plugin', 'irods_rule_engine_plugin', 'irods_http_api_user_mapper_plugin', 'irods_auth_plugin')

# ----------------
# Common Functions
# ----------------
def get_supported_oses():
    return (d.name for d in IRODS_TEST_PROJECTS_DIR.iterdir() if d.is_dir())

def get_supported_plugins():
    return (d.name for d in IRODS_PLUGINS_SRC_DIR.iterdir() if d.is_dir() for prefix in PLUGIN_PREFIXES if d.name.startswith(prefix))

def validate_choice(choice, choices: list):
    if choice not in choices:
        logger.warning(f"User choice=[{choice!r}] not in valid choices=[{choices!r}]")
        sys.exit(1)

def format_pure_path(paths: list[PurePath], **kwargs):
    return (Path(str(d).format(**kwargs)) for d in paths)

def get_valid_tags(client, img_name):
    supported_oses = tuple(get_supported_oses())
    return (tag.split(':')[1] for imgs in client.images.list(name=img_name) for tag in imgs.tags if tag.split(':')[1] in supported_oses)

# ---------------------
# Functions for Testing
# ---------------------
def query_desired_test_project(os_choice, db_choice):
    path_stems = list(get_supported_oses())

    if os_choice is None:
        for path in path_stems:
            print(path)

        os_choice = input("What ya wanna run? ")

    validate_choice(os_choice, path_stems)

    os_of_choice = IRODS_TEST_PROJECTS_DIR / os_choice
    mid = map(lambda d: d.name, filter(lambda d: d.is_dir(), os_of_choice.iterdir()))
    db_choices = list(map(lambda d: d[len(os_choice)+1:], mid))

    if db_choice is None:
        for db in db_choices:
            print(db)

        db_choice = input("What db ya want? ")

    validate_choice(db_choice, db_choices)

    return ((os_of_choice / f'{os_choice}-{db_choice}'), os_choice, db_choice)

def query_desired_test(test_choice):
    test_files = list(map(lambda f: f.stem, IRODS_TEST_DIR.glob('run_*_tests.py')))

    if test_choice is None:
        for f in test_files:
            print(f)

        test_choice = input("What test ya want? ")

    validate_choice(test_choice, test_files)
    return IRODS_TEST_DIR / f'{test_choice}.py'

# -------
# Runners
# -------
def ask_run_test(os=None, db=None, test_type=None, test_args=None):
    desired_test = query_desired_test(test_type)
    project_directory, os_choice, _ = query_desired_test_project(os, db)

    # Build up named args
    named_args = [('--project-directory', project_directory),
                  ('--irods-package-directory', IRODS_PACKAGES_DIR),
                  ('--output-directory', IRODS_LOGS_DIR),]
    bonus_args = []

    # python run_plugin_tests.py --project-directory projects/ubuntu-22.04/ubuntu-22.04-postgres-14.8/ --irods-package-directory ../build-artifacts/ubuntu-22/packages/ --plugin-package-directory ../build-artifacts/ubuntu-22/plugins --discard-logs irods_microservice_plugins_curl
    # match/case candidate?
    if test_args is None:
        if desired_test.stem == 'run_plugin_tests':
            # Gather valid plugins
            yes_plugins = tuple(get_supported_plugins())
            assert(len(yes_plugins) > 0)

            for plugin in yes_plugins:
                print(plugin)
    
            # Prompt user for desired plugin
            plugin_choice = input("What plugin ya wanna build? ")
            validate_choice(plugin_choice, yes_plugins)

            # Add plugin git name
            bonus_args.append(plugin_choice)

            # Dumb trim of plugin
            for prefix in PLUGIN_PREFIXES:
                if plugin_choice.startswith(prefix):
                    plugin_name = plugin_choice[len(prefix)+1:]

            # Append plugin dir
            named_args.append(('--plugin-package-directory', str(IRODS_PLUGIN_PACKAGE_DIR).format(os_name=os_choice, short_plugin_name=plugin_name)))
        elif desired_test.stem == 'run_core_tests':
            num_executors = int(input('How many test executors do you want? '))
            named_args.append(('--concurrent-test-executor-count', str(num_executors)))
        elif desired_test.stem == 'run_topology_tests':
            num_executors = int(input('How many test executors do you want? '))
            named_args.append(('--concurrent-test-executor-count', str(num_executors)))

            topo_options = ['provider', 'consumer']
            for option in topo_options:
                print(option)

            choice = input('Where ya wanna run the tests? ')
            validate_choice(choice, topo_options)

            bonus_args.append(choice)

    else:
        test_idx = len(test_args) 
        try:
            test_idx = test_args.index('--tests')
        except ValueError:
            ...
        bonus_args = test_args[:test_idx]

    arg_list = [sys.executable, str(desired_test),]
    for arg, param in named_args:
        arg_list.append(arg)

        if isinstance(param, PurePath):
            param = str(param).format(os_name=os_choice)

        arg_list.append(param)

    arg_list.extend(bonus_args)

    failed_tests_list = None
    if test_args is None:
        tests_to_run = input('Please input test you wish to run (default: all): ').split()

        if len(tests_to_run) != 0:
            failed_tests_list = tests_to_run
            failed_tests_list.insert(0, '--tests')
    else:
        failed_tests_list = test_args[test_idx:]

    res = None
    failed_tests_pattern = re.compile('(?<=List of failed tests:\n\t).*')

    max_duplicate_attempts = 3
    current_duplicate_attempt = 1
    attempt = 0

    while current_duplicate_attempt <= max_duplicate_attempts:
        attempt += 1

        logger.info(f'Running attempt=[{attempt!r}] with current_duplicate_attempt=[{current_duplicate_attempt!r} of max_duplicate_attempts=[{max_duplicate_attempts!r}]]')

        if failed_tests_list:
            running_arg_list = arg_list + failed_tests_list
        else:
            running_arg_list = arg_list

        logger.debug(f"Executing running_arg_list=[{running_arg_list!r}]")

        try:
            res = subprocess.run(running_arg_list, capture_output=True, text=True)
        except KeyboardInterrupt:
            logger.warning('Interrupt received. Kill test...')
            arg_list = []
            d_c = shutil.which('docker')
            arg_list.append(d_c)
            arg_list.append('compose')
            arg_list.append('down')
            subprocess.run(arg_list, cwd=str(project_directory))
            c = input('Continue current test? (y/N)')
            if c.lower() == 'n' or len(c) == 0:
                break
            else:
                continue

        logger.debug(f'res=[{res!r}] of attempt=[{attempt!r}]')

        if res.returncode == 0:
            sha = SHA_RE.search(res.stdout).group('sha')
            logger.info(f'Test passed on attempt=[{attempt!r}], sha=[{sha!r}]')
            break

        failed_tests = failed_tests_pattern.search(res.stdout)

        if failed_tests:
            new_failed_tests_list = failed_tests.group().strip().split()
            new_failed_tests_list.insert(0, '--tests')
            if new_failed_tests_list == failed_tests_list:
                current_duplicate_attempt += 1
            else:
                current_duplicate_attempt = 1
            failed_tests_list = new_failed_tests_list
        else:
            logger.error(f'Failed to parse failed_tests with failed_tests_pattern=[{failed_tests_pattern!r}]')
            current_duplicate_attempt += 1

        logger.info(f'attempt=[{attempt!r}] failed')

    return res

def ask_run_compile(os=None, build_args=None):
    logger.debug(f'ask_run_compile(os=[{os!r}], build_args=[{build_args!r}])')
    client = docker.from_env()

    yes_images = tuple(get_valid_tags(client, IRODS_BUILD_IMAGE_NAME))
    assert(len(yes_images) > 0)

    if os is None:
        for image in yes_images:
            print(image)

        os_choice = input("What image ya wanna run? ")
    else:
        os_choice = os

    validate_choice(os_choice, yes_images)

    build_image = client.images.get(f'{IRODS_BUILD_IMAGE_NAME}:{os_choice}')
    
    dirs_to_format = [IRODS_SERV_BUILD_DIR, IRODS_ICOMMANDS_BUILD_DIR, IRODS_PACKAGES_DIR, IRODS_CCACHE_DIR]
    dirs_to_mount = [d for d in format_pure_path(dirs_to_format, os_name=os_choice)]

    for d in (d for d in dirs_to_mount if not d.exists()):
        logger.info(f'The path=[{d!r}] does not exist, creating.')
        d.mkdir(parents=True)

    dirs_to_mount = [str(d) for d in dirs_to_mount]

    # Build up docker mounts
    mounts = [Mount('/irods_source', str(IRODS_SERV_DIR), read_only=True, type='bind'),
              Mount('/icommands_source', str(IRODS_ICOMMANDS_DIR), read_only=True, type='bind'),
              Mount('/irods_build', str(dirs_to_mount[0]), type='bind'),
              Mount('/icommands_build', str(dirs_to_mount[1]), type='bind'),
              Mount('/irods_packages', str(dirs_to_mount[2]), type='bind'),
              Mount('/irods_build_cache', str(dirs_to_mount[3]), type='bind')]

    if build_args is None:
        args = ['--ccache',]
        build_debug = input('Build Debug? (Y/n) ')
        if build_debug.lower() == 'y' or len(build_debug) == 0:
            args.append('--debug')

        enable_asan = input('Enable ASAN? (Y/n) ')
        if enable_asan.lower() == 'y' or len(enable_asan) == 0:
            args.append('--enable-address-sanitizer')

        enable_ubsan = input('Enable UBSAN? (Y/n) ')
        if enable_ubsan.lower() == 'y' or len(enable_ubsan) == 0:
            args.append('--enable-undefined-behavior-sanitizer')
    else:
        args = build_args

    logger.debug(f'Executing build_image={build_image!r} with mounts={mounts!r} and args={args!r}')
    build_container = client.containers.run(build_image, command=args, detach=True, mounts=mounts, remove=True)
    logs = build_container.logs(stream=True)
    for line in logs:
        print(line.decode(), end='')
    res = build_container.wait()
    logger.debug(f'Container result of build_image={build_image!r}, build_container={res!r}')

    return res['StatusCode']

def ask_build_plugin():
    # docker run --rm -v /home/marflo/Documents/iRODS/irods_microservice_plugins_curl:/irods_plugin_source:ro -v /home/marflo/Documents/iRODS/build-artifacts/ubuntu-22:/irods_packages:ro -v /home/marflo/Documents/iRODS/build-artifacts/ubuntu-22/curl_build:/irods_plugin_build -v /home/marflo/Documents/iRODS/build-artifacts/ubuntu-22/curl:/irods_plugin_packages plugin-builder:ubuntu-22 --build_directory /irods_plugin_build
    client = docker.from_env()

    # Get valid images
    yes_images = tuple(get_valid_tags(client, IRODS_PLUGIN_BUILDER_NAME))
    assert(len(yes_images) > 0)

    for image in yes_images:
        print(image)

    # Prompt user for image choice
    os_choice = input("What image ya wanna run? ")
    validate_choice(os_choice, yes_images)

    # Get the selected image
    build_image = client.images.get(f'{IRODS_PLUGIN_BUILDER_NAME}:{os_choice}')

    # Gather valid plugins
    yes_plugins = tuple(get_supported_plugins())
    assert(len(yes_plugins) > 0)

    for plugin in yes_plugins:
        print(plugin)
    
    # Prompt user for desired plugin
    plugin_choice = input("What plugin ya wanna build? ")
    validate_choice(plugin_choice, yes_plugins)

    # Dumb trim of plugin
    for prefix in PLUGIN_PREFIXES:
        if plugin_choice.startswith(prefix):
            plugin_name = plugin_choice[len(prefix)+1:]

    # Gather args, convert PurePaths to Paths
    dirs_to_format = [IRODS_PLUGIN_SRC_DIR, IRODS_PACKAGES_DIR, IRODS_PLUGIN_BUILD_DIR, IRODS_PLUGIN_PACKAGE_DIR]
    dirs_to_mount = [d for d in format_pure_path(dirs_to_format, os_name=os_choice, full_plugin_name=plugin_choice, short_plugin_name=plugin_name)]

    # Create directories if needed
    for d in (d for d in dirs_to_mount if not d.exists()):
        logger.info(f'The path=[{d!r}] does not exist, creating.')
        d.mkdir(parents=True)

    # Create symlinks for build & testing
    sym_link_needed = [dirs_to_mount[1], dirs_to_mount[3]]
    for d in sym_link_needed:
        supported_oses = {'ubuntu-22.04': 'Ubuntu_22',
                          'ubuntu-24.04': 'Ubuntu_24',
                          'debian-11': 'Debian gnu_linux_11',}
        if os_choice in supported_oses:
            link_dir = d / supported_oses[os_choice]
            
            # Assume if exists is link
            if not link_dir.exists():
                logger.info(f'The link_dir=[{link_dir!r}] does not exist, creating.')
                link_dir.symlink_to('.', target_is_directory=True)
        else:
            logger.warning(f'The os_choice=[{os_choice!r}] is not supported!')

    mounts = [Mount('/irods_plugin_source', str(dirs_to_mount[0]), read_only=True, type='bind'),
              Mount('/irods_packages', str(dirs_to_mount[1]), read_only=True, type='bind'),
              Mount('/irods_plugin_build', str(dirs_to_mount[2]), type='bind'),
              Mount('/irods_plugin_packages', str(dirs_to_mount[3]), type='bind'),]

    args = ['--build_directory', '/irods_plugin_build',]

    build_container = client.containers.run(build_image, command=args, detach=True, mounts=mounts, remove=True)
    logs = build_container.logs(stream=True)
    for line in logs:
        print(line.decode(), end='')

    res = build_container.wait()
    logger.debug(f'Container result of build_image={build_image!r}, build_container={res!r}')

    return res['StatusCode']

def ask_compile_externals(os=None, repo=None, branch=None, target=None):
    logger.debug(f'ask_compile_externals(os=[{os!r}], repo=[{repo!r}], branch=[{branch!r}], target=[{target!r}])')
    client = docker.from_env()

    yes_images = tuple(get_valid_tags(client, IRODS_EXTERNALS_BUILDER_NAME))
    assert(len(yes_images) > 0)

    if os is None:
        for image in yes_images:
            print(image)

        os_choice = input("What image ya wanna run? ")
    else:
        os_choice = os

    validate_choice(os_choice, yes_images)

    build_image = client.images.get(f'{IRODS_EXTERNALS_BUILDER_NAME}:{os_choice}')

    dirs_to_format = [IRODS_EXTERNALS_DIR]
    dirs_to_mount = [d for d in format_pure_path(dirs_to_format, os_name=os_choice)]

    for d in (d for d in dirs_to_mount if not d.exists()):
        logger.info(f'The path=[{d!r}] does not exist, creating.')
        d.mkdir(parents=True)

    dirs_to_mount = [str(d) for d in dirs_to_mount]

    # Build up docker mounts
    mounts = [Mount('/irods_externals_packages', str(dirs_to_mount[0]), type='bind'),]

    args = []
    if repo:
        args.append('--git-repository')
        args.append(repo)
    if branch:
        args.append('--branch')
        args.append(branch)
    if target:
        args.append('--make-target')
        args.append(target)

    logger.debug(f'Executing build_image={build_image!r} with mounts={mounts!r} and args={args!r}')
    build_container = client.containers.run(build_image, command=args, detach=True, mounts=mounts, remove=True)
    logs = build_container.logs(stream=True)
    for line in logs:
        print(line.decode(), end='')
    res = build_container.wait()
    logger.debug(f'Container result of build_image={build_image!r}, build_container={res!r}')

    return res['StatusCode']

def refresh_core_builders():
    tag_name = {'ubuntu20': 'ubuntu-20.04',
                'ubuntu22': 'ubuntu-22.04',
                'ubuntu24': 'ubuntu-24.04',
                'debian11': 'debian-11',
                'debian12': 'debian-12',}
    tag_name = {'debian11': 'debian-11'}
    # Get current env
    docker_env = os.environ.copy()

    # Add buildkit to env
    docker_env['DOCKER_BUILDKIT'] = '1'

    # Setup environ
    # client = docker.from_env(environment=docker_env)
    
    # For all builders found...
    for builder in IRODS_DEV_DIR.glob('irods_core_builder.*'):
        system = builder.name.split('.')[1]

        # skip if mapping not provided yet...
        if system not in tag_name:
            continue

        # Build up exec args
        args = [shutil.which('docker'),
                'build',
                '--no-cache',
                '--pull',
                '-f',
                str(builder),
                '-t',
                f'{IRODS_BUILD_IMAGE_NAME}:{tag_name[system]}',
                str(IRODS_DEV_DIR),]

        # TODO: Use the following line if buildkit ever gets supported
        # See the following: https://github.com/docker/docker-py/issues/2230
        # img, logs = client.images.build(path=str(IRODS_DEV_DIR), dockerfile=str(builder), nocache=True, rm=True, labels={IRODS_BUILD_IMAGE_NAME: tag_name[system]})

        # logger.debug(f'img=[{img!r}]')
        # logger.debug(f'img=[{logs!r}]')

        # Run docker build
        logger.debug(f"Executing args=[{args!r}]")
        res = subprocess.run(args, env=docker_env)
        logger.debug(f'res=[{res!r}] of updating builder for system=[{system!r}]')

def refresh_plugin_builders():
    tag_name = {'ubuntu20': 'ubuntu-20.04',
                'ubuntu22': 'ubuntu-22.04',
                'ubuntu24': 'ubuntu-24.04',
                'debian11': 'debian-11',
                'debian12': 'debian-12',}
    tag_name = { 'debian11': 'debian-11'}
    # Get current env
    docker_env = os.environ.copy()

    # Add buildkit to env
    docker_env['DOCKER_BUILDKIT'] = '1'

    # Setup environ
    # client = docker.from_env(environment=docker_env)
    
    # For all builders found...
    for builder in IRODS_DEV_DIR.glob('plugin_builder.*'):
        system = builder.name.split('.')[1]

        # skip if mapping not provided yet...
        if system not in tag_name:
            continue

        # Build up exec args
        args = [shutil.which('docker'),
                'build',
                '--no-cache',
                '--pull',
                '-f',
                str(builder),
                '-t',
                f'{IRODS_PLUGIN_BUILDER_NAME}:{tag_name[system]}',
                str(IRODS_DEV_DIR),]

        # TODO: Use the following line if buildkit ever gets supported
        # See the following: https://github.com/docker/docker-py/issues/2230
        # img, logs = client.images.build(path=str(IRODS_DEV_DIR), dockerfile=str(builder), nocache=True, rm=True, labels={IRODS_BUILD_IMAGE_NAME: tag_name[system]})

        # logger.debug(f'img=[{img!r}]')
        # logger.debug(f'img=[{logs!r}]')

        # Run docker build
        logger.debug(f"Executing args=[{args!r}]")
        res = subprocess.run(args, env=docker_env)
        logger.debug(f'res=[{res!r}] of updating builder for system=[{system!r}]')

def refresh_externals_builders():
    tag_name = {'ubuntu20': '  ubuntu-20.04',
                'ubuntu22':   'ubuntu-22.04',
                'ubuntu24':   'ubuntu-24.04',
                'debian11':   'debian-11',
                'debian12':   'debian-12',
                'rocky9':     'rockylinux-9',
                'almalinux8': 'almalinux-8',}

    # Get current env
    docker_env = os.environ.copy()

    # Add buildkit to env
    docker_env['DOCKER_BUILDKIT'] = '1'

    # Setup environ
    # client = docker.from_env(environment=docker_env)
    
    # For all builders found...
    for builder in IRODS_DEV_DIR.glob('externals_builder.*'):
        system = builder.name.split('.')[1]

        # skip if mapping not provided yet...
        if system not in tag_name:
            continue

        # Build up exec args
        args = [shutil.which('docker'),
                'build',
                '--no-cache',
                '--pull',
                '-f',
                str(builder),
                '-t',
                f'{IRODS_EXTERNALS_BUILDER_NAME}:{tag_name[system]}',
                str(IRODS_DEV_DIR),]

        # TODO: Use the following line if buildkit ever gets supported
        # See the following: https://github.com/docker/docker-py/issues/2230
        # img, logs = client.images.build(path=str(IRODS_DEV_DIR), dockerfile=str(builder), nocache=True, rm=True, labels={IRODS_BUILD_IMAGE_NAME: tag_name[system]})

        # logger.debug(f'img=[{img!r}]')
        # logger.debug(f'img=[{logs!r}]')

        # Run docker build
        logger.debug(f"Executing args=[{args!r}]")
        res = subprocess.run(args, env=docker_env)
        logger.debug(f'res=[{res!r}] of updating builder for system=[{system!r}]')

# -------
# SCHEMAS
# -------
TEST_MATRIX_SCHEMA = {
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'type': 'object',
    'properties': {
        'build': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'args': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                        },
                    },
                    'os': {
                        'enum': list(get_supported_oses()),
                    },
                },
                'required': ['args', 'os'],
            },
            'minItems': 1,
            'uniqueItems': True,
        },
        'plugin': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'plugin': {
                        'enum': list(get_supported_plugins())
                    },
                    'os': {
                        'enum': list(get_supported_oses()),
                    },
                },
                'required': ['plugin', 'os'],
            },
            'minItems': 1,
            'uniqueItems': True,
        },
        'test': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properies': {
                    'args': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                        },
                    },
                    'os': {
                        'enum': list(get_supported_oses()),
                    },
                    'db': {
                        'type': 'string',
                    },
                    'type': {
                        'enum': list(map(lambda f: f.stem, IRODS_TEST_DIR.glob('run_*_tests.py')))
                    },
                },
                'required': ['args', 'os', 'db', 'type'],
            },
            'minItems': 1,
            'uniqueItems': True,
        },
        'externals': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'os': {
                        'enum': list(get_supported_oses()),
                    },
                    'repo': {
                        'type': 'string',
                    },
                    'branch': {
                        'type': 'string',
                    },
                    'target': {
                        'type': 'string',
                    },
                },
                'required': ['os'],
            },
            'minItems': 1,
            'uniqueItems': True,
        },
    },
}
    
if __name__ == '__main__':
    # Construct argument parser
    parser = argparse.ArgumentParser(description='Build and Test iRODS using a unified interface')
    parser.add_argument('--test-matrix', help='JSON file containing build and test instructions', type=Path)

    # Parse args, branch based on input or lack of
    args = vars(parser.parse_args())

    # refresh_core_builders()
    # refresh_plugin_builders()
    # refresh_externals_builders()

    # Run 'interactive mode'
    if args['test_matrix'] is None:
        choices = {'build': ask_run_compile, 'test': ask_run_test, 'plugin': ask_build_plugin}
        for choice in choices:
            print(choice)

        choice = input('What you wanna do? ')
        validate_choice(choice, choices.keys())

        # Call function at choice
        choices[choice]()

    # Run 'test matrix' mode (i.e. automated mode)
    else:
        path_to_matrix = args['test_matrix']

        # Error out early
        if not path_to_matrix.is_file():
            logger.error(f'path_to_matrix=[{path_to_matrix!r}] is not a file, or doesn\'t exist.')

        # Load the JSON config
        with open(path_to_matrix) as test_matrix_file:
            test_matrix_config = json.load(test_matrix_file)

        jsonschema.validate(instance=test_matrix_config, schema=TEST_MATRIX_SCHEMA)

        # Run build options, if present
        if 'build' in test_matrix_config:
            build_items = test_matrix_config['build']

            for item in build_items:
                rc = ask_run_compile(os=item["os"], build_args=item["args"])

                if rc != 0:
                    logger.error(f'Failed to build for os=[{item["os"]!r}] with build_args=[{item["args"]!r}].')
                    sys.exit(1)
                logger.info(f'Build for os=[{item["os"]!r}] with build_args=[{item["args"]!r}] succeeded.')


        # TODO: add plugin build options here


        # Run test options, if present
        if 'test' in test_matrix_config:
            test_items = test_matrix_config['test']
            did_pass = {}

            # Run through all tests in matrix
            for item in test_items:
                res = ask_run_test(os=item["os"], db=item["db"], test_type=item["type"], test_args=item["args"])

                # Extract sha from test result if available
                sha_res = SHA_RE.search(res.stdout)
                if sha_res:
                    sha = sha_res.group('sha')
                else:
                    sha = '???'

                # Put together string for log results
                run_string = ':'.join([item["os"], item["db"], item["type"], ' '.join(item["args"])])

                # Store whether or not the tests passed
                if res.returncode == 0:
                    did_pass[run_string] = (True, sha)
                else:
                    did_pass[run_string] = (False, sha)

            # Print out results of tests
            for test in did_pass:
                test_args = test.split(':')
                (is_pass, sha) = did_pass[test]
                logger.info(f'test_args=[{test_args!r}], did_pass=[{is_pass!r}], sha=[{sha!r}]')

        if 'externals' in test_matrix_config:
            externals_items = test_matrix_config['externals']

            for external in externals_items:
                rc = ask_compile_externals(**external)

                if rc != 0:
                    logger.error(f'Failed to build externals for os=[{external["os"]!r}].')
                    sys.exit(1)
                logger.info(f'Externals build for os=[{external["os"]!r}] succeeded.')
            

