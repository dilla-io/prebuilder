#!/usr/bin/env python3

from FileSystemManager import FileSystemManager
from DesignSystem import DesignSystem
import glob


class TemplateManager:
    def __init__(self, design_system: DesignSystem):
        self.design_system = design_system

    def copy(self, source_path: str, target_path: str) -> None:
        """Copy template files to the expected folder and replace placeholders"""
        pattern = source_path + "/components/**/*.jinja"
        paths = glob.glob(pattern, recursive=True)
        for path in paths:
            dst = path.replace(source_path, target_path)
            FileSystemManager.copy_file(path, dst)
            self._replace_placeholder(dst)

    def _replace_placeholder(self, path: str) -> None:
        with open(path, "r") as template:
            content = template.read()
            content = content.replace("@root/", self.design_system.cdn + "/")
        with open(path, "w") as template:
            template.write(content)
