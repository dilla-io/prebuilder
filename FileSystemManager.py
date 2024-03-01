#!/usr/bin/env python3

import os
import sys
import shutil
import logging
import coloredlogs

coloredlogs.install(level="INFO", stream=sys.stdout)


class FileSystemManager:
    @staticmethod
    def prepare_target(target_path: str) -> None:
        """Prepare target path by deleting existing content"""
        if os.path.exists(target_path):
            logging.info("PURGE %s", target_path)
            shutil.rmtree(target_path)
        os.makedirs(target_path, exist_ok=True)

    @staticmethod
    def write_file(path: str, content: str) -> None:
        """Create missing folders and write file"""
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
            os.makedirs(dir, exist_ok=True)
        with open(path, "w") as file:
            file.write(content)

    @staticmethod
    def copy_file(source_path: str, target_path: str) -> None:
        """Create missing folders and copy file to new path"""
        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
        shutil.copyfile(source_path, target_path)

    @staticmethod
    def copy_directory(source_path: str, target_path: str) -> None:
        """Create missing folders and copy directory to new path"""
        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
        shutil.copytree(source_path, target_path)
