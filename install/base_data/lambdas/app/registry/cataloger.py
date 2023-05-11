# Contains implementations of Bucket Catalog generation per the specification at
# https://git.smce.nasa.gov/heliocloud/heliocloud-services/-/blob/develop/install/base_data/documentation/CloudMe-data-access-spec-0.1.1.md#5-info

import boto3


class Cataloger(object):
    """
    Generates the catalog JSON file stored at the root of each public S3 bucket in the registry.
    This catalog contains metadata about each registered dataset and its files stored in the bucket.
    """

    def __init__(self, s3client: boto3.client = None, dbhandle=None) -> None:
        """
        TODO:  Still implementing...
        """
        self.s3client = s3client
        self.dbhandle = dbhandle

        # Possible status codes for the availability of a particular data set
        self.__status_codes = {
            "OK": "1200/OK",
            "Unavailable": "1400/temporarily unavailable",
            "User Pays": "1600/user pays"
        }

        # A publicly accessible S3 bucket designated for storing HelioCloud data
        self.__endpoint = "s3://helio.....blah"
        self.__name = "APL HelioCloud"  # Descriptive name for the data set
        self.__status = "1200/OK"  # Toggleable by owners to disable access
        self.__contact = "Dr. Contact, dr_contact@example.com"  # Example contact information
        self.__description = "Human readable description for this bucket"
        self.__citation = "Optional how to cite, preferably a DOI for the server"
        self.__catalog = list()

    def write_catalog(self):
        """
        Stub method for outputting the catalog
        """
        example_json = {
            "Cloudy": "0.1",
            "endpoint": "s3://gov-nasa-helio-public/MMS/",
            "name": "GSFC HelioCloud",
            "contact": "Dr. Contact, dr_contact@example.com",
            "description": "Optional description of this collection",
            "citation": "Optional how to cite, preferably a DOI for the server",
            "registry": [
                {
                    "id": "mms1_feeps_brst_electron",
                    "loc": "s3://helio-public/MMS/mms1/feeps/brst/l2/electron/",
                    "title": "mms1/feeps/brst/l2/electron/",
                    "startdate": "2015-06-01T00:00Z",
                    "enddate": "2021-12-31T23:59Z",
                    "modificationdate": "2023-03-08T00:00Z",
                    "indexformat": "csv",
                    "fileformat": "cdf",
                    "ownership": {
                        "description": "Optional description for dataset",
                        "resourceID": "optional identifier e.g. SPASE ID",
                        "creationDate": "optional ISO 8601 date/time of the dataset creation",
                        "citation": "optional how to cite this dataset, DOI or similar",
                        "contact": "optional contact info, SPASE ID, email, or ORCID",
                        "aboutURL": "optional website URL for info, team, etc"
                    }
                }
            ]
        }

    def execute(self):
        """
        Generate and store the Catalog JSON files in the registry S3 buckets.
        """
        self.write_catalog()
        print("Not implemented yet")
