import os

import boto3

from .aws_utils.document_db import get_documentdb_client
from .repositories import DataSetRepository
from .catalog.cataloger import Cataloger


def handler(event, context) -> None:
    """
    Lambda handler function for invoking the Catalog generator

    Parameters:
        event:  not used
        context: not used
    """
    # Steps:
    # 1 - Create a DataSetRepository instance pointing to the DocumentDB running in this HelioCloud stack
    # 2 - Instantiate a Cataloger instance
    # 3 - Execute the instance

    # Boto3 session for AWS
    session = boto3.session.Session()

    # DataSetRepository creation
    catalog_db_secret = os.environ['CATALOG_DB_SECRET']
    db_client = get_documentdb_client(session=session, secret_name=catalog_db_secret,
                                      tlsCAFile=os.path.dirname(__file__) + "/resources/global-bundle.pem")
    ds_repo = DataSetRepository(db_client=db_client)

    # Create and execute a Cataloger
    cataloger = Cataloger(dataset_repository=ds_repo, session=session)
    cataloger.execute()
