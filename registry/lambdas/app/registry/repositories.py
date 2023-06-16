from ..model.dataset import DataSet


class DataSetRepository(object):
    """
    For persisting dataset records in the catalog database.
    """

    def __init__(self, db_handle=None):
        """
        TODO: Implement to support AWS DocumentDB
        """
        self.__db_handle = db_handle

    def save(self, dataset: DataSet) -> None:
        print(f"Now saving dataset: {dataset}")
