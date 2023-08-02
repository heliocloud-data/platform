import datetime
import unittest

from registry.lambdas.app.local_utils.entry import get_entry_from_fs
from registry.lambdas.app.exceptions import IngesterException


class TestEntry(unittest.TestCase):
    def test_upload_entry_not_json(self):
        filename = "test/registry/resources/ingest/entry/not_json.txt"
        with self.assertRaises(IngesterException) as raised:
            entry = get_entry_from_fs(filename=filename)

    def test_upload_entry_valid(self):
        filename = "test/unit/registry/resources/ingest/entry/valid.json"
        dataset = get_entry_from_fs(filename=filename)
        self.assertEqual(dataset.dataset_id, "MMS")
        self.assertEqual(
            dataset.creation,
            datetime.datetime(year=2015, month=9, day=1, hour=0, minute=0, second=0),
        )
        self.assertEqual(dataset.resource, "SPASE-1234567")
