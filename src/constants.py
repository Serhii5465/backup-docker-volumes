import posixpath
from pathlib import Path

BACKUP_DIR = posixpath.join(str(Path.home()), 'backup/docker-volumes')

LOGS_DIR = posixpath.join(str(Path.home()), '.logs/backup-docker-vol')

VERSIONS = 3