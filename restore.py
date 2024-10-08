import logging
import docker
import argparse
import sys
import posixpath
import os
from pathlib import Path
from typing import Dict, List
from src import log, exec, constants

def parse_args(volume_names: List[str]) -> Dict[str, any]:
    parser = argparse.ArgumentParser(description='Backup Docker volumes')

    parser.add_argument('-a', '--archive', help='Path to the volume backup archive', required=True, type=str)
    parser.add_argument('-v', help='Volume name for restoration', required=True,
                    default=None,
                    type=str,
                    choices=volume_names)

    args = vars(parser.parse_args())

    if len(sys.argv) == 1:
        parser.parse_args(['-h'])
    else:
        return args

def restore_volume(client: docker.DockerClient, logger: logging.Logger, target_volume: str, path_archive: str) -> None:
    name_archive = os.path.basename(path_archive)

    bind_volumes = {
        target_volume : {
            'bind' : constants.PATH_CONT_MOUNT_DEST,
            'mode' : 'rw'
        },
        path_archive : {
            'bind' : posixpath.join('/', name_archive),
            'mode' : 'ro'
        }
    }

    tar_cmd = f'tar --listed-incremental=/dev/null --verbose --totals --gzip --extract --file={name_archive} --directory={constants.PATH_CONT_MOUNT_DEST}'

    logger.info(f'Restoring {target_volume}')

    exec.run_container(
        client=client,
        image='ubuntu:24.04',
        command=tar_cmd,
        volumes=bind_volumes,
        environment=["LANG=C.UTF-8"],
        logger=logger
    )

def main() -> None:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    args = parse_args([item.name for item in client.volumes.list()])

    path_archive = args['archive']
    volume = args['v']

    if not Path(path_archive).is_file() and not Path(path_archive).suffix == '.tar.gz':
        raise FileNotFoundError(f'The file {path_archive} does not exist')

    logger = log.init_logger(constants.LOGS_DIR_RESTORE_MODE, None)

    containers = client.containers.list(filters={'volume': volume})

    if not containers:
        logger.warning(f'The volume {volume} is not bound to any containers on the host')
    else:
        logger.info(f'The volume {volume} is bound to:')
        for item in containers:
            logger.info(f'Container ID: {item.id}, Name: {item.name}, Status: {item.status}')

            if item.status == 'running':
                item.stop()
                item.reload()
                logger.info(f'Current state of {item.name} is {item.status}')

    restore_volume(
        client=client,
        path_archive=path_archive,
        target_volume=volume,
        logger=logger
    )
    
if __name__ == "__main__":
    main()