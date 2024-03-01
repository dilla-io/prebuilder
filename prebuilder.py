#!/usr/bin/env python3

from FileSystemManager import FileSystemManager
from DesignSystem import DesignSystem
from RustGenerator import RustGenerator
from SchemaGenerator import SchemaGenerator
from ExamplesExporter import ExamplesExporter
import sys
import glob
import os
import logging
import coloredlogs

SOURCE_ROOT = "/data/input"
TARGET_ROOT = "/data/output"

coloredlogs.install(level="INFO", stream=sys.stdout)


def copy_templates(source_path: str, target_path: str) -> None:
    pattern = source_path + "/components/**/*.jinja"
    paths = glob.glob(pattern, recursive=True)
    for path in paths:
        dst = path.replace(source_path, target_path)
        FileSystemManager.copy_file(path, dst)


def copy_tests(source_path: str, target_path: str) -> None:
    if not os.path.exists(source_path + "/tests"):
        return
    FileSystemManager.copy_directory(source_path + "/tests", target_path + "/tests")


def copy_static_data(source_path: str, target_path: str) -> None:
    EXCLUDE_EXTENSIONS = [
        ".yaml",
        ".yml",
        ".json",
        ".twig",
        ".jinja",
        ".scss",
        ".css.map",
        ".js.map",
        ".py",
        ".php",
        ".theme",
        ".inc",
        ".md",
        "Makefile",
    ]
    EXCLUDE_FOLDERS = [
        "tests/",
    ]
    pattern = os.path.join(source_path, "**", "*")
    paths = glob.glob(pattern, recursive=True)
    paths = [path for path in paths if not os.path.isdir(path)]
    for folder in EXCLUDE_FOLDERS:
        folder = os.path.join(source_path, folder)
        paths = [path for path in paths if not path.startswith(folder)]
    for extension in EXCLUDE_EXTENSIONS:
        paths = [path for path in paths if not path.endswith(extension)]
    for path in paths:
        dst = path.replace(source_path, target_path)
        FileSystemManager.copy_file(path, dst)


def run_build(cdn: str) -> None:
    pattern = os.path.join(SOURCE_ROOT, "**", "info.yml")
    generic_schema = SchemaGenerator.get_generic_schema()
    for path in glob.glob(pattern, recursive=True):
        logging.info(path)
        source_path = os.path.dirname(path)
        target_path = source_path.replace(SOURCE_ROOT, TARGET_ROOT)
        target_path = os.path.join(target_path, "build/")
        design_system = DesignSystem(source_path, cdn)
        FileSystemManager.prepare_target(target_path)
        design_system.export(target_path)
        definition = design_system.getData()

        rust_generator = RustGenerator()
        rust = rust_generator.generate(definition, source_path)
        rust_generator.export(rust, target_path)

        schema_generator = SchemaGenerator(generic_schema)
        schema = schema_generator.generate(definition)
        schema_generator.export(schema, target_path)

        examples_exporter = ExamplesExporter()
        examples_exporter.export(definition, target_path)

        copy_templates(source_path, target_path)
        copy_tests(source_path, target_path)
    logging.info("Build folder created!")


def run_data() -> None:
    pattern = os.path.join(SOURCE_ROOT, "**", "info.yml")
    for path in glob.glob(pattern, recursive=True):
        logging.info(path)
        source_path = os.path.dirname(path)
        target_path = source_path.replace(SOURCE_ROOT, TARGET_ROOT)
        target_path = os.path.join(target_path, "data/")
        FileSystemManager.prepare_target(target_path)
        copy_static_data(source_path, target_path)
    logging.info("Data folder created!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        cdn = sys.argv[2] if len(sys.argv) > 2 else ""
        run_build(cdn)
        run_data()
    elif len(sys.argv) > 1 and sys.argv[1] == "build":
        cdn = sys.argv[2] if len(sys.argv) > 2 else ""
        run_build(cdn)
    elif len(sys.argv) > 1 and sys.argv[1] == "data":
        run_data()
    else:
        logging.error("Unknown command: %s", sys.argv[1])
        sys.exit()
