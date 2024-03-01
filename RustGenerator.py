#!/usr/bin/env python3

import os
from jinja2 import Environment, FileSystemLoader
import glob
from DesignSystem import DesignSystem
from FileSystemManager import FileSystemManager
from typing import Any


class RustGenerator:
    def __init__(self) -> None:
        basepath = os.path.dirname(__file__)
        basepath = os.path.join(basepath, "templates/")
        env = Environment(loader=FileSystemLoader(basepath))
        self.template = env.get_template("rust.jinja")

    def _prepare_data(
        self, source_data: dict[str, Any], source_path: str
    ) -> dict[str, Any]:
        data = {}
        data["design_system"] = source_data["id"]
        data["components_library_css_html"] = self._renderComponentsLibrariesCss(
            source_data
        )
        data[
            "components_library_dependencies"
        ] = self._getComponentsLibraryDependencies(source_data)
        data["components_library_js"] = self._getComponentsLibrariesJs(source_data)
        data["components_variant_template"] = self._getVariantsWithTemplates(
            source_data, source_path
        )
        data["components_with_library"] = self._getComponentsWithLibrary(
            source_data
        ).keys()
        data["default_libraries_css_html"] = self._renderDefaultLibrariesCss(
            source_data
        )
        data["default_libraries_js"] = self._getDefaultLibrariesJs(source_data)
        data["libraries_css_html"] = self._renderOtherLibrariesCss(source_data)
        data["libraries_js"] = self._getOtherLibrariesJs(source_data)
        data["libraries_keys"] = self._getOtherLibrariesDefinitions(source_data).keys()
        data["styles"] = DesignSystem.merge_styles_options(source_data)
        data["variables"] = self._getVariablesDefaultValues(source_data)
        data["themes"] = self._getThemes(source_data)
        return data

    def _getThemes(self, data: dict[str, Any]) -> dict[str, Any]:
        definitions = {}
        if "themes" not in data.keys():
            return {}
        for theme_id, theme in data["themes"].items():
            definitions[theme_id] = {
                "key": theme.get("key", "")
                if "key" in theme
                else "class"
                if "value" in theme
                else "",
                "target": theme["target"] if "target" in theme.keys() else "",
                "val": theme["value"] if "value" in theme.keys() else theme_id,
            }
        return definitions

    def _getDefaultLibrariesDefinitions(self, data: dict[str, Any]) -> dict[str, Any]:
        definitions = {}
        if "libraries" not in data.keys():
            return {}
        for library_id, library in data["libraries"].items():
            if "default" not in library.keys():
                continue
            if not library["default"]:
                continue
            definitions[library_id] = library
        return definitions

    # A flat list of links because all default libraries mixed together.
    def _getDefaultLibrariesCss(self, data: dict[str, Any]) -> dict[str, Any]:
        links: dict[str, dict[str, Any]] = {}
        for library_id, library in self._getDefaultLibrariesDefinitions(data).items():
            if "css" not in library.keys():
                continue
            links = links | library["css"]
        return links

    def _getDefaultLibrariesJs(self, data: dict[str, Any]) -> dict[str, Any]:
        links: dict[str, dict[str, Any]] = {}
        for library_id, library in self._getDefaultLibrariesDefinitions(data).items():
            if "js" not in library.keys():
                continue
            links = links | library["js"]
        return links

    # A single string  because all default libraries mixed together.
    def _renderDefaultLibrariesCss(self, data: dict[str, Any]) -> str:
        markup = ""
        for url, attributes in self._getDefaultLibrariesCss(data).items():
            attributes["href"] = url
            attributes["rel"] = "stylesheet"
            attributes["type"] = "text/css"
            markup += "<link" + self.renderAttributes(attributes) + ">\n"
        return markup

    def _getOtherLibrariesDefinitions(self, data: dict[str, Any]) -> dict[str, Any]:
        definitions = {}
        if "libraries" not in data.keys():
            return {}
        for library_id, library in data["libraries"].items():
            if "default" not in library.keys():
                definitions[library_id] = library
                continue
            if not library["default"]:
                definitions[library_id] = library
        return definitions

    def _getOtherLibrariesCss(self, data: dict[str, Any]) -> dict[str, Any]:
        libraries = {}
        for library_id, library in self._getOtherLibrariesDefinitions(data).items():
            if "css" not in library.keys():
                continue
            libraries[library_id] = library["css"]
        return libraries

    def _getOtherLibrariesJs(self, data: dict[str, Any]) -> dict[str, Any]:
        libraries = {}
        for library_id, library in self._getOtherLibrariesDefinitions(data).items():
            if "js" not in library.keys():
                continue
            libraries[library_id] = library["js"]
        return libraries

    # A map where keys are libraries ID, and values are rendered markup.
    def _renderOtherLibrariesCss(self, data: dict[str, Any]) -> dict[str, Any]:
        markups = {}
        for library_id, library in self._getOtherLibrariesCss(data).items():
            markup = ""
            for url, attributes in library.items():
                attributes["href"] = url
                attributes["rel"] = "stylesheet"
                attributes["type"] = "text/css"
                markup += "<link" + self.renderAttributes(attributes) + ">\n"
            if len(markup) == 0:
                continue
            markups[library_id] = markup
        return markups

    # A map where keys are components ID, and values are rendered markup.
    def _renderComponentsLibrariesCss(self, data: dict[str, Any]) -> dict[str, Any]:
        markups = {}
        for component_id, library in self._getComponentsLibrariesCss(data).items():
            markup = ""
            for url, attributes in library.items():
                attributes["href"] = url
                attributes["rel"] = "stylesheet"
                attributes["type"] = "text/css"
                markup += "<link" + self.renderAttributes(attributes) + ">\n"
            if len(markup) == 0:
                continue
            markups[component_id] = markup
        return markups

    def renderAttributes(self, attributes: dict[str, Any]) -> str:
        """Render attributes mapping as HTML string"""
        markup = ""
        for key, value in attributes.items():
            if type(value) not in (dict, tuple, list):
                markup += " " + key + '="' + str(value) + '"'
            if isinstance(value, list):
                markup += " " + key + '="' + " ".join(value) + '"'
        return markup

    # A map where keys are components ID, and values are url / attributes maps.
    def _getComponentsLibraryDependencies(self, data: dict[str, Any]) -> dict[str, Any]:
        libraries = {}
        for component_id, library in self._getComponentsWithLibrary(data).items():
            if "dependencies" not in library.keys():
                continue
            if not library["dependencies"]:
                continue
            libraries[component_id] = library["dependencies"]
        return libraries

    def _getComponentsWithLibrary(self, data: dict[str, Any]) -> dict[str, Any]:
        components = {}
        if "components" not in data.keys():
            return {}
        for component_id, component in data["components"].items():
            if "library" not in component.keys():
                continue
            if not component["library"]:
                continue
            components[component_id] = component["library"]
        return components

    # A map where keys are components ID, and values are url / attributes maps.
    def _getComponentsLibrariesJs(self, data: dict[str, Any]) -> dict[str, Any]:
        libraries = {}
        for component_id, library in self._getComponentsWithLibrary(data).items():
            if "js" not in library.keys():
                continue
            if not library["js"]:
                continue
            libraries[component_id] = library["js"]
        return libraries

    # A map where keys are components ID, and values are url / attributes maps.
    def _getComponentsLibrariesCss(self, data: dict[str, Any]) -> dict[str, Any]:
        libraries = {}
        for component_id, library in self._getComponentsWithLibrary(data).items():
            if "css" not in library.keys():
                continue
            if not library["css"]:
                continue
            libraries[component_id] = library["css"]
        return libraries

    def _getVariantsWithTemplates(
        self, data: dict[str, Any], source_path: str
    ) -> dict[str, Any]:
        SEPARATOR = "."
        variants = {}
        for component_id, component in data["components"].items():
            if "variants" not in component.keys():
                continue
            for variant_id in component["variants"].keys():
                filename = component_id + SEPARATOR + variant_id + ".jinja"
                pattern = source_path + "/components/**/" + filename
                paths = glob.glob(pattern, recursive=True)
                if not paths:
                    continue
                if component_id not in variants:
                    variants[component_id] = [variant_id]
                    continue
                variants[component_id].append(variant_id)
        return variants

    def _getVariablesDefaultValues(self, data: dict[str, Any]) -> dict[str, Any]:
        variables = {}
        if "variables" not in data.keys():
            return {}
        for variable_id, variable in data["variables"].items():
            # Temp: because renderer is not ready.
            if "default" not in variable.keys():
                continue
            for scope, default in variable["default"].items():
                if ":root" == scope:
                    variables[variable_id] = default
                    break
        # The expected behaviour is here.
        # variables[variable_id] = variable["default"]
        return variables

    def generate(self, data: dict[str, Any], source_path: str) -> str:
        """Generate Rust file using the Jinja template and design system data"""
        data = self._prepare_data(data, source_path)
        return self.template.render(data)

    def export(self, content: str, target_path: str) -> None:
        """Write content to a ds.rs in a target path"""
        path = os.path.join(target_path, "ds.rs")
        FileSystemManager.write_file(path, content)
