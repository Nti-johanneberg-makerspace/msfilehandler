#!/usr/bin/python3

import logging
import sys

from fileHandler import FileHandler



def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))



if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logging.root.setLevel(logging.NOTSET)
    logger.setLevel(0)
    general_handler = logging.FileHandler(filename='/home/makerspace/msfilehandler/filehandler.log')
    general_handler.setLevel(20)
    session_handler = logging.FileHandler(filename='/home/makerspace/msfilehandler/filehandler.session.log', mode='w')
    
    standard_format = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
    general_handler.setFormatter(standard_format)
    session_handler.setFormatter(standard_format)
    
    
    logger.addHandler(general_handler)
    logger.addHandler(session_handler)
    logger.debug("Test")
    
    sys.excepthook = handle_exception
    
    fh = FileHandler(logger)
    fh.config_load("/home/makerspace/msfilehandler/config.json")
    fh.verify_config()
    fh.main()
    # fh.check_dirs()
