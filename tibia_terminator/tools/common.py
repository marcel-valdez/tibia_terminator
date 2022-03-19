import os
import time
import logging

logger = logging.getLogger(__name__)


def acquire_lock(lock_file_path: str):
    with open(lock_file_path, "a", encoding="utf-8"):
        pass


def release_lock(lock_file_path):
    os.remove(lock_file_path)


def wait_for_lock(lock_file_path):
    if not os.path.exists(lock_file_path):
        return True

    logger.info("Another process locked the file %s, waiting.", lock_file_path)
    max_wait_retry_secs = 60 * 64
    wait_retry_secs = 60
    while wait_retry_secs <= max_wait_retry_secs:
        locked = os.path.exists(lock_file_path)
        if locked:
            logging.info("Still locked.")
            logging.info("Waiting %s seconds before retrying.", wait_retry_secs)
            time.sleep(wait_retry_secs)
        else:
            return True
        wait_retry_secs *= 2

    return False
