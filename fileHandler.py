import os
import re
import shutil
from time import sleep
import json

class FileHandler:

    @staticmethod
    def get_files(path):
        return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

    @staticmethod
    def p_join(path: str, *paths: str):
        return os.path.join(path, *paths)

    def __init__(self):
        self.target_dir = ""
        self.source_dir = ""
        self.pattern = ""
        self.other_pattern = []
        self.excluded_dirs = []
        self.checked_dirs = []
        self.delay = 30

    def add_pattern(self, pattern, executable=None):
        self.other_pattern.append((pattern, executable))

    def get_subdir(self, path):
        return [d for d in os.listdir(path) if (
                os.path.isdir(os.path.join(path, d))
                and d not in self.excluded_dirs)]

    def handle_file(self, file):
        if re.match(self.pattern, file):
            self.move_file(file)
        else:
            for pattern, executable in self.other_pattern:
                if re.match(pattern, file):
                    if executable:
                        executable(file)
                    else:
                        self.move_file(file)

    def move_file(self, file):
        shutil.move(self.p_join(self.source_dir, file), self.p_join(self.target_dir, file))

    def check_dirs(self):
        current_dirs = self.get_subdir(self.source_dir)
        for checked_dir in self.checked_dirs:
            if checked_dir not in current_dirs:
                # remove from checked_dirs
                self.checked_dirs.remove(checked_dir)

        for i in current_dirs:
            if i not in self.checked_dirs:
                self.checked_dirs.append(i)
                self.check_dir(i)

    def check_dir(self, dir_path):
        for file in self.get_files(self.p_join(self.source_dir, dir_path)):
            self.handle_file(file)

    def config_load(self, path_to_json):
        with open(path_to_json, "r") as f:
            data = json.load(f)
        self.source_dir = data["source_dir"]
        self.target_dir = data["target_dir"]
        self.pattern = data["pattern"]
        self.other_pattern = [(i['pattern'], i['exec']) for i in data["other_pattern"]]
        self.excluded_dirs = data["excluded_dirs"]
        self.delay = data["delay"]

    def verify_config(self):
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

    def main(self):
        while True:
            self.check_dirs()
            try:
                sleep(self.delay)
            except KeyboardInterrupt:
                break


if __name__ == '__main__':
    fh = FileHandler()
    fh.config_load("config.json")
    fh.verify_config()
    fh.main()




