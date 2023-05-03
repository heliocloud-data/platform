# Contains implementations of Bucket Catalog & File Registry generation per the specification at
# https://git.smce.nasa.gov/heliocloud/heliocloud-services/-/blob/develop/install/base_data/documentation/CloudMe-data-access-spec-0.1.1.md#5-info

from base_data.model.dataset import VALID_FILE_FORMATS


# Generates a Global registration file for this HelioCloud instance per the following specification:
# https://git.smce.nasa.gov/heliocloud/heliocloud-services/-/blob/develop/install/base_data/documentation/CloudMe-data-access-spec-0.1.1.md#5-info


class GlobalRegistrar:

    def __init__(self, config) -> None:
        print("Initializing a registry")

        self.__example = {
            "CloudMe": "0.1",
            "modificationDate": "2022-01-01T00:00Z",
            "registry": [
                {
                    "endpoint": "s3://gov-nasa-hdrl-data1/",
                    "name": "GSFC HelioCloud Set 1",
                    "region": "us-east-1"
                },
                {
                    "endpoint": "s3://gov-nasa-hdrl-data2/",
                    "name": "GSFC HelioCloud Set 2",
                    "region": "us-east-1"
                },
                {
                    "endpoint": "s3://edu-apl-helio-public/",
                    "name": "APL HelioCLoud",
                    "region": "us-west-1"
                }
            ]

        }




class Catalog(object):

    def __init__(self) -> None:
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

        # For Each data set we need something like:


# Example JSON
# {
#    "Cloudy": "0.1",
#    "endpoint": "s3://gov-nasa-helio-public/MMS/",
#    "name": "GSFC HelioCloud",
#    "contact": "Dr. Contact, dr_contact@example.com",
#    "description": "Optional description of this collection",
#    "citation": "Optional how to cite, preferably a DOI for the server",
#    "registry": [
#        {
#	    "id": "mms1_feeps_brst_electron",
#	    "loc": "s3://helio-public/MMS/mms1/feeps/brst/l2/electron/",
#	    "title": "mms1/feeps/brst/l2/electron/",
#	    "startdate": "2015-06-01T00:00Z",
#	    "enddate": "2021-12-31T23:59Z",
#	    "modificationdate": "2023-03-08T00:00Z",
#	    "indexformat": "csv",
#	    "fileformat": "cdf",
#           "ownership": {
#                "description": "Optional description for dataset",
#                "resourceID": "optional identifier e.g. SPASE ID",
#                "creationDate": "optional ISO 8601 date/time of the dataset creation",
#                "citation": "optional how to cite this dataset, DOI or similar",
#                "contact": "optional contact info, SPASE ID, email, or ORCID",
#                "aboutURL": "optional website URL for info, team, etc"
#            }
#	},


class FileRegistry(object):
    """
    Compiles a File Registry file for placement in an S3 Bucket's data set directory to
    enumerate the files that have been registered

    # Review section 4:
    # https://git.smce.nasa.gov/heliocloud/heliocloud-services/-/blob/develop/install/base_data/documentation/CloudMe-data-access-spec-0.1.1.md#5-info

    """

    def __init__(self, set_id, year, registry_type="CSV") -> None:
        # Header line for CSV/CSV.ZIP files (not necessary for parquet)
        self.__header = ""

        # Example #1

        # Will contain

        # Name follows the format "id"_YYYY.<extension>
        self.__name = set_id + "_" + year + "." + registry_type

        # string, restricted ISO 8601 date/time for the start of the data
        self.__start_date = "1995-01-01T00:00Z"

        # OPTIONAL fields
        # string, restricted ISO 8601 date/time for the end of the data
        self.__end_date = "2022-01-01T00:00Z"
        self.__startdate = "1995-01-01T00:00Z"  # String, restricted ISO 8601 date/time of the first record of data
        # in the entire data set
        self.__enddate = "2022-01-01T00:00Z"
