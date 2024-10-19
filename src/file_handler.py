#!/usr/bin/python3

import os
import re
import shutil
from time import sleep
import json
import datetime
import logging

from functools import wraps

def is_valid(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self._valid:
            self.verify_config()
        if not self._valid:
            raise ValueError("Invalid operation: self._valid is False")
        return func(self, *args, **kwargs)
    return wrapper


class FileHandler:

    @staticmethod
    def get_files(path: str) -> list:
        """
        Get all files in a directory
        :param path: str
        :return: list
        """
        return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

    @staticmethod
    def p_join(path: str, *paths: str) -> str:
        """
        Shortcut for os.path.join
        :param path: str
        :param paths: List[str]
        :return:
        """
        return os.path.join(path, *paths)

    def __init__(self, logger):
        self.target_dir = ""
        self.source_dir = ""

        self.pattern = ""
        self.other_pattern = []

        self.excluded_dirs = []
        self.checked_dirs = []

        self.delay = 30

        self.logger = logger
        self.logger.info('File Handler initialized')

        self._valid = False

        self.purge_delay = 0
        self._last_purge = None

    def config_load(self, path_to_json: str) -> None:
        """
        Load configuration from a json file
        :param path_to_json:
        :return:
        """
        self.logger.info('Config load begin')
        with open(path_to_json, "r") as f:
            data = json.load(f)

        self.source_dir = data["source_dir"]
        self.target_dir = data["target_dir"]

        self.pattern = data["pattern"]
        self.other_pattern = [(i['pattern'], i['exec']) for i in data["other_pattern"]]

        self.excluded_dirs = data["excluded_dirs"]
        self.delay = data["delay"]

        if bool(data['verbose']):
            self.logger.setLevel(logging.DEBUG)

        self.purge_delay = data["purge_after"]

        self.logger.info('Config loaded')

    def verify_config(self):
        """
        Verify that the configuration is correct, If not it will raise an error. Many methods are decorated with
        @is_valid, which will call this method before executing the method. If the configuration is invalid, the method
        will raise an error.
        :return:
        """
        self.logger.info('Validating data')

        # Check if source exists
        if not os.path.isdir(self.source_dir):
            raise FileNotFoundError(f"Source directory {self.source_dir} not found")

        # Check if target exists
        if not os.path.isdir(self.target_dir):
            raise FileNotFoundError(f"Target directory {self.target_dir} not found")

        # Check if pattern is correctly set
        if not self.pattern.startswith("^") or not self.pattern.endswith("$"):
            raise ValueError("Pattern not correctly set")

        # Check if other patterns are correctly set
        for pattern, _ in self.other_pattern:
            if not pattern.startswith("^") or not pattern.endswith("$"):
                raise ValueError(f'Alt pattern "{pattern}" not set')

        # Check if delay is an integer
        if not isinstance(self.delay, int):
            raise ValueError("Delay must be an integer")

        # Ensure purge_delay is an integer greater than 0
        if not isinstance(self.purge_delay, int) or self.purge_delay < 0:
            raise ValueError("Purge delay must be an integer greater than 0")

        self.logger.info("Checks passed")

        self._valid = True

    def add_pattern(self, pattern, executable=None):
        self.other_pattern.append((pattern, executable))

    def get_subdirs(self, path : str) -> list:
        """

        :param path: str
        :return: list
        """

        return [
            d for d in os.listdir(path)
            if os.path.isdir(os.path.join(path, d)) and d not in self.excluded_dirs
        ]
    @is_valid
    def handle_file(self, dir_path: str, file: str, handled_debug: dict):
        """
        Handle file based on patterns. If no pattern matches
        :param dir_path: str
        :param file: str
        :param handled_debug: dict
        :return:
        """

        # Check if file matches the default pattern
        if re.match(self.pattern, file):
            handled_debug['default'].append(file)
            self.move_file(dir_path, file)
            return

        # Check if file matches any of the other patterns
        for pattern, executable in self.other_pattern:
            if re.match(pattern, file):
                handled_debug[pattern].append(file)
                if executable:
                    executable(file)
                    return

                self.move_file(dir_path, file)
                return

        # If no pattern matches, log the file as unhandled
        handled_debug['unhandled'].append(file)

    @staticmethod
    def format_file_name(file: str) -> str:
        """
        Format the file name to include the day of the month. We only want the day of the month to be included
        in the file name, otherwise the file name will be too long. Additionally, all files will be cleaned up
        after a set period of time, so the day of the month is sufficient.

        :param file: str
        :return: str
        """
        return f'{datetime.date.today().day}_{file}'

    def move_file(self, dir_path: str, file: str) -> None:
        """
        Move file from source to target directory.
        :param dir_path: str
        :param file: str
        :return: None
        """
        source_path = self.p_join(self.source_dir, dir_path, file)
        target_path = self.p_join(self.target_dir, self.format_file_name(file))
        shutil.move(source_path, target_path)

    @is_valid
    def check_dirs(self):
        """
        Check all directories in source_dir for files. If a directory is not in checked_dirs, check it and add it to
        checked_dirs. If a directory is not in the current directories, remove it from checked_dirs. This is to ensure
        that all discs are checked once before they are removed.
        :return: None
        """
        current_dirs = self.get_subdirs(self.source_dir)

        # Remove USBs that are removed
        for checked_dir in self.checked_dirs:
            if checked_dir not in current_dirs:
                # remove from checked_dirs
                self.checked_dirs.remove(checked_dir)

        # Check all current USBs
        for i in current_dirs:
            if i not in self.checked_dirs:
                self.checked_dirs.append(i)
                self.logger.debug(f'Checking {i}')
                self.check_dir(i)
        self.logger.debug(f'Curently in checked: {self.checked_dirs}')
        
    @is_valid
    def check_dir(self, dir_path: str) -> None:
        """
        Check a USB for files. If a file matches the default pattern, move it to the target directory. If a file matches
        any of the other patterns, execute the function associated with the pattern. If no pattern matches, log the file
        as unhandled. If an extra pattern matches but lacks an executable, move the file to the target directory as normal.

        :param dir_path: str
        :return: None
        """
        # Create a dictionary to store the handled files, used for logging
        logger_categories = ['default', 'unhandled'] + [i[0] for i in self.other_pattern]
        log_handled = {key: [] for key in logger_categories}

        for file in self.get_files(self.p_join(self.source_dir, dir_path)):
            self.handle_file(dir_path, file, log_handled)

        # Count the total number of files handled
        files_handled = sum(len(files) for key, files in log_handled.items() if key != 'unhandled')

        # Send log to logger
        self.logger.log_handled_dir(dir_path, files_handled, log_handled)

    def purge_files(self):
        """
        Purge files in the target directory. The files will be purged based on the day of the month. If the file name
        contains the day of the month, the file will be removed. This is to ensure that the files are not kept for too
        long.
        :return: None
        """
        self.logger.info('Purging files')

        # if last purge is not set or the day has changed, purge the files
        if not self._last_purge or self._last_purge.day != datetime.date.today().day:
            self._last_purge = datetime.datetime.now()

             # get day of the month 3 days ago
            day = (datetime.datetime.now() - datetime.timedelta(days=self.purge_delay)).day

            purge_count = 0

            # remove all files that contain the day of the month or older
            for file in self.get_files(self.target_dir):
                # get the day of the month from the file name
                # pattern: <day>_<filename>

                try:
                    file_day = int(file.split('_')[0])
                except ValueError:
                    continue

                # if the day is older than the set day, remove the file
                if file_day <= day:
                    os.remove(self.p_join(self.target_dir, file))
                    purge_count += 1

            self.logger.info(f'Purged {purge_count} files')

    @is_valid
    def main(self):
        """
        :return:
        """
        self.logger.info('Start mainloop')
        while True:
            self.check_dirs()
            self.purge_files()
            try:
                sleep(self.delay)
            except KeyboardInterrupt:
                break

