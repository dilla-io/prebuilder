#!/usr/bin/env python3

from FileSystemManager import FileSystemManager
import os
import sys
import yaml
from yaml.loader import SafeLoader
import glob
import stat
import validators
import json
import logging
import coloredlogs
from typing import Any

DEFAULT_CDN_ROOT = "https://data.dilla.io"

coloredlogs.install(level="INFO", stream=sys.stdout)


class DesignSystem:
    def __init__(self, root_path: str, cdn: str):
        self.root_path = root_path
        self.artifacts = {
            "component": "components",
            "style": "styles",
            "theme": "themes",
            "variable": "variables",
            "example": "examples",
            "library": "libraries",
        }
        data = self._get_full_definition()
        if not cdn:
            cdn = "/".join([DEFAULT_CDN_ROOT.rstrip("/"), data["id"]])
        self.cdn = cdn
        self.data = self._add_cdn_url(data)

    def getData(self) -> dict[str, Any]:
        """Get design system full definition with artefacts"""
        return self.data

    def _get_full_definition(self) -> dict[str, Any]:
        data = self._load_main_file()
        for artifact in self.artifacts:
            # Examples:
            # - color.style.yml
            # - examples/album.example.yml
            # - components/card/card.component.yml
            pattern = os.path.join(self.root_path, "**", "*." + artifact + ".yml")
            for path in glob.glob(pattern, recursive=True):
                data = self._load_file_with_single_item(path, data)
            # Examples:
            # - styles.yml
            # - libraries.yml
            plural = self.artifacts[artifact]
            pattern = os.path.join(self.root_path, "**", plural + ".yml")
            for path in glob.glob(pattern, recursive=True):
                data = self._load_file_with_multiple_items(path, data)
            # Examples:
            # - colors.styles.yml
            # - whatever/background.variables.yml
            pattern = os.path.join(self.root_path, "**", "*." + plural + ".yml")
            for path in glob.glob(pattern, recursive=True):
                data = self._load_file_with_multiple_items(path, data)
        data = self._fix_integer_keys(data)
        data = self._add_missing_component_id_to_examples(data)
        data = self._add_the_date(data)
        # TODO: extends mechanism
        return data

    def _resolve_path(self, path: str) -> str:
        path = os.path.dirname(path)
        path = path.removeprefix(self.root_path)
        if len(path) > 1:
            path = "/" + path.lstrip("/")
        return path

    def _fix_integer_keys(self, data: dict[str, Any]) -> dict[str, Any]:
        new = {}
        for key, value in data.items():
            if isinstance(value, dict):
                value = self._fix_integer_keys(value)
            new[str(key)] = value
        return new

    def _add_the_date(self, data: dict[str, Any]) -> dict[str, Any]:
        if "dateModified" not in data.keys():
            data["dateModified"] = self._get_last_modification(self.root_path)
        return data

    def _get_last_modification(self, path: str) -> int:
        date = 0
        for root, dirs, files in os.walk(path):
            for name in files:
                filepath = os.path.join(root, name)
                if ".git" in filepath:
                    continue
                if os.stat(filepath)[stat.ST_MTIME] > date:
                    date = int(os.stat(root)[stat.ST_MTIME])
            for name in dirs:
                dirpath = os.path.join(root, name)
                if ".git" in filepath:
                    continue
                if os.stat(dirpath)[stat.ST_MTIME] > date:
                    date = int(os.stat(root)[stat.ST_MTIME])
        return date

    def _add_cdn_url(self, data: dict[str, Any]) -> dict[str, Any]:
        if "libraries" in data.keys():
            for library_id, library in data["libraries"].items():
                path = library["_path"] if "_path" in library.keys() else ""
                library = self._add_cdn_url_to_library(library, path)
                data["libraries"][library_id] = library
        if "examples" in data.keys():
            for example_id, example in data["examples"].items():
                path = example["_path"] if "_path" in example.keys() else ""
                renderable = self._add_cdn_url_to_renderable(
                    example["renderable"], path
                )
                data["examples"][example_id]["renderable"] = renderable
        if "components" in data.keys():
            for component_id, component in data["components"].items():
                data["components"][component_id] = self._add_cdn_url_to_component(
                    component
                )
        return data

    def _add_cdn_url_to_component(self, component: dict[str, Any]) -> dict[str, Any]:
        path = component["_path"] if "_path" in component.keys() else ""
        if "library" in component.keys():
            library = self._add_cdn_url_to_library(component["library"], path)
            component["library"] = library
        if "examples" in component.keys():
            for example_id, example in component["examples"].items():
                renderable = self._add_cdn_url_to_renderable(
                    example["renderable"], path
                )
                component["examples"][example_id]["renderable"] = renderable
        return component

    def _add_cdn_url_to_library(
        self, library: dict[str, Any], path: str
    ) -> dict[str, Any]:
        if "css" in library.keys():
            for url, attributes in library["css"].copy().items():
                if validators.url(url):
                    continue
                new_url = url
                if not new_url.startswith("/"):
                    new_url = os.path.join(path, new_url)
                new_url = "/".join([self.cdn.rstrip("/"), new_url.lstrip("/")])
                library["css"][new_url] = attributes
                del library["css"][url]
        if "js" in library.keys():
            for url, attributes in library["js"].copy().items():
                if validators.url(url):
                    continue
                new_url = url
                if not new_url.startswith("/"):
                    new_url = os.path.join(path, new_url)
                new_url = "/".join([self.cdn.rstrip("/"), new_url.lstrip("/")])
                library["js"][new_url] = attributes
                del library["js"][url]
        return library

    def _add_cdn_url_to_renderable(
        self, data: dict[str, Any], path: str
    ) -> dict[str, Any]:
        if isinstance(data, list):
            for index, item in enumerate(data):
                data[index] = self._add_cdn_url_to_renderable(item, "")
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = self._add_cdn_url_to_renderable(value, "")
        if isinstance(data, str):
            if " " in data:
                return data
            if validators.url(data):
                return data
            data = self._add_cdn_url_to_path(data, path)
        return data

    def _add_cdn_url_to_path(self, data: str, path: str) -> str:
        for extension in ["jpg", "png", "jpeg", "svg"]:
            if not data.endswith("." + extension):
                continue
            if not data.startswith("/"):
                data = os.path.join(path, data)
            data = "/".join([self.cdn.rstrip("/"), data.lstrip("/")])
            return data
        return data

    def _load_main_file(self) -> dict[str, Any]:
        with open(self.root_path + "/info.yml") as file:
            return dict(yaml.load(file, Loader=SafeLoader))
        return {}

    def _load_file_with_multiple_items(
        self, path: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        filename = os.path.basename(path)
        _path = self._resolve_path(path)
        parts = filename.split(".")
        if len(parts) == 3:
            whatever, artifact_plural, extension = parts
        if len(parts) == 2:
            artifact_plural, extension = parts
        if not artifact_plural:
            return data
        with open(path) as file:
            if artifact_plural not in data.keys():
                data[artifact_plural] = {}
            items = yaml.load(file, Loader=SafeLoader)
            for item_id, item in items.items():
                item = self._add_missing_ids(item_id, artifact_plural, item)
                if _path:
                    item["_path"] = _path
                data[artifact_plural][item_id] = item
        return data

    def _add_missing_ids(
        self, item_id: str, artifact_plural: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        if "id" in data.keys() and data["id"] != item_id:
            logging.error("%s %s has conflicting IDs", item_id, artifact_plural)
        data = {"id": item_id} | data
        subs = {
            "components": ["variants", "slots", "props", "examples"],
            "styles": [
                "options",
            ],
        }
        if artifact_plural not in subs.keys():
            return data
        for sub in subs[artifact_plural]:
            if sub not in data.keys():
                continue
            for sub_id, sub_item in data[sub].items():
                data[sub][sub_id] = self._add_missing_ids(sub_id, sub, sub_item)
        if artifact_plural != "components":
            return data
        if "library" not in data.keys():
            return data
        if "id" not in data["library"].keys():
            data["library"]["id"] = item_id
        return data

    def _add_missing_component_id_to_examples(
        self, data: dict[str, Any]
    ) -> dict[str, Any]:
        if "components" not in data.keys():
            return data
        for component_id, component in data["components"].items():
            if "examples" not in component.keys():
                continue
            for example_id, example in component["examples"].items():
                renderable = (
                    example["renderable"] if "renderable" in example.keys() else {}
                )
                renderable = {"@component": component_id} | renderable
                data["components"][component_id]["examples"][example_id][
                    "renderable"
                ] = renderable
        return data

    def _load_file_with_single_item(
        self, path: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        filename = os.path.basename(path)
        _path = self._resolve_path(path)
        item_id, artifact, extension = filename.split(".")
        plural = self.artifacts[artifact]
        with open(path) as file:
            if plural not in data.keys():
                data[plural] = {}
            item = yaml.load(file, Loader=SafeLoader)
            item = self._add_missing_ids(item_id, plural, item)
            if _path:
                item["_path"] = _path
            data[plural][item_id] = item
        return data

    @staticmethod
    def merge_styles_options(data: dict[str, Any]) -> list[str]:
        """Merge options of every styles in a single list"""
        if "styles" not in data.keys():
            return []
        options: set[str] = set()
        for style in data["styles"].values():
            style_options = set(style["options"].keys())
            options = options | style_options
        return sorted(options)

    def export(self, target_path: str) -> None:
        """Export full design system definition in a single JSON file"""
        content = json.dumps(self.data, indent=4, ensure_ascii=False)
        path = os.path.join(target_path, "definitions.json")
        FileSystemManager.write_file(path, content)
