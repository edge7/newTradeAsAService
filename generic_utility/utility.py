import functools
import logging
import time
import threading
from notifications.email import try_to_send_email
from pathlib import Path
import os


logger = logging.getLogger(__name__)


def exception(function):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        exc = None
        for i in range(1, 4):
            try:
                return function(*args, **kwargs)
            except Exception as e:
                # log the exception
                err = "There was an exception in  "
                err += function.__name__
                logger.exception(err)
                logger.exception(e)
                exc = e
                time.sleep(5)

        logger.error("Unable to fix Exception .. raising")
        raise exc

    return wrapper


def notify_the_boss(message):
    try_to_send_email(message)


def notify(msg, CROSS):
    os.environ["PATH"] += os.pathsep + str(Path(__file__).parent.parent) + "/lib"
    msg = "[" + CROSS + "] " + msg
    th = threading.Thread(target=notify_the_boss, args=(msg,))
    th.start()



