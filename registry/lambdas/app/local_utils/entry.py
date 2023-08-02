import json

from ..model.dataset import DataSet
from ..exceptions import IngesterException


def get_entry_from_fs(filename: str) -> DataSet:
    """
    Load the entry.json file from the local file system, returning a DataSet instance.
    """
    # Check file extension
    if not filename.endswith("json"):
        raise IngesterException(
            "Upload entry file " + filename + " does not have a JSON extension."
        )

    data = dict()
    with open(filename) as entry_f:
        data = json.load(entry_f)

    # Correction for id field used in the JSON form
    data["dataset_id"] = data["id"]
    return DataSet.from_serialized_dict(data)
