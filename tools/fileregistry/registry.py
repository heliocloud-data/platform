import boto3
from io import BytesIO
import pandas as pd
import os
from datetime import datetime
from math import ceil
import json
import requests


class CatalogRegistry:
    """Use to work with the the global catalog (catalog of catalogs)"""
    
    def __init__(self, catalog_url=None):
        """
        Parameters:
        catalog_url: either the environment variable `ROOT_CATALOG_REGISTRY_URL` if it exists
                     or the smce heliocloud global catalog by default, otherwise the explicitly passed in url
        """
        # Set the catalog URL (env variable or default if not manually provided)
        if catalog_url is None:
            catalog_url = os.getenv('ROOT_CATALOG_REGISTRY_URL')
            if catalog_url is None:
                # TODO: Edit to real catalog
                catalog_url = 'https://git.mysmce.com/heliocloud/heliocloud-data-uploads/-/blob/main/catalog.json'
                # TODO: Remove ValueError
                raise ValueError('No environment variable ROOT_CATALOG_REGISTRY_URL nor was an explicit catalog_url passed in')
        self.catalog_url = catalog_url

        # Load the content from json
        response = requests.get(self.catalog_url)
        if response.status_code == 200:
            self.catalog = response.json()
        else:
            raise requests.ConnectionError(f'Get Request for Global Catalog Failed. Catalog url: {self.catalog_url}')
        
        # Check global catalog format assumptions
        if 'registry' not in self.catalog:
            raise KeyError('Invalid catalog. Missing registry key.')
        for reg_entry in self.catalog['registry']:
            if 'endpoint' not in reg_entry or 'name' not in reg_entry or 'region' not in reg_entry:
                raise KeyError('Invalid registry entry in catalog. Missing endopount or name or region key.')
        

    def get_catalog(self):
        """
        Get the global catalog with all metadata and registry entries

        Returns:
        The global catalog dict
        """
        return self.catalog
        
    def get_registry(self):
        """
        Get the registry values in the global catalog

        Returns:
        A list of catalog dicts, which are each entry in the registry
        """
        return self.catalog['registry']
    
    def get_entries(self):
        """
        Get the entry names and region of each entry in the registry
        
        Returns:
        A list of tuples with the name and region from the global catalog registry
        """
        # Get the name and region of each entry in the catalog
        return [(x['name'], x['region']) for x in self.catalog['registry']]
    
    def get_endpoint(self, name, region_prefix='', force_first=False):
        """
        Get the s3 endpoint given the name and region
        
        Parameters:
        name: Name of the endpoint
        region_prefix (optional, str,): Prefix for a region
        force_first (optional, defaults to False, bool): If True, returns the first entry regardless of name+region uniqueness

        Returns:
        The URI of the endpoint
        """
        # Find registries that match the specified name and region prefix
        registries = [x for x in self.catalog['registry'] if x['name'] == name and x['region'].startswith(region_prefix)]
        # Check to make sure all entries have unique names + prefixed region
        if not force_first and len(registries) > 1:
            if len(set(x['region'] for x in registries)) == 1:
                raise ValueError('Entries do not all have unique names. You may enable force_first to choose first option')
            else:
                raise ValueError('Entries do not all have unique names but have different regions, please further specify region_prefix')
        elif len(registries) == 0:
            raise ValueError('No endpoint found with given name and region_prefix')
        return registries[0]['endpoint']


class FailedS3Get(Exception):
    """
    A custom exception for any errors relating to s3 that are not already thrown by boto.
    """
    pass


class UnavailableData(Exception):
    """
    A custom exception for when the catalog indicates the dataset is unavailable.
    """
    pass

    
