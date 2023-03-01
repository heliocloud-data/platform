import boto3
from boto3.session import Session
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
        catalog_url: either the environment variable by default or an explicitly passed in url
        """
        # Set the catalog URL (env variable if not manually provided)
        if catalog_url is None:
            catalog_url = os.getenv('ROOT_CATALOG_REGISTRY_URL')
            if catalog_url is None:
                raise ValueError('No environment variable ROOT_CATALOG_REGISTRY_URL nor was an explicit catalog_url passed in')
        self.catalog_url = catalog_url

        # Load the content from json
        self.catalog = requests.get(self.catalog_url).json()

    def get_catalog(self):
        return self.catalog
        
    def get_registry(self):
        return self.catalog['registry']
    
    def get_entries(self):
        # Get the name and region of each entry in the catalog
        return [(x['name'], x['region']) for x in self.catalog['registry']]
    
    def get_endpoint(self, name, region_prefix='', force_first=False):
        """
        Parameters:
        name: Name of the endpoint
        region_prefix (optional): Prefix for a region
        force_first (optional, defaults to False): If True, returns the first entry regardless of name+region uniqueness

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


class FileRegistry:
    """
    Use to work with a specific bucket (obtained from the global catalog) and
    the associated catalog in the bucket
    """
    
    def __init__(self, bucket_name, cache_folder=None,
                 aws_access_key_id=None, aws_secret_access_key=None):
        """
        Parameters: 
        bucket_name (str): The name of the s3 bucket.
        cache_folder (str): Folder to store the file registry cache, defaults to bucket_name + '_cache'.
        aws_access_key_id (str): AWS access key ID
        aws_secret_access_key (str): AWS secret access key
        """
        # Remove s3 uri info if provided
        if bucket_name.startswith('s3://'):
            bucket_name = bucket_name[5:]
        if bucket_name[-1] == '/':
            bucket_name = bucket_name[:-1]
    
        # Store the values for future use  
        self.bucket_name = bucket_name
        
        # Create a 'session' object with provided credentials 
        session = Session(aws_access_key_id=aws_access_key_id,
                         aws_secret_access_key=aws_secret_access_key)
        self.s3 = session.resource('s3')
        
        # Get the given bucket 
        self.bucket = self.s3.Bucket(self.bucket_name)

        # Get catalog bytes from S3 
        catalog_bytes = BytesIO()
        self.bucket.download_fileobj('catalog.json', catalog_bytes)

        # Set the pointer back at the start  
        catalog_bytes.seek(0)
        
        # Load the content from json
        self.catalog = json.load(catalog_bytes)
        
        # Set and create the folder for caching 
        if cache_folder is None:
            cache_folder = bucket_name + '_cache'
        self.cache_folder = cache_folder
        if not os.path.exists(self.cache_folder):
            os.mkdir(self.cache_folder)

        # Copy the content of the catalog to this folder 
        catalog_bytes.seek(0)
        with open(os.path.join(cache_folder, 'catalog.json'), 'wb') as file:
            file.write(catalog_bytes.read())
            
        # Check status and rasie exception
        if self.catalog['status'] == '1400/temporarily unavailable':
            raise Exception(self.catalog['status'])

    def get_catalog(self):
        return self.catalog
            
    def request_file_registry(self, catalog_id, start_date=None, end_date=None):
        """
        Function to request file registry from the s3 bucket. 

        Parameters: 
        catalog_id (str): The id of the catalog entry in the s3 bucket. 
        start_date (str): Start date for which file registry is needed (default None). ISO 8601 standard
        end_date (str): End date for which file registry is needed (default None). ISO 8601 standard.
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
        eid, loc, catalog_start_date, catalog_end_date, ndxformat = entry['id'], entry['loc'], entry['startdate'], entry['enddate'], entry['indexformat']

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
        
        # Get Bucket info dependening on the type of address passed (Local, S3 or diffrent bucket)
        if loc.startswith(f's3://{self.bucket_name}/'):
            loc = loc[len(self.bucket_name)+6:]
            bucket = self.bucket
        elif loc.startswith(f'{self.bucket_name}/'):
            loc = loc[len(self.bucket_name)+1:]
            bucket = self.bucket
        elif loc.startswith(f's3://'):
            bucketname = loc[5:].split('/', 1)[0]
            bucket = self.s3.Bucket(bucketname)
            loc = loc[len(self.bucket_name)+6:]
        else:
            raise Exception(f'Invalid Catalog Loc: {loc}')

        # Define empty array for storing data frames 
        frs = []

        # Loop through all the years 
        for year in range(year_start_date, year_end_date):
            filename = f'{eid}_{year}.{ndxformat}'
            filepath = os.path.join(path, filename)

            # If file does not exist download it from s3
            # And save it to the given path 
            if not os.path.exists(filepath):
                fr_bytes = BytesIO()
                bucket.download_fileobj(os.path.join(loc, filename), fr_bytes)
                fr_bytes.seek(0)
                with open(filepath, 'wb') as file:
                    file.write(fr_bytes.read())

                fr_bytes.seek(0)

                # Depending on the format of index read the csv or parq file
                if ndxformat == 'csv':
                    frs.append(pd.read_csv(fr_bytes))
                elif ndxformat == 'parquet':
                    frs.append(pd.read_parquet(fr_bytes))
                elif ndxformat == 'csv-zip':
                    frs.append(pd.read_csv(fr_bytes, compression='zip'))
                else:
                    raise NotImplementedError(f'Invalid ndxformat: {ndxformat}')

            # If file exists, read from given path 
            else:
                if ndxformat == 'csv':
                    frs.append(pd.read_csv(filepath))
                elif ndxformat == 'parquet':
                    frs.append(pd.read_parquet(filepath))
                elif ndxformat == 'csv-zip':
                    frs.append(pd.read_csv(filepath, compression='zip'))
                else:
                    raise NotImplementedError(f'Invalid ndxformat: {ndxformat}')

        frs = pd.concat(frs)
                    
        # Filter file registry dataframe to exact requested dates
        frs['starttime'] = pd.to_datetime(frs['starttime'], format='%Y-%m-%dT%H:%M:%SZ')
        frs = frs[(start_date <= frs['starttime']) & (frs['starttime'] < end_date)]
                    
        return frs
