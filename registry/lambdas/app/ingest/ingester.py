# Use data in  s3://test-cdaweb/mms/mms1/fgm/brst/l2
# 8 years with 3-6 months per year of data and 100-1000 files per month.  Long baseline yet relatively small data set.
# Stick to the CSV RFC: https://www.ietf.org/rfc/rfc4180.txt
import csv
import datetime
import shutil
import os

import boto3
import botocore.exceptions
import pandas as pd

import boto3
from boto3.session import Session

from enum import Enum
from ..exceptions import IngesterException
from registry.lambdas.app.repositories import DataSetRepository
from ..model.dataset import DataSet, FileType
from ..aws_utils.s3 import get_bucket_name, get_bucket_subfolder


class FileStatus(Enum):
    """
    Help describe the status of a file during validation of the manifest.
    """
    NOT_FOUND = "NOT_FOUND"
    WRONG_SIZE = "WRONG_SIZE"
    VALID = "VALID"


# TODO:  Review if the local testing mode is still required.  May simply be too divergent from using the

class Ingester(object):
    """
    An Ingester instance is used to ingest new or updated datasets into a HelioCloud's Registry,
    making them available in the Registry's public s3 buckets.

    Invoking an Ingester requires a dataset be uploaded to the HelioCloud instance's Ingest bucket (provisioned
    during installation). This dataset must be comprised of:
        - an entry.json file containing the details of the HelioCloud instance DataSet this data should be incorporated into
        - a manifest.csv file containing a list of all the files comprising the dataset, along with start times & sizes
        - the dataset files themselves
    """

    def __init__(self, ingest_bucket: str, ingest_folder: str, manifest_df: pd.DataFrame, entry_dataset: DataSet,
                 ds_repo: DataSetRepository, tmp_dir="/tmp", session: Session = boto3.session.Session()) -> None:
        """
        Initialize an Ingester instance

        Parameters:
            ingest_bucket_name
            upload_folder
            manifest_df
            entry_dataset
            ds_repo
            tmp_dir
            session
        """

        # Name of the S3 bucket the ingest operation will run against
        self.__ingest_bucket = ingest_bucket
        self.__ingest_folder = ingest_folder

        #
        self.__entry_dataset = entry_dataset
        # Destination on AWS s3 for the ingest
        self.__destination_bucket = get_bucket_name(self.__entry_dataset.index)

        # Sub folder in S3/Local file system into which the ingested data set will be copied
        self.__destination_folder = get_bucket_subfolder(self.__entry_dataset.index)
        if not self.__destination_folder.endswith("/"):
            self.__destination_folder += "/"

        # Hold manifest
        self.__manifest_df = manifest_df

        # Reference to dataset repository
        self.__ds_repo = ds_repo

        # AWS session
        self.__s3_client = session.client("s3")

        # Temp directory
        self.__tmp_dir = tmp_dir

        # File successfully installed by this Ingester
        self.__installed_files: pd.DataFrame = None

    def __validate_destination(self) -> None:
        """
        Check that the entry JSON file provided as part of this upload contains a valid target location.
        """
        # Check that the file system path is in place
        try:
            response = self.__s3_client.head_bucket(Bucket=self.__destination_bucket)
        except botocore.exceptions.ClientError as ce:
            raise IngesterException(ce)
        else:
            # Need a 200 status code to confirm the bucket is accessible.  Otherwise, return exception
            status_code = response['ResponseMetadata']['HTTPStatusCode']
            if status_code != 200:
                print('Got here??')
                raise IngesterException(f"S3 bucket {self.__destination_bucket} is not accessible. Received response :"
                                        f"{response}")

    def __validate_manifest(self) -> None:
        """
        Validate each entry in the manifest data frame, confirming that:
        (a) the listed file is present and accessible
        (b) the file is of the expected size

        We validate the WHOLE manifest at this point, so we can deliver a comprehensive analysis
        back to the invoking process (presumably making its way back to a user).
        """

        # Iterate through the manifest entries, checking that files exists and are the correct size
        def check_file(row):
            record = {
                'status': None,
                'filename': None,
            }

            # Check that the file exists and has the correct size
            s3key = self.__ingest_folder + row.s3key
            try:
                response = self.__s3_client.head_object(Bucket=self.__ingest_bucket, Key=s3key)
            except botocore.exceptions.ClientError as ce:
                # File wasn't found
                record['status'] = FileStatus.NOT_FOUND.name
                print(f"Manifest file s3://{self.__ingest_bucket}/{s3key} not found.")
            else:
                status_code = response['ResponseMetadata']['HTTPStatusCode']
                content_length = response['ContentLength']
                if row.filesize != content_length:
                    # File was the wrong size
                    record['status'] = FileStatus.WRONG_SIZE.name
                    print(f"Manifest file s3://{self.__ingest_bucket}/{s3key} wrong size.")
                else:
                    record['status'] = FileStatus.VALID.name
                    print(f"Manifest file s3://{self.__ingest_bucket}/{s3key} validated.")
            # results of check
            return record

        # Check all the files in the manifest
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

    def __install_dataset(self):
        """
        Time to register the data.
        """

        installed_files = list[[str, str, int]]()
        for (start_date, uploaded_file, size) in self.__manifest_df.to_records(index=False):
            target_file = str()

            # copy the file over to the destination bucket in the correct sub folder
            copy_source = {
                'Bucket': self.__ingest_bucket,
                'Key': self.__ingest_folder + uploaded_file
            }
            destination_key = self.__destination_folder + uploaded_file

            def copy_callback(transferred):
                source_s3 = "s3://" + self.__ingest_bucket + "/" \
                            + self.__ingest_folder + uploaded_file
                dest_s3 = "s3://" + self.__destination_bucket + "/" + destination_key
                print(f"Copied {transferred} of {source_s3} to {dest_s3}.")

            self.__s3_client.copy(CopySource=copy_source, Bucket=self.__destination_bucket,
                                  Key=destination_key, Callback=copy_callback)

            # Final file name in the destination bucket
            target_file = "s3://" + self.__destination_bucket + "/" + destination_key

            # Store a record for the registered file
            installed_files.append([start_date, target_file, size])

        # Store a dataframe for the installed files
        self.installed_files_df = pd.DataFrame(installed_files, columns=['startDate', 'key', 'size'])

    def __install_index_files(self) -> None:
        """
        Generate one index file for each year of the data being ingested.
        - Index files are deposited in data set destination bucket location,
        per the entry.json provided.
        - Naming convention is <id>_YYYY.csv
        """

        # First we need to know the years of data involved
        def get_year(start_date: datetime.datetime):
            return start_date.year

        self.installed_files_df['year'] = self.installed_files_df['startDate'].apply(get_year)
        years = self.installed_files_df['year'].unique()

        # For each year, generate an index file stored in a temporary directory
        index_files = list[str]()
        for year in years:

            # Generate a temp file first
            index_file = self.__tmp_dir + "/" + self.__entry_dataset.dataset_id + "_" + str(year) + ".csv"
            tmp_index_file = index_file + ".tmp"
            year_df = self.installed_files_df[self.installed_files_df["year"] == year]
            year_df.to_csv(tmp_index_file, header=False, index=False, quoting=csv.QUOTE_ALL,
                           quotechar="'", columns=['startDate', 'key', 'size'])

            # We do this loop so we can prepend the header row without it being quoted, per the spec
            with open(tmp_index_file, mode='r') as t_file:
                with open(index_file, mode='x') as i_file:
                    i_file.write("# startDate, key, size\n")
                    for line in t_file:
                        i_file.write(line)
            os.remove(tmp_index_file)
            index_files.append(index_file)

        # Upload the index files to the destination bucket and subfolder
        for index_file in index_files:
            key = self.__destination_folder + index_file[index_file.rindex("/") + 1:]
            data = open(index_file, mode='rb')
            self.__s3_client.put_object(
                Bucket=self.__destination_bucket,
                Key=key,
                Body=data
            )
            print(f"Uploading {index_file} to bucket: {self.__destination_bucket} at key: {key}.")
            data.close()
            os.remove(index_file)

    def __update_catalog(self):
        """
        Update the catalog database
        """
        # Now update the CatalogEntry that will be made
        # Start date & end date come from the min & max of the manifest
        start_date = self.__manifest_df['time'].min()

        # Note:  End date is the min "start time" of the data provided.  Not really the end date....
        end_date = self.__manifest_df['time'].max()
        self.__entry_dataset.start = start_date
        self.__entry_dataset.stop = end_date

        # Get the file formats
        def get_extension(filename: str):
            return filename.split(".")[-1].lower()

        extensions = self.__manifest_df['s3key'].apply(get_extension).unique()

        # TODO: Do an earlier check on the extensions.  Why copy the files over if the extension type is not supported?
        self.__entry_dataset.filetype = [FileType(extension) for extension in extensions]

        # Save the DataSet and RegisteredFile lists to their repositories
        self.__ds_repo.save([self.__entry_dataset])

    def __clean_up(self) -> None:
        """
        Clean up the upload directory.
        """

        # Delete data files
        def delete_file(row):
            key = self.__ingest_folder + row.s3key
            print(f"Deleting key {key}")
            response = self.__s3_client.delete_object(Bucket=self.__ingest_bucket, Key=key)

        self.__manifest_df.apply(delete_file, axis=1)

        # clean up
        self.__s3_client.close()

    def execute(self):
        # Check that the entry instructions are valid (namely that the destination S3 bucket exists)
        self.__validate_destination()

        # Validate that each file listed in the manifest is present in the upload path
        self.__validate_manifest()

        # Register this upload job as a data set (copying files, updating the registry, etc)
        self.__install_dataset()

        # Generate & install the index files
        self.__install_index_files()

        # Update the catalog DB
        self.__update_catalog()

        # Clean up the upload directory
        self.__clean_up()
