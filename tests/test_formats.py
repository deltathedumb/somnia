from __future__ import annotations

import json
import unittest

from somnia import (
    DataModel,
    ModelDocument,
    NativeFunction,
    NativeLibrary,
    NativeLibraryService,
    PortaPyRuntime,
    PythonScript,
    ScriptService,
)
from somnia.formats import (
    data_to_document,
    document_to_data,
    dumps_sem,
    dumps_semj,
    loads_sem,
    loads_semj,
)


class ModelFormatTests(unittest.TestCase):
    def make_document(self) -> ModelDocument:
        data_model = DataModel(object_id="data", name="Game")

        libraries = NativeLibraryService(object_id="native", name="NativeLibraries")
        data_model.add_child(libraries)
        library = NativeLibrary(object_id="lib", name="ProjectCore")
        library.windows_path = "native/project_core.dll"
        library.linux_path = "native/libproject_core.so"
        libraries.add_child(library)
        function = NativeFunction(object_id="fn", name="project_add")
        function.arguments = ["int", "int"]
        function.result = "int"
        library.add_child(function)

        scripts = ScriptService(object_id="scripts", name="Scripts")
        data_model.add_child(scripts)
        portapy = PortaPyRuntime(object_id="portapy", name="PortaPy")
        scripts.add_child(portapy)
        script = PythonScript(object_id="script", name="Startup")
        script.source = "answer = 40 + 2"
        portapy.add_child(script)

        return ModelDocument("Game", [data_model], {"author": "Pixelated Dream"})

    def test_semj_is_literal_json_and_round_trips_objects(self) -> None:
        source = self.make_document()
        text = dumps_semj(source)
        parsed_json = json.loads(text)
        self.assertEqual(parsed_json["format"], "somnia-model")

        loaded = loads_semj(text)
        by_id = loaded.by_id()
        self.assertIsInstance(by_id["lib"], NativeLibrary)
        self.assertIsInstance(by_id["fn"], NativeFunction)
        self.assertIsInstance(by_id["portapy"], PortaPyRuntime)
        self.assertIsInstance(by_id["script"], PythonScript)
        self.assertEqual(by_id["lib"].linux_path, "native/libproject_core.so")
        self.assertEqual(by_id["fn"].arguments, ["int", "int"])
        self.assertEqual(by_id["script"].source, "answer = 40 + 2")

    def test_sem_binary_round_trip_matches_logical_document(self) -> None:
        source = self.make_document()
        encoded = dumps_sem(source)
        loaded = loads_sem(encoded)
        self.assertEqual(document_to_data(loaded), document_to_data(source))

    def test_unknown_custom_class_is_preserved(self) -> None:
        data = {
            "format": "somnia-model",
            "version": 1,
            "name": "PluginModel",
            "root_ids": ["custom"],
            "objects": [
                {
                    "id": "custom",
                    "type": "missing.plugin.SpecialNode",
                    "name": "Special",
                    "parent": None,
                    "properties": {
                        "enabled": True,
                        "archivable": True,
                        "plugin_value": {"nested": [1, 2, 3]},
                    },
                    "tags": ["Imported"],
                    "extensions": {"plugin": "missing.plugin"},
                }
            ],
            "metadata": {},
        }
        document = data_to_document(data)
        unknown = document.roots[0]
        self.assertEqual(unknown.type_name, "missing.plugin.SpecialNode")
        self.assertEqual(unknown.raw_properties["plugin_value"], {"nested": [1, 2, 3]})
        encoded_again = document_to_data(document)
        self.assertEqual(encoded_again["objects"][0]["type"], "missing.plugin.SpecialNode")
        self.assertEqual(
            encoded_again["objects"][0]["properties"]["plugin_value"],
            {"nested": [1, 2, 3]},
        )


if __name__ == "__main__":
    unittest.main()
