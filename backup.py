import argparse
import logging
import sys
import docker
import posixpath
import docker.models.containers
from typing import Dict, List
from pathlib import Path
from src import constants, log, exec

def create_backups_dir(dir_path: str) -> None:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

def parse_args(containers_names: List[str]) -> Dict[str, any]:
    """
    Parse command-line arguments to determine which containers' volumes to back up.

    Args:
        containers_names (List[str]): List of container names available on the Docker host.

    Returns:
        Dict[str, any]: A dictionary containing parsed command-line arguments.
    """
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

def backup_volume(client: docker.DockerClient, container: docker.models.containers.Container) -> None:
    """
    Create a backup of the Docker volumes attached to a specific container.

    Args:
        client (docker.DockerClient): Docker client instance.
        container (docker.models.containers.Container): The container whose volumes will be backed up.
        logger (logging.Logger): Logger for logging backup process information.
    """
    # Get the list of mounts (volumes) for the container
    list_cont_vol = client.api.inspect_container(container.name)['Mounts']

    # Filter to get only volumes (not bind mounts)
    volumes = list(filter(lambda d: d.get('Type') == 'volume', list_cont_vol))

    logger = log.init_logger(constants.LOGS_DIR_BACKUP_MODE, container.name)

    if not volumes:
        logger.warning('The ' + container.name + ' container has no volumes...')
        return

    logger.info('Creating a backup of ' + container.name + ' container volumes')

    is_cont_run_before = False
    curr_name_vol = ''

    backup_name_archive = ''
    backup_end_point = posixpath.join(constants.BACKUP_DIR, container.name)

    if container.status == 'running':
        is_cont_run_before = True
        logger.info('Stopping ' + container.name)
        container.stop()

    create_backups_dir(backup_end_point)

    for volume in volumes:
        source = volume['Name']
        logger.info('Creating a backup of the ' + source + ' volume')

        backup_name_archive = source + '.tar.gz'
        cmd = 'tar --totals --verbose --verbose --create --gzip --file=' + posixpath.join('/backup', backup_name_archive) + ' --directory=/data ./'
        
        bind = {
            source : {
                'bind' : '/data',
                'mode' : 'rw'
            },
            backup_end_point : {
                'bind' : '/backup',
                'mode' : 'rw'
            }
        }

        exec.run_container(
            client=client,
            image='ubuntu:24.04',
            command=cmd,
            volumes=bind,
            environment=["LANG=C.UTF-8"],
            logger=logger
        )

        upload(
            client=client,
            logger=logger,
            sync_dir=container.name
        )

    if is_cont_run_before == True:
        logger.info('Container ' + container.name + ' starting')
        container.start()
      
def upload(client: docker.DockerClient, logger: logging.Logger, sync_dir: str) -> None:
    host_source = posixpath.join(constants.BACKUP_DIR, sync_dir)
    cont_source = '/backup'
    destination = posixpath.join(constants.REMOTE_STORAGE, sync_dir)

    cmd = 'sync --progress --progress ' + cont_source + ' ' + destination
    bind = {
        posixpath.join(str(Path.home()), '.config/rclone/rclone.conf') : {
            'bind' : '/config/rclone/rclone.conf',
            'mode' : 'rw'
        },
        host_source: {
            'bind' : cont_source,
            'mode' : 'rw'
        }
    }
    
    exec.run_container(
        client=client,
        image='rclone/rclone:1.67',
        command=cmd,
        volumes=bind,
        environment=None,
        logger=logger
    )

def main() -> None:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    containers = client.containers.list(all=True)
    containers_names = [item.name for item in containers]

    args = parse_args(containers_names)
    
    if args['all'] is True:
        for item in containers:
            backup_volume(client, item)

    if args['c']:
        for item in containers:
            if item.name == args['c']:
                backup_volume(client, item)

    client.close()

if __name__ == "__main__":
    main()