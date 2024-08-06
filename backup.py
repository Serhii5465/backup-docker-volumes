import argparse
import logging
import sys
import docker
import os
import subprocess
import posixpath
import docker.models.containers
from typing import Dict, List
from pathlib import Path
from src import constants, log

def create_backups_dir(dir_path: str) -> None:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

def run_container(client: docker.DockerClient, image: str, command: str, volumes: dict[str, str], environment: list, logger: logging.Logger) -> None:
        container = client.containers.run(
            image=image,
            volumes=volumes,
            command=command,
            environment=environment,
            remove=True,
            detach=True
        )

        for log in container.logs(stream=True):
            logger.info(log.decode('utf-8').strip())

def parse_args(containers_names: List[str]) -> Dict[str, any]:
    parser = argparse.ArgumentParser(description='Backup Docker volumes')
    group = parser.add_mutually_exclusive_group()

    group.add_argument('-a', '--all', action='store_true', help='Creating a backup of volumes for all containers on the host')
    group.add_argument('-c', help='Backup of volumes for specified containers',
                    default=None,
                    type=str,
                    choices=containers_names)

    args = vars(parser.parse_args())

    if len(sys.argv) == 1:
        parser.parse_args(['-h'])
    else:
        return args

def backup_volume(client: docker.DockerClient, container: docker.models.containers.Container, logger: logging.Logger) -> None:
    volumes = client.api.inspect_container(container.name)['Mounts']
    is_run_before = False
    
    type_vol = 'volume'
    name_vol = ''

    backup_name_archive = ''
    backup_end_point = posixpath.join(constants.BACKUP_DIR, container.name)

    if not volumes:
        logger.info('The ' + container.name + ' container has no mounted volumes...')
        return

    if container.status == 'running':
        is_run_before = True
        logger.info('Stopping ' + container.name)
        container.stop()

    create_backups_dir(backup_end_point)

    logger.info('Creating backup ' + container.name + ' container volumes')

    for item in volumes:
        if item['Type'] == type_vol:
            name_vol = item['Name']

            backup_name_archive = name_vol + '.tar.gz'
            cmd = 'tar --totals --verbose --verbose -c -z -f ' + posixpath.join('/backup', backup_name_archive) + ' -C /data ./'
            
            vol = {
                name_vol : {
                    'bind' : '/data',
                    'mode' : 'rw'
                },
                backup_end_point : {
                    'bind' : '/backup',
                    'mode' : 'rw'
                }
            }

            run_container(
                client=client,
                image='ubuntu:24.04',
                command=cmd,
                volumes=vol,
                environment=["LANG=C.UTF-8"],
                logger=logger
            )

            upload(
                client=client,
                logger=logger
            )
        
        elif item['Type'] == 'bind':
            logger.warning('The current volume is of type bind. Skipping')

    if is_run_before == True:
        logger.info('Container ' + container.name + ' starting')
        container.start()

def upload(client: docker.DockerClient, logger: logging.Logger) -> None:
    cmd = 'sync --progress --progress /backup docker-backup-vol:'
    volumes = {
        posixpath.join(str(Path.home()), '.config/rclone/rclone.conf') : {
            'bind' : '/config/rclone/rclone.conf',
            'mode' : 'rw'
        },
        constants.BACKUP_DIR : {
            'bind' : '/backup',
            'mode' : 'rw'
        }
    }

    run_container(
        client=client,
        image='rclone/rclone:1.67',
        command=cmd,
        volumes=volumes,
        environment=None,
        logger=logger
    )


def main() -> None:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    containers = client.containers.list(all=True)
    containers_names = [item.name for item in containers]

    args = parse_args(containers_names)
    
    logger = log.get_logger()

    if args['all'] is True:
        for item in containers:
            backup_volume(client, item, logger)

    if args['c']:
        for item in containers:
            if item.name == args['c']:
                backup_volume(client, item, logger)

    client.close()

if __name__ == "__main__":
    main()