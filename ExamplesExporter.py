#!/usr/bin/env python3

from FileSystemManager import FileSystemManager
import os
import json
from typing import Any


class ExamplesExporter:
    def export(self, data: dict[str, Any], target_path: str) -> None:
        """Export examples and component examples to JSON files"""
        self._export_examples(data, target_path)
        self._export_components_examples(data, target_path)

    def _export_examples(self, data: dict[str, Any], target_path: str) -> None:
        if "examples" not in data:
            return
        for example_id, example in data["examples"].items():
            if "renderable" not in example:
                continue
            renderable = example["renderable"]
            if renderable is list and len(renderable) == 1:
                renderable = renderable[0]
            parts = [
                target_path,
                "examples",
                example_id + ".json",
            ]
            path = os.path.join(*parts)
            content = json.dumps(renderable, indent=4, ensure_ascii=False)
            FileSystemManager.write_file(path, content)

    def _export_components_examples(
        self, data: dict[str, Any], target_path: str
    ) -> None:
        for component_id, component in data["components"].items():
            if "examples" not in component:
                continue
            for example_id, example in component["examples"].items():
                if "renderable" not in example:
                    continue
                renderable = example["renderable"]
                if renderable is list and len(renderable) == 1:
                    renderable = renderable[0]
                parts = [
                    target_path,
                    "components",
                    component_id,
                    example_id + ".json",
                ]
                path = os.path.join(*parts)
                content = json.dumps(renderable, indent=4, ensure_ascii=False)
                FileSystemManager.write_file(path, content)
