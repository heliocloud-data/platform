# Generates a Global registration file for this HelioCloud instance per the following specification:
# https://git.smce.nasa.gov/heliocloud/heliocloud-services/-/blob/develop/install/base_data/documentation/CloudMe-data-access-spec-0.1.1.md#5-info


class Registrar(object):
    """
    Implements support for the global registration of HelioCloud instances
    """

    def __init__(self, config) -> None:
        pass

    def global_update(self) -> None:
        """
        Updates the global registry of HelioCloud instances with information about this instance.
        """
        example_registry = {
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
        raise
        }
