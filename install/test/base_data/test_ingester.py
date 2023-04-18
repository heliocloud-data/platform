import os
import shutil
import unittest
import boto3

from base_data.ingest.manifest import get_manifest_from_fs

from base_data.ingest.exceptions import IngesterException
from base_data.ingest.ingester import Ingester, get_entry_dataset_from_fs
from base_data.model.registered_file import RegisteredFile
from base_data.model.dataset import DataSet

from base_data.registry.repositories import DataSetRepository, RegisteredFileRepository


class TestIngester(unittest.TestCase):
    upload_path = "file://test/base_data/resources/ingest/upload_bucket"
    data_set_registry_path = "file://test/base_data/resources/ingest/dataset_bucket"
    manifest_file = "test/base_data/resources/ingest/upload_bucket/manifest.csv"
    entry_file = "entry.json"

    @classmethod
    def setUpClass(cls) -> None:
        # Create data set registry bucket
        os.makedirs(TestIngester.data_set_registry_path.replace("file://", ""), exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(TestIngester.data_set_registry_path.replace("file://", ""))

    def setUp(self) -> None:
        """
        Instantiate Mock repository implementations to inject in the Ingester instances to enable them to
        complete execution in each test.
        """

        class MockRFRepository(RegisteredFileRepository):
            def save(self, files: list[RegisteredFile]) -> None:
                return None

        self.rf_repo = MockRFRepository(None)

        class MockDSRepository(DataSetRepository):
            def save(self, dataset: DataSet) -> None:
                return None

        self.ds_repo = MockDSRepository(None)

    def test_manifest_incorrect(self):
        manifest_file = 'test/base_data/resources/ingest/manifest/bad_files.csv'
        manifest_df = get_manifest_from_fs(manifest_file)
        with self.assertRaises(IngesterException) as raised:
            ingester = Ingester(upload_path=TestIngester.upload_path, manifest_df=manifest_df,
                                entry_dataset=TestIngester.entry_file, registered_files_repository=self.rf_repo,
                                dataset_repository=self.ds_repo)
            ingester.execute()

    def test_upload_entry_not_json(self):
        filename = 'test/base_data/resources/ingest/entry/entry.txt'
        with self.assertRaises(IngesterException) as raised:
            entry = get_entry_dataset_from_fs(filename=filename)

    @unittest.skip
    def test_upload_entry_invalid_loc(self):
        filename = 'test/base_data/resources/ingest/entry/invalid_loc.json'
        manifest_df = get_manifest_from_fs(TestIngester.manifest_file)
        entry_ds = get_entry_dataset_from_fs(filename)
        with self.assertRaises(IngesterException) as raised:
            ingester = Ingester(TestIngester.upload_path, manifest_df=manifest_df,
                                entry_dataset=entry_ds, registered_files_repository=self.rf_repo,
                                dataset_repository=self.ds_repo)
            ingester.execute()

    def test_upload_entry_valid(self):
        filename = 'test/base_data/resources/ingest/entry/entry.json'
        dataset = get_entry_dataset_from_fs(filename=filename)
        self.assertEqual(dataset.entry_id, 'MMS')
        self.assertEqual(dataset.ownership.about_url, 'https://www.nasa.gov')


    def test_file_copy(self):
        manifest_df = get_manifest_from_fs(TestIngester.manifest_file)
        ingester = Ingester(TestIngester.upload_path, manifest_df=manifest_df,
                            entry_dataset=TestIngester.entry_file,
                            registered_files_repository=self.rf_repo, dataset_repository=self.ds_repo)
        ingester.execute()
        copied_file = TestIngester.data_set_registry_path.replace("file://", "")
        copied_file += "/MMS/mms1/fgm/brst/l2/2015/09/01/mms1_fgm_brst_l2_20150901121114_v4.18.0.cdf"
        self.assertTrue(os.path.isfile(
            copied_file
        ))


if __name__ == '__main__':
    unittest.main(verbosity=2)
