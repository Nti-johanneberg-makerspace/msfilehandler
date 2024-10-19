"""
Module Name: py_logger
Purpose: Create the logger object used in the project

Author: Carl Johan Ståhl
"""

# Imports
import logging


class PyLogger(logging.Logger):
    def __init__(self, name, log_file, session_log_file, verbose=False, level=logging.INFO):
        super().__init__(name, level)
        self.setLevel(level)

        general_handler = logging.FileHandler(filename=log_file)
        general_handler.setLevel(logging.INFO)

        session_handler = logging.FileHandler(filename=session_log_file, mode='w')
        session_handler.setLevel(logging.INFO)

        standard_format = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
        general_handler.setFormatter(standard_format)
        session_handler.setFormatter(standard_format)

        self.addHandler(general_handler)
        self.addHandler(session_handler)
        self.debug("Logger initialized")

        # If verbose is True, set the logger to debug
        if verbose:
            self.setLevel(logging.DEBUG)
            general_handler.setLevel(logging.DEBUG)
            session_handler.setLevel(logging.DEBUG)
            self.debug("Logger set to debug")

    def log_handled_dir(self, dir_path, files_moved, handled_debug):
        self.info(f'Folder "{dir_path}" checked, {files_moved} files handled')
        self.debug(f'Handled files: {handled_debug}')



"""
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
"""