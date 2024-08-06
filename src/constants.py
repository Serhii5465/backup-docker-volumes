import posixpath
from pathlib import Path

BACKUP_DIR = posixpath.join(str(Path.home()), 'backup/docker-volumes')

VERSIONS = 3