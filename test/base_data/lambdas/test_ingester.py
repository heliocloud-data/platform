import os
import shutil
import unittest
import unittest.mock as mock

import boto3

#from registry.ingest.entry import get_entry_from_fs, get_entry_from_s3
#from registry.ingest.exceptions import IngesterException
#from registry.ingest.ingester import Ingester, get_bucket_name, get_bucket_subfolder
#from registry.ingest.manifest import get_manifest_from_fs, get_manifest_from_s3
#from registry.registry.repositories import DataSetRepository

from registry.lambdas.app.ingest.entry import get_entry_from_fs, get_entry_from_s3
from registry.lambdas.app.ingest.exceptions import IngesterException
from registry.lambdas.app.ingest.ingester import Ingester
from registry.lambdas.app.ingest.manifest import get_manifest_from_fs, get_manifest_from_s3
from registry.lambdas.app.ingest.utils import get_bucket_name, get_bucket_subfolder
from registry.lambdas.app.registry.repositories import DataSetRepository


class TestIngester(unittest.TestCase):
    # local dir that serves as the base_dir for testing
    testing_dir = 'test/registry/resources/ingest/'
    dataset_bucket = "file://test-heliocloud-datasets/"
    upload_bucket = "file://test-heliocloud-uploads/"

    # metadata required by upload
    entry_file = testing_dir + upload_bucket.replace("file://", "") + "entry.json"
    manifest_file = testing_dir + upload_bucket.replace("file://", "") + "manifest.csv"

    @classmethod
    def setUpClass(cls) -> None:
        # Create data set registry bucket
        os.makedirs(TestIngester.testing_dir + TestIngester.dataset_bucket.replace("file://", ""), exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        clean_up_dir = TestIngester.testing_dir + get_bucket_name(TestIngester.dataset_bucket)
        shutil.rmtree(clean_up_dir)

    def setUp(self) -> None:
        """
        Instantiate Mock repository implementations to inject in the Ingester instances to enable them to
        complete execution in each test.
        """
        self.ds_repo = DataSetRepository(None)
        self.ds_repo.save = mock.MagicMock(return_value=None)

    def test_get_bucket_name(self):
        bucket = get_bucket_name(TestIngester.dataset_bucket)
        self.assertEqual(bucket, "test-heliocloud-datasets")

    def test_get_bucket_subfolder(self):
        entry = get_entry_from_fs(TestIngester.entry_file)
        sub_folder = get_bucket_subfolder(entry.loc)
        self.assertEqual(sub_folder, 'MMS/')

    def test_invalid_dest_bucket(self):
        filename = 'test/registry/resources/ingest/entry/invalid_loc.json'
        entry_ds = get_entry_from_fs(filename)
        manifest_df = get_manifest_from_fs(TestIngester.manifest_file)
        with self.assertRaises(IngesterException) as raised:
            ingester = Ingester(TestIngester.upload_bucket, manifest_df=manifest_df,
                                entry_dataset=entry_ds, dataset_repository=self.ds_repo, local_dir=self.testing_dir)
            ingester.execute()

    def test_missing_file(self):
        manifest_file = 'test/registry/resources/ingest/manifest/missing_file.csv'
        manifest_df = get_manifest_from_fs(manifest_file)
        entry_ds = get_entry_from_fs(TestIngester.entry_file)
        with self.assertRaises(IngesterException) as raised:
            ingester = Ingester(upload_path=TestIngester.upload_bucket, manifest_df=manifest_df,
                                entry_dataset=entry_ds, dataset_repository=self.ds_repo, local_dir=self.testing_dir)
            ingester.execute()

    def test_ingester_local(self):
        entry_ds = get_entry_from_fs(TestIngester.entry_file)
        manifest_df = get_manifest_from_fs(TestIngester.manifest_file)
        ingester = Ingester(TestIngester.upload_bucket, manifest_df=manifest_df,
                            entry_dataset=entry_ds, dataset_repository=self.ds_repo, local_dir=self.testing_dir)
        ingester.execute()

        # Confirm an expected file is in the data set bucket
        copied_file = TestIngester.testing_dir + get_bucket_name(entry_ds.loc) + "/" + get_bucket_subfolder(
            entry_ds.loc)
        copied_file += "mms1/fgm/brst/l2/2015/09/01/mms1_fgm_brst_l2_20150901121114_v4.18.0.cdf"
        self.assertTrue(os.path.isfile(
            copied_file
        ))

        # Confirm an index file is present
        index_file = TestIngester.testing_dir + get_bucket_name(entry_ds.loc) + "/" + get_bucket_subfolder(entry_ds.loc)
        index_file += "MMS_2015.csv"
        self.assertTrue(os.path.isfile(index_file))

        # Check that the catalog was updated
        self.ds_repo.save.assert_called_once()

    @unittest.skip
    def test_ingester_s3(self):
        s3_upload_path = "s3://heliocloud-dev-resources/ingest/upload_testing/mms_201509_upload/"

        # First, check we resolve bucket name & sub folder correctly
        bucket_name = get_bucket_name(s3_upload_path)
        self.assertEqual(bucket_name, 'heliocloud-dev-resources')
        sub_folder = get_bucket_subfolder(s3_upload_path)
        self.assertEqual(sub_folder, "ingest/upload_testing/mms_201509_upload/")

        # now get the entry file
        s3client = boto3.client('s3')
        entry_ds = get_entry_from_s3(s3client=s3client, bucket_name=bucket_name, entry_key=sub_folder + "entry.json")
        self.assertEqual(entry_ds.entry_id, "MMS")

        # Check the manifest
        manifest_df = get_manifest_from_s3(s3client=s3client, bucket_name=bucket_name, manifest_key=sub_folder + "manifest.csv")
        num_rows = manifest_df.shape[0]
        self.assertEqual(num_rows, 704)

        # Create an ingester instance
        ingester = Ingester(upload_path=s3_upload_path, entry_dataset=entry_ds, manifest_df=manifest_df,
                            dataset_repository=self.ds_repo, s3client=s3client)
        ingester.execute()

        s3client.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
