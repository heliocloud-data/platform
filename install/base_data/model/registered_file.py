from dataclasses import dataclass
from datetime import datetime


@dataclass
class RegisteredFile:
    """
    Data object describing a file that is registered as belonging to a data set.

    Example entries:
        '2010-05-08T12:05:30.000Z', 's3://edu-apl-helio-public/euvml/stereo/a/195/20100508_120530_n4euA.fts', '246000'
        '2010-05-08T12:06:15.000Z', 's3://edu-apl-helio-public/euvml/stereo/a/195/20100508_120615_n4euA.fts', '246000'
        '2010-05-08T12:10:30.000Z', 's3://edu-apl-helio-public/euvml/stereo/a/195/20100508_121030_n4euA.fts', '246000'
    """

    """Required fields"""
    # Id of the data set to associate the file with
    dataset_id: str

    # start_date of data in file
    start_date: datetime

    # S3 location of file
    key: str

    # in bytes
    file_size: int

    """Optional fields"""
    # ending datetime of data in file (if known)
    end_date: datetime = None

    # Checksum information
    checksum: int = None
    checksum_algorithm: str = None  # Checksum algorith
