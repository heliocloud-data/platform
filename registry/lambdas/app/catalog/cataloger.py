# Contains implementations of Bucket Catalog generation per the specification at
# https://git.smce.nasa.gov/heliocloud/heliocloud-services/-/blob/develop/install/base_data/documentation/CloudMe-data-access-spec-0.1.1.md#5-info
import dataclasses

import boto3
import json
from collections import OrderedDict
from dataclasses import dataclass, field

from registry.lambdas.app.repositories import DataSetRepository
from registry.lambdas.app.aws_utils.s3 import get_s3_bucket_name
from registry.lambdas.app.model.dataset import DataSet


class Cataloger(object):
    """
    The Cataloger is used to generate catalog.json files placed at the root of the public s3 buckets that
    are part of a HelioCloud instance's Registry module. They are created by traversing a DataSetRepository
    instance for all DataSet entries, grouping them by public s3 bucket name, and composing individual
    catalog.json files for each bucket.

    Currently implements the CloudMe v.03 specification
    """

    @dataclass
    class Catalog(object):
        """
        Internal class to help with generating and validating the head fields of catalog.json file
        """
        Cloudy: str = field(default=0.3, init=False)  # Version
        endpoint: str  # An accessible S3 (or equivalent) bucket link
        name: str  # Descriptive name for the dataset
        region: str  # Which AWS region hosts it
        contact: str  # Whom to contact for issues with this bucket
        egress: str = "user-pays"  # One of 'no-egress', 'user-pays', 'egress-allowed', 'none'
        status: str = "1200/OK"  # A return code '1200/OK'. Sit owners can temporarily set this to other values
        description: str = None  # Optional description of this collection
        citation: str = None  # Optional how to cite, preferably a DOI for the server
        comment: str = None  # A catch-all comment field for data provider and developer use.
        catalog: list[DataSet] = field(default_factory=list)

        def __post_init__(self):
            if self.egress not in ('no-egress', 'user-pays', 'egress-allowed', 'none'):
                raise TypeError("egress must be one of: no-egress, user-pays, egress-allowed, none")

        def to_serializable_dict(self) -> OrderedDict:
            datasets_dicts = [dataset.to_serializable_dict() for dataset in self.catalog]
            catalog_dict = OrderedDict(dataclasses.asdict(self))
            catalog_dict['catalog'] = datasets_dicts
            return catalog_dict

    def __init__(self, session: boto3.session.Session, dataset_repository: DataSetRepository) -> None:
        """
        Initialize a new Cataloger instance.

        Parameters:
            session: a boto3.Session instance to use for accessing AWS services
            dataset_repository: an instance of DataSetRepository to execute against
        """
        self.__s3client = session.client('s3')
        self.__dataset_repository = dataset_repository

    def __cache_datasets_by_bucket(self):
        # Internal method to pull all the DataSet instances out of the repository and group them up
        # by s3 bucket name
        datasets = self.__dataset_repository.get_all()
        self.__bucket_dataset_cache = dict[str, list[DataSet]]()
        for dataset in datasets:
            bucket_name = get_s3_bucket_name(dataset.index)
            if bucket_name not in self.__bucket_dataset_cache:
                self.__bucket_dataset_cache[bucket_name] = [dataset]
            else:
                self.__bucket_dataset_cache[bucket_name].append(dataset)

    def __generate_bucket_catalog(self):
        # Generates a catalog.json for each s3 bucket
        for bucket in self.__bucket_dataset_cache.keys():
            catalog = self.Catalog(
                endpoint="s3://" + bucket,
                name="TBD-INJECTED",
                region=self.__s3client.get_bucket_location(Bucket=bucket)['LocationConstraint'],
                contact="Dr.YouKnowWho"
            )
            for dataset in self.__bucket_dataset_cache[bucket]:
                catalog.catalog.append(dataset)

            bucket_catalog_json = json.dumps(catalog.to_serializable_dict(), indent="\t")
            self.__s3client.put_object(Bucket=bucket,
                                       Body=bytes(bucket_catalog_json, 'utf-8'),
                                       Key="catalog.json")

    def execute(self):
        """
        Executes a Cataloger run, resulting in catalog.json files being placed in the root all
        AWS S3 buckets found in the DataSets contained in the DataSetRepository instance provided.
        """
        self.__cache_datasets_by_bucket()
        self.__generate_bucket_catalog()
        self.__s3client.close()
