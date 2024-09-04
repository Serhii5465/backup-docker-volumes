import posixpath
from pathlib import Path

BACKUP_DIR = '/mnt/backup_docker_volume'

LOGS_DIR_BACKUP_MODE = posixpath.join(str(Path.home()), '.logs/backup-docker-volumes')

LOGS_DIR_RESTORE_MODE = posixpath.join(str(Path.home()), '.logs/restore-docker-volumes')

REMOTE_STORAGE = 'docker-backup-vol:'

LIST_EXCLUDE_VOLUMES = ['vscode', 'jenkins_agent_data', 'mysql_data', 'npm-letsencrypt', 'serial_poll_logs', 'thingsboard-data', 'thingsboard-logs']

COUNT_DIFF_SNAPSHOTS = 2

COUNT_SNAPSHOTS = COUNT_DIFF_SNAPSHOTS + 1

EXTENSION_FILE_SNAP_BACKUP = '.snar'

PATH_CONT_MOUNT_SRC = '/data'

PATH_CONT_MOUNT_DEST = '/backup'