import logging
import sys
import posixpath
from datetime import datetime
from pathlib import Path
from src import constants

def init_logger(root_logs_dir: str, subdir: str) -> logging.Logger:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H\uA789%M\uA789%S")
    name_log_file = timestamp + '.log'

    path_dir_log = ''

    if subdir is None:
        path_dir_log = root_logs_dir
    else:
        path_dir_log = posixpath.join(root_logs_dir, subdir)
    
    full_path_log_file = posixpath.join(path_dir_log, name_log_file)

    Path(path_dir_log).mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    log_format = logging.Formatter('%(levelname)s %(asctime)s - %(message)s')

    file_handler = logging.FileHandler(filename=full_path_log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_format)

    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(log_format)

    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(stdout_handler)
    else:
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                logger.removeHandler(handler)
                handler.close()

        logger.addHandler(file_handler)

    return logger