class FileRegistry:
    """
    Use to work with a specific bucket (obtained from the global catalog) and
    the associated catalog in the bucket
    """
    
    def __init__(self, bucket_name, cache_folder=None, cache=True, **client_kwargs):
        """
        Parameters: 
        bucket_name (str): The name of the s3 bucket.
        cache_folder (str): Folder to store the file registry cache, defaults to bucket_name + '_cache'.
        cache (optional, defaults to True, bool): Determines if any files should be cached so that S3 pulling
                                                  is not unnecessarily done. If a cache_folder is provided,
                                                  this is forced to true.
        client_kwargs: parameters for boto3.client: region_name, aws_acces_key_id, aws_secret_access_key, etc.
        """
        # Remove s3 uri info if provided
        if bucket_name.startswith('s3://'):
            bucket_name = bucket_name[5:]
        if bucket_name[-1] == '/':
            bucket_name = bucket_name[:-1]
    
        # Store the bucket name for future use  
        self.bucket_name = bucket_name
        
        # Create a client object with provided kwargs
        self.s3_client = boto3.client('s3', **client_kwargs)

        # Get catalog bytes from S3 
        # May through some errors, NoSuchBucket, ClientError (file may not exists or access denied)
        # If have ListBucket perms, no such key error will be raised instead of client error
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key='catalog.json')
        status = response.get('ResponseMetadata', {}).get('HTTPStatusCode')
        if 'Body' in response and status == 200:
            catalog_bytes = response['Body'].read()
        else:
            raise FailedS3Get('Failed to Get Catalog from Bucket.')
        
        # Load the content from json
        self.catalog = json.loads(catalog_bytes)
        
        # Check catalog format assumptions
        if any([key not in self.catalog for key in ['status', 'catalog']]):
            raise KeyError('Invalid catalog. Missing either status or catalog key.')
        for entry in self.catalog['catalog']:
            if any([key not in entry for key in ['id', 'loc', 'title', 'startdate', 'enddate']]):
                raise KeyError('Invalid catalog entry. Missing a needed key.')
            loc = entry['loc']
            #if (not loc.startswith('s3://') and not loc.startswith(f'{bucket_name}/')) or loc[-1] != '/':
            if not loc.startswith('s3://') or loc[-1] != '/':
                raise ValueError('Invalid loc in catalog entry.')
        
        # Set and create the folder for caching 
        if cache_folder is None and cache:
            cache_folder = self.bucket_name + '_cache'
        self.cache_folder = cache_folder
        if self.cache_folder is not None and not os.path.exists(self.cache_folder):
            os.mkdir(self.cache_folder)

        # Copy the content of the catalog to this folder 
        with open(os.path.join(cache_folder, 'catalog.json'), 'wb') as file:
            file.write(catalog_bytes)
            
        # Check status and rasie exception
        if self.catalog['status'] == '1400/temporarily unavailable':
            raise UnavailableData(self.catalog['status'])

    def get_catalog(self):
        """
        Gets the raw catalog downloaded from the bucket.

        Returns:
        The catalog dict
        """
        return self.catalog
    
    def get_entries(self):
        """
        Get the entry id and title of each entry in the catalog
        
        Returns:
        A list of tuples with the id and title from the global catalog registry
        """
        # Get the name and region of each entry in the catalog
        return [(x['id'], x['title']) for x in self.catalog['catalog']]
            
    def request_file_registry(self, catalog_id, start_date=None, end_date=None, overwrite=False):
        """
        Request the files in the file registry within the provided times from the s3 bucket. 

        Parameters: 
        catalog_id (str): The id of the catalog entry in the s3 bucket. 
        start_date (str): Start date for which file registry is needed (default None). ISO 8601 standard
        end_date (str): End date for which file registry is needed (default None). ISO 8601 standard.
        overwrite (bool): Overwrite files already cached if within request,
                          cache in initilization must have been true.
                             
        Returns:
        A pandas Dataframe containing the requested file registry data
        """
        # Make dates conform with ISO 8601 standard
        if start_date[-1] != 'Z':
            start_date += 'Z'
        if end_date[-1] != 'Z':
            end_date += 'Z'
            
        # Convert dates to datetime object
        start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%SZ')
        end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%SZ')

        # Get the entry with given catalog id from the list of catalogs 
        entry = [catalog_entry for catalog_entry in self.catalog['catalog'] if catalog_entry['id'] == catalog_id]

        # Raises error if no matching entry is found 
        if len(entry) != 1:
            raise ValueError(f'No unique catalog entry found with id: {catalog_id}')
        else:
            entry = entry[0]

        # Get some necessary variables 
        eid, loc, catalog_start_date, catalog_end_date = entry['id'], entry['loc'], entry['startdate'], entry['enddate']
        ndxformat = 'csv'  # entry['ndxformat']

        # If caching
        if self.cache_folder is None:
            path = None
        else:
            # Create the path for storing cached files and folder if does not exist
            path = os.path.join(self.cache_folder, catalog_id)
            if not os.path.exists(path):
                os.mkdir(path)

        # Compute minimum and maximum year from start and end date respectively 
        catalog_year_start_date = datetime.strptime(catalog_start_date, '%Y-%m-%dT%H:%M:%SZ').year
        year_start_date = catalog_year_start_date if start_date is None else max(catalog_year_start_date, start_date.year)

        def ceil_year(date):
            return ceil(date.year + (date - datetime(date.year, 1, 1)).total_seconds() * 3.17098e-8)

        catalog_year_end_date = ceil_year(datetime.strptime(catalog_end_date, '%Y-%m-%dT%H:%M:%SZ'))
        year_end_date = catalog_year_end_date if end_date is None else min(catalog_year_end_date, ceil_year(end_date))

        # Check if start date is less or equal than end date
        if year_end_date < year_start_date:
            raise ValueError('start_date must be equal or less than end_date')
        
        # Local or different: Could be same bucket or different bucket
        # not enforcing being same bucket
        bucket_name = loc[5:].split('/', 1)[0]
        loc = loc[len(bucket_name)+6:]

        # Define empty array for storing data frames 
        frs = []

        # Loop through all the years 
        for year in range(year_start_date, year_end_date):
            filename = f'{eid}_{year}.{ndxformat}'

            if path is None:
                filepath = None
            else:
                filepath = os.path.join(path, filename)
            
            # If file does not exist download it from s3
            # And save it to the given path 
            if overwrite or filepath is None or not os.path.exists(filepath):
                # May through some errors, NoSuchBucket, ClientError (file may not exists or access denied)
                # If have ListBucket perms, no such key error will be raised instead of client error
                response = self.s3_client.get_object(Bucket=bucket_name, Key=loc + filename)
                status = response.get('ResponseMetadata', {}).get('HTTPStatusCode')
                if 'Body' in response and status == 200:
                    fr_bytes_file = BytesIO()
                    fr_bytes_file.write(response['Body'].read())
                    fr_bytes_file.seek(0)
                else:
                    raise FailedS3Get('Failed to get a file registry object')
                
                if filepath is not None:
                    with open(filepath, 'wb') as file:
                        file.write(fr_bytes_file.read())
                    fr_bytes_file.seek(0)

                frs.append(pd.read_csv(fr_bytes_file))
                    
                # Depending on the format of index read the csv or parq file
                #if ndxformat == 'csv':
                #    frs.append(pd.read_csv(fr_bytes_file))
                #elif ndxformat == 'parquet':
                #    frs.append(pd.read_parquet(fr_bytes_file))
                #elif ndxformat == 'csv-zip':
                #    frs.append(pd.read_csv(fr_bytes_file, compression='zip'))
                #else:
                #    raise NotImplementedError(f'Invalid ndxformat: {ndxformat}')

            # If file exists, read from given path
            else:
                frs.append(pd.read_csv(filepath))
                
                #if ndxformat == 'csv':
                #    frs.append(pd.read_csv(filepath))
                #elif ndxformat == 'parquet':
                #    frs.append(pd.read_parquet(filepath))
                #elif ndxformat == 'csv-zip':
                #    frs.append(pd.read_csv(filepath, compression='zip'))
                #else:
                #    raise NotImplementedError(f'Invalid ndxformat: {ndxformat}')

        frs = pd.concat(frs)
                    
        # Filter file registry dataframe to exact requested dates
        frs['starttime'] = pd.to_datetime(frs['starttime'], format='%Y-%m-%dT%H:%M:%SZ')
        frs = frs[(start_date <= frs['starttime']) & (frs['starttime'] < end_date)]
                    
        return frs
