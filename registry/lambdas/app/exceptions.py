class RegistryException(Exception):
    def __init__(self, message="There was an error in the Registry module") -> None:
        """
        Exception raised for events in the Registry Module

        Parameters:
            message - the message to include in the exception
        """
        self.message = message
        super().__init__(self.message)


class IngesterException(Exception):
    """
    Exception raised for errors encountered in the Ingest process.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="There was an error in the ingest process"):
        self.message = message
        super().__init__(self.message)
