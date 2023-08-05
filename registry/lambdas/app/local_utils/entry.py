"""
Utility methods for tests that may use the local file system.
"""
import json

from ..model.dataset import DataSet
from ..core.exceptions import IngesterException


def get_entry_from_fs(filename: str) -> DataSet:
    """
    Load the entry.json file from the local file system, returning a Dataset instance.
    :param filename: fully qualified path to entry.json
    :return: a DataSet instance created from the contents of entry.json
    """

    # Check file extension
    if not filename.endswith("json"):
        raise IngesterException(
            "Upload entry file " + filename + " does not have a JSON extension."
        )

    with open(filename, encoding="UTF-8") as entry_f:
        data = json.load(entry_f)

    # Correction for id field used in the JSON form
    data["dataset_id"] = data["id"]
    return DataSet.from_serialized_dict(data)
