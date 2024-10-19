#!/usr/bin/python3

import os
import re
import shutil
from time import sleep
import json
import datetime
import logging
import sys


class FileHandler:

    @staticmethod
    def get_files(path):
        return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

    @staticmethod
    def p_join(path: str, *paths: str):
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

    def add_pattern(self, pattern, executable=None):
        self.other_pattern.append((pattern, executable))

    def get_subdir(self, path):
        return [d for d in os.listdir(path) if (
                os.path.isdir(os.path.join(path, d))
                and d not in self.excluded_dirs)]

    def handle_file(self, dir_path, file, handled_debug = {}):
        if re.match(self.pattern, file):
            if 'default' not in handled_debug:
                handled_debug['default'] = []
            handled_debug['default'].append(file)
            self.move_file(dir_path, file)
        else:
            for pattern, executable in self.other_pattern:
                if re.match(pattern, file):
                    if pattern not in handled_debug:
                        handled_debug[pattern] = []
                    handled_debug[pattern].append(file)
                    if executable:
                        executable(file)
                    else:
                        self.move_file(dir_path, file)
                    break
            else:
                if 'unhandled' not in handled_debug:
                    handled_debug['unhandled'] = []
                handled_debug['unhandled'].append(file)

    def move_file(self, dir_path, file):
        target = self.p_join(self.target_dir, file)
        shutil.move(self.p_join(self.source_dir, dir_path, file), target)

    def check_dirs(self):
        current_dirs = self.get_subdir(self.source_dir)
        for checked_dir in self.checked_dirs:
            if checked_dir not in current_dirs:
                # remove from checked_dirs
                self.checked_dirs.remove(checked_dir)

        for i in current_dirs:
            if i not in self.checked_dirs:
                self.checked_dirs.append(i)
                self.logger.debug(f'Checking {i}')
                self.check_dir(i)
        self.logger.debug(f'Curently in checked: {self.checked_dirs}')
        

    def check_dir(self, dir_path):
        handled_debug = {}
        for file in self.get_files(self.p_join(self.source_dir, dir_path)):
            self.handle_file(dir_path, file, handled_debug)
        files_moved = 0
        for key in handled_debug:
            if key == 'unhandled':
                continue
            files_moved += len(handled_debug[key])
        self.logger.info(f'Folder "{dir_path}" checked, {files_moved} files handled')
        self.logger.debug(f'Handled files: {handled_debug}')

    def config_load(self, path_to_json):
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
        self.logger.info('Config loaded')

    def verify_config(self):
        self.logger.info('Validating data')
        if not os.path.isdir(self.source_dir):
            raise FileNotFoundError(f"Source directory {self.source_dir} not found")

        if not os.path.isdir(self.target_dir):
            raise FileNotFoundError(f"Target directory {self.target_dir} not found")

        if not self.pattern.startswith("^") or not self.pattern.endswith("$"):
            raise ValueError("Pattern not correctly set")

        for pattern, _ in self.other_pattern:
            if not pattern.startswith("^") or not pattern.endswith("$"):
                raise ValueError(f'Alt pattern "{pattern}" not set')

        if not isinstance(self.delay, int):
            raise ValueError("Delay must be an integer")
        self.logger.info("Checks passed")

    def main(self):
        self.logger.info('Start mainloop')
        while True:
            self.check_dirs()
            try:
                sleep(self.delay)
            except KeyboardInterrupt:
                break

