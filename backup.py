import argparse
import glob
import logging
import sys
import docker
import posixpath
import shutil
import docker.models.containers
from typing import Dict, List
from datetime import datetime
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
    volumes = [item['Name'] for item in list(filter(lambda d: d.get('Type') == 'volume', list_cont_vol))]

    logger = log.init_logger(constants.LOGS_DIR_BACKUP_MODE, container.name)

    if not volumes:
        logger.warning(f'The {container.name} container has no volumes...')
        return

    logger.info(f'Creating a backup of {container.name} container volumes')
    is_cont_run_before = False

    backup_name_archive = ''
    backup_end_point = ''

    name_file_snap_backup = ''

    tar_command = ''

    if container.status == 'running':
        is_cont_run_before = True
        logger.info(f'Stopping {container.name}')
        container.stop()

    for volume in volumes:
        if not volume in constants.LIST_EXCLUDE_VOLUMES:
            backup_end_point = posixpath.join(constants.BACKUP_DIR, container.name, volume)

            create_backups_dir(backup_end_point)

            logger.info(f'Creating a backup of the {volume} volume')

            list_snap_files = glob.glob(posixpath.join(backup_end_point, '*.snar'))
            
            backup_name_archive = f'{volume}_full-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.tar.gz'
            name_file_snap_backup = f'{volume}_full{constants.EXTENSION_FILE_SNAP_BACKUP}'

            if len(list_snap_files) > 0:
                if posixpath.join(backup_end_point, f'{volume}_full{constants.EXTENSION_FILE_SNAP_BACKUP}') in list_snap_files:
                    list_snap_diff_files = glob.glob(posixpath.join(backup_end_point, f'*diff*{constants.EXTENSION_FILE_SNAP_BACKUP}'))
                    count_snap_diff_files = len(list_snap_diff_files)

                    if count_snap_diff_files < constants.COUNT_DIFF_SNAPSHOTS:
                        count_snap_diff_files += 1
                        temp_name_file_snap_backup = f'{volume}_diff{count_snap_diff_files}{constants.EXTENSION_FILE_SNAP_BACKUP}'
                        shutil.copy(posixpath.join(backup_end_point, name_file_snap_backup), posixpath.join(backup_end_point, temp_name_file_snap_backup))

                        name_file_snap_backup = temp_name_file_snap_backup
                        backup_name_archive = f'{volume}_diff{count_snap_diff_files}-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.tar.gz'

            if len(list_snap_files) == constants.COUNT_SNAPSHOTS:
                raise RuntimeError(f'Error creating a full backup of the {volume} volume. Please delete old volume snapshots.')

            tar_command = (
                f'tar --totals --verbose --verbose --listed-incremental={posixpath.join(constants.PATH_CONT_MOUNT_DEST, name_file_snap_backup)} '
                f'--create --gzip --file={posixpath.join(constants.PATH_CONT_MOUNT_DEST, backup_name_archive)} '
                f'--directory={constants.PATH_CONT_MOUNT_SRC} ./'
            )

            bind = {
                volume : {
                    'bind' : constants.PATH_CONT_MOUNT_SRC,
                    'mode' : 'rw'
                },
                backup_end_point : {
                    'bind' : constants.PATH_CONT_MOUNT_DEST,
                    'mode' : 'rw'
                }
            }

            exec.run_container(
                client=client,
                image='ubuntu:24.04',
                command=tar_command,
                volumes=bind,
                environment=["LANG=C.UTF-8"],
                logger=logger
            )

            upload(
                client=client,
                logger=logger,
                backup_end_point=backup_end_point
            )

        else:
            logger.warning(f'Volume {volume} in the exclusion list. Skipping....')

    if is_cont_run_before == True:
        logger.info(f'Container {container.name} starting')
        container.start()
      
def upload(client: docker.DockerClient, logger: logging.Logger, backup_end_point: str) -> None:
    destination = posixpath.join(constants.REMOTE_STORAGE, "/".join(backup_end_point.split("/")[-2:]))

    cmd = f'sync --progress --progress {constants.PATH_CONT_MOUNT_DEST} {destination}'
    bind = {
        posixpath.join(str(Path.home()), '.config/rclone/rclone.conf') : {
            'bind' : '/config/rclone/rclone.conf',
            'mode' : 'rw'
        },
        backup_end_point: {
            'bind' : constants.PATH_CONT_MOUNT_DEST,
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