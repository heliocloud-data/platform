import unittest
from datetime import datetime


from base_data.lambdas.app.model.dataset import VALID_FILE_FORMATS
from base_data.lambdas.app.model.dataset import DataSet, Ownership, dataset_from_dict


class TestDataSet(unittest.TestCase):
    loc = "s3://public_bucket/data_set_dir/"

    def test_invalid_initialization(self):
        with self.assertRaises(TypeError) as raised:
            DataSet(entry_id=1)

    def test_invalid_loc(self):
        with self.assertRaises(ValueError) as raised:
            DataSet(entry_id="", loc="ftp://something", title="")

    def test_invalid_file_format(self):
        file_formats = VALID_FILE_FORMATS + ["pdf"]
        with self.assertRaises(ValueError) as raised:
            DataSet(entry_id="1234", loc=TestDataSet.loc, title="SomeTitle").file_format = file_formats

    def test_invalid_times(self):
        start_date = datetime(year=2015, month=9, day=1, hour=12, minute=11, second=14)
        end_date = datetime(year=2015, month=9, day=1, hour=10, minute=45, second=00)
        with self.assertRaises(ValueError) as raised:
            dataset = DataSet(entry_id="", loc=TestDataSet.loc, title="")
            dataset.start_date = start_date
            dataset.end_date = end_date

    def test_create_entry(self):
        # Basic entry creation
        dataset = DataSet(entry_id="1234", loc=TestDataSet.loc, title="TITLE")

        # Set dates
        dataset.start_date = datetime(year=2015, month=9, day=1, hour=10, minute=45, second=00)
        dataset.end_date = datetime(year=2015, month=9, day=1, hour=12, minute=11, second=14)

        # set ownership info
        creation_date = datetime(year=2015, month=9, day=1, hour=00, minute=00, second=1)
        ownership = Ownership(description="Some Description", resource_id="SPASE 123456",
                              creation_date=creation_date, citation="Cited by XYZ",
                              contact="chris.jeschke@jhuapl.edu", about_url="https://www.nasa.gov")
        dataset.ownership = ownership

        self.assertEqual(dataset.entry_id, "1234")
        self.assertEqual(dataset.loc, TestDataSet.loc)
        self.assertEqual(dataset.ownership.about_url, "https://www.nasa.gov")

    def test_from_dict(self):
        data = {
            'id': '1234',
            'loc': 's3://some.public.bucket',
            'title': 'A HelioPhysics Data Set',
            'ownership': {
                'description': 'MMS Data',
                'creation_date': datetime(year=2015, month=9, day=1, hour=00, minute=00, second=1),
                'about_url': 'https://www.jhuapl.edu'
            }
        }
        dataset = dataset_from_dict(data)
        self.assertEqual(dataset.entry_id, '1234')
        self.assertEqual(dataset.ownership.description, 'MMS Data')


if __name__ == '__main__':
    unittest.main()
