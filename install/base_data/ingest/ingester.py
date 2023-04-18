# Use data in  s3://test-cdaweb/mms/mms1/fgm/brst/l2
# 8 years with 3-6 months per year of data and 100-1000 files per month.  Long baseline yet relatively small data set.
# Stick to the CSV RFC: https://www.ietf.org/rfc/rfc4180.txt


# Product an index file named :  "id_YYYY.csv."  This goes in the root of the data set directory
# Data set directory could break down further?


# Manifest file will be in CSV format
#

import json
import os.path
import shutil
import boto3

import pandas as pd
import os.path as osp
from enum import Enum

import base_data.model.dataset as dataset
from base_data.model.dataset import DataSet
from base_data.ingest.exceptions import IngesterException
from base_data.model.registered_file import RegisteredFile
from base_data.registry.repositories import DataSetRepository, RegisteredFileRepository


def get_entry_json_from_s3(client, s3key: str):
    """

    """
    raise NotImplemented()


def get_entry_dataset_from_fs(filename: str) -> DataSet:
    """
    Load the entry.json file from the local file system, returning a DataSet instance.
    """
    # Check file extension
    if not filename.endswith("json"):
        raise IngesterException("Upload entry file " + filename + " does not have a JSON extension.")

    data = dict()
    with open(filename) as entry_f:
        data = json.load(entry_f)
    return dataset.dataset_from_dict(data)


class UploadType(Enum):
    """
    Help toggle the Ingester between file system & s3 based uploads
    """
    LOCAL = "LOCAL",
    S3 = "S3"


class FileStatus(Enum):
    """
    Help describe the status of a file during validation of the manifest.
    """
    NOT_FOUND = "NOT_FOUND"
    WRONG_SIZE = "WRONG_SIZE"
    VALID = "VALID"


# Generates a Registry per the following specification
class Ingester(object):
    """
    Class for ingesting file uploads.
    """
    registered_file_repo: RegisteredFileRepository
    dataset_repo: DataSetRepository

    def __init__(self, upload_path: str, manifest_df: pd.DataFrame, entry_dataset: DataSet,
                 dataset_repository: DataSetRepository, registered_files_repository: RegisteredFileRepository) -> None:

        # Hold the manifest
        self.__manifest_df = manifest_df

        # Hold the data set to enter these files into
        self.__dataset = entry_dataset

        # Hold repository references
        self.dataset_repo = dataset_repository
        self.registered_file_repo = registered_files_repository

        # Figure out if we are dealing with a local upload or not
        upload_path = str(upload_path)
        if upload_path.startswith("file://"):
            self.__type = UploadType.LOCAL
        elif upload_path.startswith("s3://"):
            self.__type = UploadType.S3
        else:
            raise IngesterException("Upload path " + upload_path +
                                    " does not contain either a file:// or s3:// prefix.")
        self.__upload_path = upload_path

        # Future list of file registry entries
        self.__file_registry_entries = list()

    def __validate_manifest(self):
        """
        Validate each entry in the manifest data frame, confirming that:
        (a) the listed file is present and accessible
        (b) the file is of the expected size

        We validate the WHOLE manifest at this point, so we can deliver a comprehensive analysis
        back to the invoking process (presumably making its way back to a user).
        """

        # Iterate through the manifest entries, checking the files
        def check_file(row):
            record = {
                'status': None,
                'filename': None,
            }

            # Simple checks if dealing with local file system
            if self.__type == UploadType.LOCAL:
                filename = self.__upload_path.strip("file://") + "/" + row.s3key
                record['filename'] = filename
                if not osp.isfile(filename):
                    record['status'] = FileStatus.NOT_FOUND.name
                elif row.filesize != osp.getsize(filename):
                    record['status'] = FileStatus.WRONG_SIZE.name
                else:
                    record['status'] = FileStatus.VALID.name
            else:
                # s3 handling
                raise (NotImplemented("Yeah"))

            return record

        results = self.__manifest_df.apply(check_file, axis=1, result_type='expand')

        # If the count of records that are VALID is less than the total records, we've got invalid entries
        # and can't load
        valid = results[results['status'] == FileStatus.VALID.name]
        if valid['status'].count() < results['status'].count():
            # TODO: Need to store & propagate the records back
            vc = valid['status'].count()
            rc = results['status'].count()
            raise IngesterException("Error validating manifest entries. Only " + str(vc)
                                    + " records were valid out of " + str(rc) + " files checked")

    def __validate_entry_information(self) -> None:
        """
        Check that the entry JSON file provided as part of this upload contains a valid target location.
        """
        # Check that the file system path is in place
        if self.__type == UploadType.LOCAL:
            dataset_bucket = str(self.__dataset.loc).replace("file://", "")
            if not os.path.isdir(dataset_bucket):
                raise IngesterException("Cannot find data set bucket " + dataset_bucket + " for ingester to register "
                                                                                          "data into. ")

    def __register_dataset(self):
        """
        Time to register the data.
        """

        # First, copy the files to the destination location
        registered_files = []
        if self.__type == UploadType.LOCAL:
            for (start_date, manifest_file, checksum) in self.__manifest_df.to_records(index=False):
                # Get the origin directory
                origin_dir = self.__upload_path.replace("file://", "")
                origin_dir = origin_dir + "/" + "/".join(manifest_file.split("/")[0:-1])

                # Get the target directory
                target_dir = "/".join(manifest_file.split("/")[0:-1])
                target_dir = self.__dataset.loc.replace("file://", "") + "/" + target_dir

                # Get the file name
                file_name = manifest_file.split("/")[-1]

                # Make sure the target directory exists & copy the file in
                os.makedirs(target_dir, exist_ok=True)
                origin_file = origin_dir + "/" + file_name
                target_file = target_dir + "/" + file_name

                shutil.copy(origin_file, target_file)

                # Store a record for the registered file
                registered_files.append(
                    RegisteredFile(dataset_id=self.__dataset.entry_id, key=target_file, start_date=start_date,
                                   file_size=checksum)
                )

        # Now update the CatalogEntry that will be made
        # Start date & end date come from the min & max of the manifest
        start_date = self.__manifest_df['time'].min()
        end_date = self.__manifest_df['time'].max()
        self.__dataset.start_date = start_date
        self.__dataset.end_date = end_date

        # Get the file formats
        def get_extension(filename: str):
            return filename.split(".")[-1]

        extensions = self.__manifest_df['s3key'].apply(get_extension).unique()

        # TODO: Do an earlier check on the extensions.  Why copy the files over if the extension type is not supported?
        self.__dataset.file_format = list(extensions)

        # Save the DataSet and RegisteredFile lists to their repositories
        self.dataset_repo.save(self.__dataset)
        self.registered_file_repo.save(registered_files)

    def execute(self):
        # Validate that each file listed in the manifest is present in the upload path
        self.__validate_manifest()

        # Check that the entry instructions are valid (namely that the destination S3 bucket exists)
        self.__validate_entry_information()

        # Register this upload job as a data set (copying files, updating the registry, etc)
        self.__register_dataset()

        # Clean up the upload directory
        # self.__clean_up()
