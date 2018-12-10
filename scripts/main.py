import logging
from logging.config import fileConfig
from os import path
import argparse
import threading

log_file_path = path.join(path.dirname(path.abspath(__file__)), 'logging_config.ini')
logging.config.fileConfig(log_file_path)
logger = logging.getLogger(__name__)


from manual_trader.manual_scan import ManualScan
from webserver.app import run



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("path", help ="Path base directory MQL4")
    args = parser.parse_args()
    path = args.path
    logger.info("Starting app with base path: %s " % path)
    # Starting Manual Thread
    ms = ManualScan(path)
    manualScanThread = threading.Thread(target=ms.loop_and_update)
    # Starting Algo Thhread
    th = threading.Thread(target=run, args=(ms,))
    th.start()
    manualScanThread.start()