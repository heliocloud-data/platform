# Use data in  s3://test-cdaweb/mms/mms1/fgm/brst/l2
# 8 years with 3-6 months per year of data and 100-1000 files per month.  Long baseline yet relatively small data set.
# Stick to the CSV RFC: https://www.ietf.org/rfc/rfc4180.txt
import csv
import datetime
# Product an index file named :  "id_YYYY.csv."  This goes in the root of the data set directory
# Data set directory could break down further?


# Manifest file will be in CSV format
#
import shutil
import os
import pandas as pd
import boto3

from enum import Enum

from .utils import get_bucket_name, get_bucket_subfolder
from .exceptions import IngesterException
from ..registry.repositories import DataSetRepository
from ..model.dataset import DataSet


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

    # Bucket paths on S3 (or local fs)
    upload_path: str
    destination_bucket: str
    destination_subfolder: str

    # Holds the manifest for this ingest job
    manifest_df: pd.DataFrame

    # Metadata for the dataset this upload will be added to
    dataset: DataSet

    # References to the repositories needed by this ingester to save state
    dataset_repo: DataSetRepository

    # List of files successfully installed by this ingester
    installed_files_df: pd.DataFrame

    # Temporary directory (needed for index file generation)
    tmp_dir: str

    # Operating mode for the ingester
    mode: UploadType

    # Required if mode=UploadType.LOCAL
    local_dir: str

    # Required if mode=UploadType.S3
    s3client: boto3.client

    def __init__(self, upload_path: str, manifest_df: pd.DataFrame, entry_dataset: DataSet,
                 dataset_repository: DataSetRepository, tmp_dir: str = "/tmp",
                 local_dir: str = None, s3client: boto3.client = None) -> None:

        # Initialization for an Ingester running against S3
        if upload_path.startswith("s3://"):
            # We are doing an ingest operation in S3
            self.mode = UploadType.S3
            self.upload_path = upload_path
            self.destination_bucket = get_bucket_name(entry_dataset.loc)
            self.destination_subfolder = get_bucket_subfolder(entry_dataset.loc)
            if s3client is None:
                raise IngesterException("Ingester instances working against AWS S3 require the s3client parameter "
                                        "be provided on initialization.")
            self.s3client = s3client

        # Initialization for an Ingester running against the local file system (used for testing)
        elif upload_path.startswith("file://"):
            # TODO: Add check that local dir is provided and ends with "/"
            # Local file system mode (for testing purposes)
            self.mode = UploadType.LOCAL
            self.upload_path = local_dir + upload_path.replace("file://", "")
            self.destination_bucket = local_dir + get_bucket_name(entry_dataset.loc)
            self.destination_subfolder = get_bucket_subfolder(entry_dataset.loc)
            if local_dir is None:
                raise IngesterException(f"Parameter local_dir cannot be NoneType if upload path is local. Upload "
                                        f"path is : {upload_path}.")
            self.local_dir = local_dir
        else:
            raise IngesterException(f"Upload bucket {upload_path} is not local file system (file://) or s3 (s3://).")

        # Creating consistent pathing
        if not self.upload_path.endswith("/"):
            self.upload_path += "/"
        if self.destination_subfolder.startswith("/"):
            self.destination_subfolder = self.destination_subfolder[1:]
        if not self.destination_subfolder.endswith("/"):
            self.destination_subfolder += "/"

        # Hold the manifest
        self.manifest_df = manifest_df

        # Hold the data set to enter these files into
        self.dataset = entry_dataset

        # Hold repository references
        self.dataset_repo = dataset_repository

        # Temporary directory for index file generation
        self.tmp_dir = tmp_dir

    def __validate_destination(self) -> None:
        """
        Check that the entry JSON file provided as part of this upload contains a valid target location.
        """
        # Check that the file system path is in place
        if self.mode == UploadType.LOCAL:
            if not os.path.isdir(self.destination_bucket):
                raise IngesterException(f"Cannot find data set destination bucket {self.destination_subfolder}.")
        else:
            response = self.s3client.head_bucket(Bucket=self.destination_bucket)
            # HTTP Status Code of 200 in the response indicates the bucket exists and is accessible to this process
            status_code = response['ResponseMetadata']['HTTPStatusCode']
            if status_code != 200:
                raise IngesterException(f"S3 bucket {self.destination_bucket} is not accessible. Received response :"
                                        f"{response}")

    def __validate_manifest(self):
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
            if self.mode == UploadType.S3:
                # For S3 upload types
                bucket_name = get_bucket_name(self.upload_path)
                upload_folder = get_bucket_subfolder(self.upload_path)
                s3key = upload_folder + row.s3key

                print(f"Checking S3 bucket {bucket_name} for file {s3key}.")
                response = self.s3client.head_object(Bucket=bucket_name, Key=s3key)
                status_code = response['ResponseMetadata']['HTTPStatusCode']
                content_length = response['ContentLength']

                if status_code != 200:
                    # File wasn't found
                    record['status'] = FileStatus.NOT_FOUND.name
                elif row.filesize != content_length:
                    # File was the wrong size
                    record['status'] = FileStatus.WRONG_SIZE.name
                else:
                    record['status'] = FileStatus.VALID.name
            else:
                # Handling for local file system
                filename = self.upload_path + row.s3key
                record['filename'] = filename
                if not os.path.isfile(filename):
                    record['status'] = FileStatus.NOT_FOUND.name
                elif row.filesize != os.path.getsize(filename):
                    record['status'] = FileStatus.WRONG_SIZE.name
                else:
                    record['status'] = FileStatus.VALID.name

            return record

        results = self.manifest_df.apply(check_file, axis=1, result_type='expand')

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
        for (start_date, uploaded_file, size) in self.manifest_df.to_records(index=False):

            target_file = str()
            if self.mode == UploadType.S3:

                # copy the file over to the destination bucket in the correct sub folder
                copy_source = {
                    'Bucket': get_bucket_name(self.upload_path),
                    'Key': get_bucket_subfolder(self.upload_path) + uploaded_file
                }
                destination_key = self.destination_subfolder + uploaded_file

                def copy_callback(transferred):
                    source_s3 = "s3://" + get_bucket_name(self.upload_path) + "/" \
                                + get_bucket_subfolder(self.upload_path) + uploaded_file
                    dest_s3 = "s3://" + self.destination_bucket + "/" + destination_key
                    print(f"Copied {transferred} of {source_s3} to {dest_s3}.")

                response = self.s3client.copy(CopySource=copy_source, Bucket=self.destination_bucket,
                                              Key=destination_key, Callback=copy_callback)

                # Final file name in the destination bucket
                target_file = "s3://" + self.destination_bucket + "/" + destination_key

            else:
                # Get the origin directory
                origin_file = self.upload_path + uploaded_file

                # Make sure the full target directory exists
                target_file = self.destination_bucket + "/" + self.destination_subfolder + uploaded_file
                target_dir = target_file[:target_file.rindex("/") + 1]
                os.makedirs(target_dir, exist_ok=True)

                # Copy the file over
                shutil.copy(origin_file, target_file)

                # clean up the target_file name before storing it,
                # - removing the local dir
                # - prepend file://
                target_file = target_file.replace(self.local_dir, "file://")

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
            index_file = self.tmp_dir + "/" + self.dataset.entry_id + "_" + str(year) + ".csv"
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
            if self.mode == UploadType.LOCAL:
                target_file = self.destination_bucket + "/" + self.destination_subfolder + \
                              index_file[index_file.rindex("/") + 1:]
                shutil.copyfile(index_file, target_file)
                os.remove(index_file)
            else:
                key = self.destination_subfolder + index_file[index_file.rindex("/") + 1:]
                data = open(index_file, mode='rb')
                self.s3client.put_object(
                    Bucket=self.destination_bucket,
                    Key=key,
                    Body=data
                )
                print(f"Uploading {index_file} to bucket: {self.destination_bucket} at key: {key}.")
                data.close()
                os.remove(index_file)

    def __update_catalog(self):
        """
        Update the catalog database
        """
        # Now update the CatalogEntry that will be made
        # Start date & end date come from the min & max of the manifest
        start_date = self.manifest_df['time'].min()
        end_date = self.manifest_df['time'].max()
        self.dataset.start_date = start_date
        self.dataset.end_date = end_date

        # Get the file formats
        def get_extension(filename: str):
            return filename.split(".")[-1]

        extensions = self.manifest_df['s3key'].apply(get_extension).unique()

        # TODO: Do an earlier check on the extensions.  Why copy the files over if the extension type is not supported?
        self.dataset.file_format = list(extensions)

        # Save the DataSet and RegisteredFile lists to their repositories
        self.dataset_repo.save(self.dataset)

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
        # self.__clean_up()
