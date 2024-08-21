import posixpath
from pathlib import Path

BACKUP_DIR = posixpath.join(str(Path.home()), 'backup/docker-volumes')

LOGS_DIR_BACKUP_MODE = posixpath.join(str(Path.home()), '.logs/backup-docker-volumes')

LOGS_DIR_RESTORE_MODE = posixpath.join(str(Path.home()), '.logs/restore-docker-volumes')

REMOTE_STORAGE = 'docker-backup-vol:'