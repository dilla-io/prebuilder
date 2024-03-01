#!/usr/bin/env python3

import validators
import os
import json
import requests
import mergedeep
from DesignSystem import DesignSystem
from FileSystemManager import FileSystemManager
from typing import Any

GENERIC_SCHEMA_PATH = (
    "https://gitlab.com/dilla-io/schemas/-/raw/master/renderable.schema.json"
)


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        """A snippet taken from StackOverflow"""
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


class SchemaGenerator:
    def __init__(self, generic_schema: str):
        self.generic_schema: dict[str, Any] = json.loads(generic_schema)

    @staticmethod
    def get_generic_schema() -> str:
        """Get generic JSON schema"""
        generic_schema_path = os.environ.get("SCHEMA", GENERIC_SCHEMA_PATH)
        if validators.url(generic_schema_path):
            return requests.get(generic_schema_path, timeout=5).text
        with open(generic_schema_path) as file:
            return file.read()

    def generate(self, definition: dict[str, Any]) -> dict[str, Any]:
        """Generate a specific schema from design system definition and the generic schema"""
        schema = self.generic_schema
        if "components" in definition.keys():
            schema = self._build_components_schema(definition, schema)
        if "styles" in definition.keys():
            schema = mergedeep.merge(schema, self._add_styles_properties(definition))
        if "themes" in definition.keys():
            schema = mergedeep.merge(schema, self._add_theme_properties(definition))
        if "variables" in definition.keys():
            schema = mergedeep.merge(
                schema, self._add_local_variables_properties(definition)
            )
        for def_id, definition in schema["$defs"].items():
            schema["$defs"][def_id] = self._clean(definition)
        return schema

    def _build_components_schema(
        self, definition: dict[str, Any], schema: dict[str, Any]
    ) -> dict[str, Any]:
        refs = []
        for component_id, component in definition["components"].items():
            component_schema = schema["$defs"]["component_renderable"]
            component_schema["properties"]["@component"] = {
                "const": component_id,
            }
            # Add variants enum.
            if "variants" in component:
                component_schema["properties"]["@variant"]["enum"] = list(
                    component["variants"].keys()
                )
            # Replace patternProperties with slots & props.
            if "props" in component.keys():
                for prop_id, prop in component["props"].items():
                    component_schema["properties"][prop_id] = prop["schema"]
            if "slots" in component.keys():
                for slot_id, slot in component["slots"].items():
                    component_schema["properties"][slot_id] = {
                        "$ref": "#/$defs/slot_value"
                    }
            if "patternProperties" in component_schema.keys():
                del component_schema["patternProperties"]
            schema["$defs"]["component_renderable__" + component_id] = component_schema
            refs.append(
                {
                    "if": {
                        "properties": {"@component": {"const": component_id}},
                    },
                    "then": {
                        "$ref": "#/$defs/component_renderable__" + component_id,
                    },
                    "else": False,
                }
            )
        schema["$defs"]["component_renderable"] = {
            "type": "object",
            "required": ["@component"],
            "anyOf": refs,
        }
        return schema

    def _add_styles_properties(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "$defs": {
                "styles_property": {
                    "items": {"enum": DesignSystem.merge_styles_options(data)}
                }
            }
        }

    def _add_theme_properties(self, data: dict[str, Any]) -> dict[str, Any]:
        return {"$defs": {"theme_property": {"enum": list(data["themes"].keys())}}}

    def _add_local_variables_properties(self, data: dict[str, Any]) -> dict[str, Any]:
        variable_properties = {}
        for variable_id, variable in data["variables"].items():
            variable_type = variable["type"]
            if variable_type not in ["string", "number", "integer", "boolean"]:
                variable_type = "string"
            variable_properties[variable_id] = {"type": variable_type}
        return {
            "$defs": {
                "local_variables_property": {
                    "additionalProperties": False,
                    "properties": variable_properties,
                }
            }
        }

    def _clean(self, definition: dict[str, Any]) -> dict[str, Any]:
        definition = self._clean_property("title", definition)
        definition = self._clean_property("description", definition)
        definition = self._clean_property("examples", definition)
        definition = self._clean_property("default", definition)
        if "properties" in definition.keys():
            for index, item in definition["properties"].items():
                definition["properties"][index] = self._clean(item)
        if "patternProperties" in definition.keys():
            for index, item in definition["patternProperties"].items():
                definition["patternProperties"][index] = self._clean(item)
        if "anyOf" in definition.keys():
            for index, item in enumerate(definition["anyOf"]):
                definition["anyOf"][index] = self._clean(item)
        return definition

    def _clean_property(self, prop: str, definition: dict[str, Any]) -> dict[str, Any]:
        if prop in definition.keys():
            del definition[prop]
        return definition

    def export(self, data: dict[str, Any], target_path: str) -> None:
        """Write JSON serialized data to  renderable.schema.json"""
        path = os.path.join(target_path, "renderable.schema.json")
        content = json.dumps(data, indent=4, ensure_ascii=False, cls=SetEncoder)
        FileSystemManager.write_file(path, content)
