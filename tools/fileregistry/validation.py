import jsonschema
import os
import json
import requests
import boto3
import dateutil
import logging
from datetime import datetime
from math import ceil
from typing import List, Dict, Tuple, Optional, Any


class FailedS3Get(Exception):
    pass


class UnavailableData(Exception):
    pass


class Validator:
    def __init__(self, catalog_url: Optional[str] = None, **client_kwargs) -> None:
        self.combined_catalog = []
        self.s3_client = boto3.client('s3', **client_kwargs)
        self._fetch_and_combine_catalogs(catalog_url)

    def _fetch_and_combine_catalogs(self, catalog_url: Optional[str] = None) -> None:
        """
        Fetches the global catalog and combines it with local catalogs.

        Parameters:
            catalog_url: URL of the global catalog. If not provided, it is read from the environment variable
                         ROOT_CATALOG_REGISTRY_URL.
        """
        # Load the global catalog
        if catalog_url is None:
            catalog_url = os.getenv('ROOT_CATALOG_REGISTRY_URL')
            if catalog_url is None:
                # catalog_url = 'https://git.mysmce.com/heliocloud/heliocloud-data-uploads/-/blob/main/catalog.json'
                raise ValueError('No environment variable ROOT_CATALOG_REGISTRY_URL nor was an explicit catalog_url passed in.')

        response = requests.get(catalog_url)
        if response.status_code != 200:
            raise requests.ConnectionError(f'Get Request for Global Catalog Failed. Catalog url: {catalog_url}')

        self.global_catalog = response.json()
        # Key Error if missing registry (invalid catalog)
        entries = self.global_catalog['registry']

        failed_entries = []
        for entry in entries:
            # Key Error if missing endpoint (invalid catalog)
            bucket_name = entry['endpoint']
            if bucket_name.startswith('s3://'):
                bucket_name = bucket_name[5:]
            bucket_name = bucket_name.rstrip('/')

            try:
                response = self.s3_client.get_object(Bucket=bucket_name, Key='catalog.json')
                status = response.get('ResponseMetadata', {}).get('HTTPStatusCode')
                if 'Body' not in response and status != 200:
                    raise FailedS3Get(f'Failed to Get Catalog from Bucket. Status: {status}. Response: {response}')
                
                catalog_bytes = response['Body'].read()
                local_catalog = json.loads(catalog_bytes)
                
                if local_catalog['status'] == '1400/temporarily unavailable':
                    raise UnavailableData(self.catalog['status'])

                self.combined_catalog.append(local_catalog)

            except Exception as e:
                # Key Error if missing name or region (invalid catalog)
                logging.debug(f"Failed to fetch local catalog for entry {entry['name']} ({entry['region']}): {e}\n")
                failed_entries.append((entry['name'], entry['region']))

        if len(failed_entries) > 0:
            msg = f"Failed Local Catalog Fetches ({len(failed_entries)}/{len(entries)}): \n[\n"
            for entry in failed_entries:
                msg += f"    {entry[0]} ({entry[1]})\n"
            msg += ']'
            logging.error(msg)

    def validate_uniqueness(self) -> None:
        """
        Validates the uniqueness of name and region combinations in the combined catalog.
        """
        unique_identifiers = set()
        dups = 0
        for catalog in self.combined_catalog:
            for entry in catalog['catalog']:
                identifier = f"{entry['name']} ({entry['region']})"
                if identifier in unique_identifiers:
                    logging.debug(f'{identifier} is not a unique entry.')
                    dups += 1
                else:
                    unique_identifiers.add(identifier)
        if dups == 0:
            logging.info('All catalog name + region uniqueness passed.')
        else:
            logging.warning(f'All catalog name + region uniqueness failed. Duplicates: {dups}')
        
                
    def validate_local_catalog_schema(self, local_catalog: Dict[str, Any]) -> None:
        """
        Validates the schema of a local catalog.

        Parameters:
            local_catalog: The local catalog to be validated.
        """
        schema = {
            'type': 'object',
            'properties': {
                'Cloudy': {'type': 'string'},
                'endpoint': {'type': 'string', 'format': 'uri'},
                'name': {'type': 'string'},
                'contact': {'type': 'string'},
                'description': {'type': 'string'},
                'citation': {'type': 'string'},
                'catalog': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string', 'pattern': '^[a-zA-Z0-9-_]+$'},
                            'loc': {'type': 'string'},
                            'title': {'type': 'string'},
                            'startDate': {'type': 'string', 'format': 'date-time'},
                            'stopDate': {'type': 'string', 'format': 'date-time'},
                            'modificationDate': {'type': 'string', 'format': 'date-time'},
                            'indexformat': {'type': 'string', 'enum': ['csv', 'csv-zip', 'parquet']},
                            'fileformat': {'type': 'string'},
                            'description': {'type': 'string'},
                            'resourceURL': {'type': 'string'},
                            'creationDate': {'type': 'string', 'format': 'date-time'},
                            'citation': {'type': 'string'},
                            'contact': {'type': 'string'},
                            'contactID': {'type': 'string'},
                            'aboutURL': {'type': 'string'},
                        },
                        'required': ['id', 'loc', 'title', 'startDate', 'stopDate', 'modificationDate', 'indexformat', 'fileformat'],
                        'additionalProperties': False,
                    },
                },
                'status': {
                    'type': 'object',
                    'properties': {
                        'code': {'type': 'integer'},
                        'message': {'type': 'string'},
                    },
                    'required': ['code', 'message'],
                    'additionalProperties': False,
                },
            },
            'required': ['Cloudy', 'endpoint', 'name', 'catalog', 'status'],
            'additionalProperties': False,
        }

        try:
            jsonschema.validate(instance=local_catalog, schema=schema)
            logging.info('Local catalog schema validation passed.')
        except jsonschema.exceptions.ValidationError as e:
            logging.error(f'Local catalog schema validation failed: {e.message}')

    def validate_all_local_catalog_schemas(self) -> None:
        """
        Validates the schema of all local catalogs in the combined catalog.
        """
        for index, local_catalog in enumerate(self.combined_catalog):
            logging.info(f"Validating local catalog {index} {local_catalog['name']}:")
            self.validate_local_catalog_schema(local_catalog)
            logging.info()
            
    def validate_global_catalog_schema(self) -> None:
        """
        Validates the schema of the global catalog.
        """
        schema = {
            'type': 'object',
            'properties': {
                'CloudMe': {'type': 'string'},
                'modificationDate': {'type': 'string', 'format': 'date-time'},
                'registry': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'endpoint': {'type': 'string', 'format': 'uri'},
                            'name': {'type': 'string'},
                            'region': {'type': 'string'},
                        },
                        'required': ['endpoint', 'name', 'region'],
                        'additionalProperties': False,
                    },
                },
            },
            'required': ['CloudMe', 'modificationDate', 'registry'],
            'additionalProperties': False,
        }

        try:
            jsonschema.validate(instance=self.global_catalog, schema=schema)
            logging.info('Global catalog schema validation passed.')
        except jsonschema.exceptions.ValidationError as e:
            logging.error(f'Global catalog schema validation failed: {e.message}')

    def validate_local_catalog_file_registries(self, local_catalog: Dict[str, Any]) -> None:
        """
        Validates local file registries in the provided local catalog.

        Parameters:
            local_catalog: The local catalog containing file registries to be validated.
        """
        failed_reg_files = 0
        for entry in local_catalog['catalog']:
            try:
                eid, loc, catalog_start_date, catalog_stop_date = entry['id'], entry['loc'], entry['startDate'], entry['stopDate']
                ndxformat = 'csv'

                year_start_date = dateutil.parser.parse(catalog_start_date[:-1]).year

                def ceil_year(date):
                    return ceil(date.year + (date - datetime(date.year, 1, 1)).total_seconds() * 3.17098e-8)

                year_stop_date = ceil_year(dateutil.parser.parse(catalog_stop_date[:-1]))

                bucket_name = loc[5:].split('/', 1)[0]
                loc = loc[len(bucket_name)+6:]

                for year in range(year_start_date, year_stop_date):
                    filename = f'{eid}_{year}.{ndxformat}'

                    response = self.s3_client.get_object(Bucket=bucket_name, Key=loc + filename)
                    status = response.get('ResponseMetadata', {}).get('HTTPStatusCode')
                    if 'Body' not in response or status != 200:
                        raise FailedS3Get(f'Failed to get a file registry object. Status: {status}. Response: {response}')
            except Exception as e:
                failed_reg_files += 1
                logging.debug(f"Failed to fetch local file registry files for entry {entry['name']} ({entry['region']}): {e}\n")
        if failed_reg_files == 0:
            logging.info('Loading Local Catalog File Registries Passed.')
        else:
            logging.error(f"Loading Local Catalog File Registries Failed. Failures: {failed_reg_files}")

    def validate_all_local_catalog_file_registries(self) -> None:
        """
        Validates the file registries for all local catalogs in the combined catalog.
        """
        for index, local_catalog in enumerate(self.combined_catalog):
            logging.info(f"Validating local catalog file registries {index} {local_catalog['name']}:")
            self.validate_local_catalog_file_registries(local_catalog)
            logging.info()
                
    def validate(self) -> None:
        """
        Performs a complete validation of the catalogs.
        Validates the global catalog schema, local catalog schemas, uniqueness of entries, and local catalog file registries.
        """
        self.validate_global_catalog_schema()
        self.validate_all_local_catalog_schemas()
        self.validate_uniqueness()
        self.validate_all_local_catalog_file_registries()
