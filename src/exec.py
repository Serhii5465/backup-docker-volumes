import logging
import docker

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