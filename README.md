## Usage

backup.py -c "name_container" or -a (backuping all Docker volumes) - Creating backups of containers, which have mounted named volumes

restore.py -a "path_to_backup_archive.tar.gz" -v "name_target_volume" - Import the backup archive into the target volume. Stop the container associated with the volume before restoration

## Cloud storage
Using rclone crypt with Google Drive backend

### TODO
- Add incremental backup