# Generates a Bucket Catalog per the specification at:
# https://git.smce.nasa.gov/heliocloud/heliocloud-services/-/blob/develop/install/base_data/documentation/CloudMe-data-access-spec-0.1.1.md#5-info

from dataclasses import dataclass
from datetime import datetime

# Valid file formats for data set files stored in public s3 buckets
VALID_FILE_FORMATS = [
    'fits',
    'csv',
    'cdf',
    'netcdf3',
    'hdf5',
    'datamap',
    'other'
]


@dataclass
class Ownership:
    """
    Stores ownership attribution information about a particular data set entry
    """
    description: str = None
    resource_id: str = None
    creation_date: datetime = None
    citation: str = None
    contact: str = None
    about_url: str = None


@dataclass
class DataSet:
    """Required fields"""
    entry_id: str
    loc: str
    title: str

    # Index format type for the files registered as part of this data set
    index_format: str = "csv"

    # List of file formats in this data set
    file_format: list = None

    # The starting (earliest) date of data registered in this data set
    # Restricted IS0 8601 date/time of the first record of data
    start_date: datetime = None

    # The ending (latest) date of data registered in this data set
    # Restricted ISO 8601 date/time of the last record of data
    end_date: datetime = None

    # When this data set was last modified
    modification_date: datetime = datetime.now()

    # Ownership information, if available
    ownership: Ownership = None

    def __setattr__(self, key, value):

        # Check loc
        if key == "loc" and not (str(value).startswith("s3://") or str(value).startswith("file://")):
            raise ValueError(f"DataSet loc must start with s3:// or file://. Loc was {value}.")

        # Validate the file format on setting it
        if key == "file_format":
            if value is not None:
                for file_format in value:
                    if file_format not in VALID_FILE_FORMATS:
                        raise ValueError(f"Format {file_format} is not a valid file format. "
                                         f"Must be one of {VALID_FILE_FORMATS}")

        # Validate date values
        if key == "start_date" and (self.end_date is not None):
            if value > self.end_date:
                raise ValueError(f"Attribute start_date {value} can not be after end_date {self.end_date}.")

        if key == "end_date" and (self.start_date is not None):
            if value < self.start_date:
                raise ValueError(f"Attribute end_date {value} can not be after start_date {self.start_date}")

        self.__dict__[key] = value


def ownership_from_dict(data: dict) -> Ownership:
    """
    Returns an Ownership instance with fields populated from data.
    """
    ownership = Ownership()
    for key in ownership.__dict__.keys():
        if key in data:
            ownership.__dict__[key] = data[key]
    return ownership


def dataset_from_dict(data: dict) -> DataSet:
    """
    Returns a DataSet instance with fields populated from dict.
    Will search for a nested "Ownership" instance in the process
    """

    # Minimum fields required
    dataset = DataSet(entry_id=data['id'], loc=data['loc'], title=data['title'])

    # Get Optional fields
    if 'index_format' in data:
        dataset.index_format = data['index_format']
    if 'file_format' in data:
        dataset.file_format = data['file_format']
    if 'start_date' in data:
        dataset.start_date = data['start_date']
    if 'end_date' in data:
        dataset.end_date = data['end_date']
    if 'modification_date' in data:
        dataset.modification_date = data['modification_date']

    # Get optional ownership info
    if 'ownership' in data:
        dataset.ownership = ownership_from_dict(data['ownership'])

    return dataset
