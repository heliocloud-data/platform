# File Registry Tool

This tool is used when wanting to get the file registry files from a specific ID entry in a catalog within a bucket. This tool is not for productive searching through the global catalog (bucket registry) or the bucket-specific catalogs (data registry).

## Use Case

There is a mission that is on S3 following the HelioCloud 'CloudMe' Specification and we want to obtain specific files of this mission.

To begin, we would install this tool if it is not already installed. We then would import the tool into a script or shell. Once imported we would likely want to search the global catalog to find the specific bucket/catalog that contains references to the file registry files.

```python
# Create CatalogRegistry object which will by default pull from the Heliocloud global catalog
# or if an environment variable has been set for another global catalog, it will pull from there
cr = CatalogRegistry()

# Print out the entire global catalog
print(cr.get_catalog())

# Print out name + region of all global catalog entries
# If we know roughly what the name of the overarching bucket would be,
# this will help us find the exact name we need for the mission we want.
# Otherwise, other methods must be used to search for the bucket of interests.
print(cr.get_entries())
```

We now have hopefully found which bucket contains the data registry that is of interest. So, we will want move on to searching the bucket-specific catalog (data registry) for the ID that represents the mission we want to get some data for. 

```python
# With the bucket name we have obtained (possibly by using cr.get_endpoint(name, region_prefix=''))
bucket_name = 'a-bucket-name'
# may need to pass access_key or other boto S3 client specific params to get the data
# cache_folder is only used if cache is True and defaults to `bucket_name + '_cache'`
fr = FileRegistry(bucket_name, cache_folder=None, cache=True)  

# Print out the entire local catalog (data registry)
print(fr.get_catalog())

# To find the specific ID we can also get the ID + Title by
print(fr.get_entries())

# Now with the ID we can request the file registry files
# This if successful, will get us a Pandas dataframe of the file registry
# and if we previously had set cache to True in initialization, it will
# also save the downloaded file registry
fr_id = 'an_id_from_data_registry_catalog'
start_date = '2007-02-01T00:00:00Z'  # A ISO 8601 standard time and a valid time witin the mission/file-registry
end_date = None  # A ISO 8601 standard time or None if want all the file registry data after start_date
file_registry = fr.request_file_registry(fr_id, start_date=start_date, end_date=end_date, overwrite=False)
```

We now have a pandas DataFrame with startdate, key, and filesize for all the files of the mission within our specified start and end dates. From here one can use the key to stream some of the data through EC2, a Lambda, or other processing methods.

This tool does not offer specific methods for downloading the actual data, but using boto s3 client or other methods are possible. To outline a simple example of getting the data if it were a FITS file, look at the code below:

```python
import boto3
from astropy.io import fits

# assuming the key in each file registry entry follows the format of a full s3 uri
for key in file_registry['key']:
    # remove s3://
    key = key[5:]

    # get bucket name and relative key
    bucket_name, key = key.split('/', 1)

    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    status = response.get('ResponseMetadata', {}).get('HTTPStatusCode')
    if 'Body' in response and status == 200:
        file = response['Body'].read()
        hdul = fits.open(file)

        # do something with open fits file
        print(hdul[0].header)
    else:
        print(f'Error geting: {bucket_name} {key}')
```
