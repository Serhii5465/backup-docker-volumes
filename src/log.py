import logging
import sys
import posixpath
from datetime import datetime
from pathlib import Path
from src import constants

def get_logger(label: str) -> logging.Logger:
    """
    Creating file of logging and Logger object with custom preset.
    Returns:
        Instance of Logger.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H\uA789%M\uA789%S")

    full_path_log_file = posixpath.join(constants.LOGS_DIR, label + '_' + timestamp + '.log')

    Path(constants.LOGS_DIR).mkdir(parents=True, exist_ok=True)

    log_format = "%(levelname)s %(asctime)s - %(message)s"
    file_handler = logging.FileHandler(filename=full_path_log_file)
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    handlers = [file_handler, stdout_handler]

    logging.basicConfig(level=logging.INFO,
                        format=log_format,
                        handlers=handlers) 

    return logging.getLogger()