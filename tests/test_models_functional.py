"Functional tests showing how models can be used to create/edit datasets."

import os

import dtoolcore.utils

from . import tmp_dir_fixture  # NOQA

import pytest


def test_create_dataset(tmp_dir_fixture):  # NOQA

    import models

    input_directory = os.path.join(tmp_dir_fixture, "input_directory")
    os.mkdir(input_directory)
    item_content = "my data in a file"
    with open(os.path.join(input_directory, "data.txt"), "w") as fh:
        fh.write(item_content)

    base_uri_directory = os.path.join(tmp_dir_fixture, "datasets")
    os.mkdir(base_uri_directory)
    config_path = os.path.join(tmp_dir_fixture, "dtool-gui.json")
    base_uri_model = models.LocalBaseURIModel(config_path)
    base_uri_model.put_base_uri(base_uri_directory)

    proto_dataset_model = models.ProtoDataSetModel()

    metadata_model = models.MetadataModel()
    metadata_model.add_metadata_property(
        name="project",
        schema={"type": "string", "maxLength": 10},
        required=True
    )
    metadata_model.add_metadata_property(
        name="age",
        schema={"type": "integer", "maximum": 10},
        required=False
    )

    with pytest.raises(models.MissingDataSetNameError):
        proto_dataset_model.create()

    proto_dataset_model.set_name("my-dataset")

    with pytest.raises(models.MissingInputDirectoryError):
        proto_dataset_model.create()

    proto_dataset_model.set_input_directory(input_directory)

    with pytest.raises(models.MissingBaseURIModelError):
        proto_dataset_model.create()

    proto_dataset_model.set_base_uri_model(base_uri_model)

    with pytest.raises(models.MissingMetadataModelError):
        proto_dataset_model.create()

    proto_dataset_model.set_metadata_model(metadata_model)

    with pytest.raises(models.MissingRequiredMetadataError):
        proto_dataset_model.create()

    proto_dataset_model.metadata_model.set_value("project", "dtool-gui")  # NOQA
    proto_dataset_model.metadata_model.set_value("age", "not-an-integer")  # NOQA
    proto_dataset_model.metadata_model.select_optional_item("age")

    # Raises because "age" is not an integer.
    with pytest.raises(models.MetadataValidationError):
        proto_dataset_model.create()

    proto_dataset_model.metadata_model.set_value("project", "too-long-project-name")  # NOQA
    proto_dataset_model.metadata_model.set_value("age", 5)  # NOQA

    # Raises because "project" name is too long"
    with pytest.raises(models.MetadataValidationError):
        proto_dataset_model.create()

    proto_dataset_model.metadata_model.set_value("project", "dtool-gui")

    proto_dataset_model.create()

    expected_uri = dtoolcore.utils.sanitise_uri(
        os.path.join(base_uri_directory, "my-dataset")
    )
    assert proto_dataset_model.uri == expected_uri

    ds = dtoolcore.DataSet.from_uri(expected_uri)
    assert ds.get_annotation("project") == "dtool-gui"
    assert ds.get_annotation("age") == 5

    expected_readme = """---
project: dtool-gui
age: 5"""
    assert ds.get_readme_content() == expected_readme

    assert len(ds.identifiers) == 1
    identifier = list(ds.identifiers)[0]
    with open(ds.item_content_abspath(identifier)) as fh:
        assert item_content == fh.read()