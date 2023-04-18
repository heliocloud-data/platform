from base_data.model.registered_file import RegisteredFile
from base_data.model.dataset import DataSet


class DataSetRepository(object):
    """
    For persisting data sets in the
    """

    def __init__(self, db_handle):
        self.db_handle = db_handle

    def save(self, dataset: DataSet):
        print(f"Now saving dataset: {dataset}")


class RegisteredFileRepository(object):
    """
    Repository implementation for saving files
    """

    def __init__(self, db_handle):
        self.db_handle = db_handle

    def save(self, registered_files: list[RegisteredFile]) -> None:
        for file in registered_files:
            print(f"Now saving {file}")
