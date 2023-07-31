class IngesterException(Exception):
    """
    Exception raised for errors encountered in the Ingest process.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="There was an error in the ingest process"):
        self.message = message
        super().__init__(self.message)
